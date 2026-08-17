"""Derives a club's primary colour and a tightly-cropped crest from its badge.

The hero panel washes each half of the fixture card in the two clubs' colours,
and shows the crest itself in a small tile. Neither is available from any
feed — no colour field exists, and the crest CDNs send no CORS headers, so
the browser can't even sample the images itself — so both run server-side,
once per team, and the results are stored on the team row.

Two source formats matter in practice: SVG (Premier League badges, already
cropped tight to their artwork) and PNG (everything else, which in practice
often ships with a large transparent margin baked into the file itself — e.g.
svenskfotboll.se crests are typically <50% content by width). SVGs are parsed
as text for colour, which is both cheaper and more accurate than rasterising
them, and are never re-cropped. PNGs are opened with Pillow for both.
"""

import base64
import re
from collections import Counter
from colorsys import hsv_to_rgb, rgb_to_hsv
from io import BytesIO

import requests

_HEADERS = {"User-Agent": "Mozilla/5.0"}
_TIMEOUT = (5, 15)

# Colours that carry no identity — nearly every crest is mostly outline and
# background, and picking those would wash every panel the same grey.
_MIN_SATURATION = 0.25
_MIN_VALUE = 0.20
_MAX_VALUE = 0.97

# The wash renders at 16% over a dark navy, so a muddy or near-black source
# colour disappears. Anything below these floors is lifted to them.
_WASH_MIN_SATURATION = 0.45
_WASH_MIN_VALUE = 0.55

# Below this fraction of transparent margin, cropping isn't worth the extra
# stored data URI — the source image is already close to tight.
_MIN_CROP_GAIN = 0.08
# Breathing room added back around the trimmed content, as a fraction of its
# own size, so the crest doesn't sit flush against the tile edge.
_CROP_MARGIN = 0.06
_CROP_MAX_SIZE = (200, 200)
# Cropping out a source's transparent margin (see above) leaves less actual
# pixel data than the original file's dimensions suggested — a badge that's
# only 44px of real artwork inside a 100px canvas renders soft once the hero
# panel displays it at 90-140px. Below this size the crop is upscaled with a
# sharpening pass instead of leaving the browser to stretch it at display
# time, which softens it further with no sharpening at all.
_CROP_MIN_SIZE = 176

_HEX_RE = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
_RGB_FN_RE = re.compile(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)")


def _is_identity_color(r: int, g: int, b: int) -> bool:
    h, s, v = rgb_to_hsv(r / 255, g / 255, b / 255)
    return s >= _MIN_SATURATION and _MIN_VALUE <= v <= _MAX_VALUE


def _normalise_for_wash(r: int, g: int, b: int) -> str:
    """Lift a colour into the range where a 16% wash still reads on dark navy."""
    h, s, v = rgb_to_hsv(r / 255, g / 255, b / 255)
    s = max(s, _WASH_MIN_SATURATION)
    v = max(v, _WASH_MIN_VALUE)
    rr, gg, bb = hsv_to_rgb(h, s, v)
    return "#%02x%02x%02x" % (round(rr * 255), round(gg * 255), round(bb * 255))


def _dominant_color(pixels) -> str | None:
    counts: Counter[tuple[int, int, int]] = Counter()
    for r, g, b, a in pixels:
        if a < 128 or not _is_identity_color(r, g, b):
            continue
        # Quantise to 32-value buckets so near-identical shades group together.
        counts[(r // 32, g // 32, b // 32)] += 1

    if not counts:
        return None
    bucket = counts.most_common(1)[0][0]

    # Average the real pixels in the winning bucket — the bucket centre alone
    # would visibly shift the hue.
    members = [
        (r, g, b)
        for r, g, b, a in pixels
        if a >= 128 and (r // 32, g // 32, b // 32) == bucket
    ]
    n = len(members)
    avg = (
        sum(p[0] for p in members) // n,
        sum(p[1] for p in members) // n,
        sum(p[2] for p in members) // n,
    )
    return _normalise_for_wash(*avg)


def _trim_to_data_uri(img) -> str | None:
    """PNG data URI of `img` cropped to its non-transparent content, or None
    if the source is already tight enough that cropping wouldn't help."""
    w, h = img.size
    bbox = img.split()[-1].getbbox()  # alpha channel bounding box
    if not bbox:
        return None

    left, top, right, bottom = bbox
    content_area = (right - left) * (bottom - top)
    if content_area >= w * h * (1 - _MIN_CROP_GAIN):
        return None

    bw, bh = right - left, bottom - top
    mx, my = round(bw * _CROP_MARGIN), round(bh * _CROP_MARGIN)
    left, top = max(0, left - mx), max(0, top - my)
    right, bottom = min(w, right + mx), min(h, bottom + my)

    cropped = img.crop((left, top, right, bottom))

    if max(cropped.size) < _CROP_MIN_SIZE:
        from PIL import Image, ImageFilter

        scale = _CROP_MIN_SIZE / max(cropped.size)
        cropped = cropped.resize(
            (round(cropped.width * scale), round(cropped.height * scale)),
            Image.LANCZOS,
        )
        # LANCZOS already resamples more crisply than a browser's own
        # img-tag upscaling would, but it still softens edges a little.
        # percent=150 (tried first) way overshot this — it rang a bright
        # halo around every crest outline, which reads worse than the
        # original softness. This is a light touch-up, not a restoration.
        cropped = cropped.filter(ImageFilter.UnsharpMask(radius=1.2, percent=40, threshold=3))

    cropped.thumbnail(_CROP_MAX_SIZE)
    buf = BytesIO()
    cropped.save(buf, format="PNG", optimize=True)
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"


def _analyze_svg(text: str) -> tuple[str | None, None]:
    counts: Counter[tuple[int, int, int]] = Counter()

    for match in _HEX_RE.finditer(text):
        raw = match.group(1)
        if len(raw) == 3:
            raw = "".join(c * 2 for c in raw)
        rgb = (int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))
        if _is_identity_color(*rgb):
            counts[rgb] += 1

    for match in _RGB_FN_RE.finditer(text):
        rgb = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        if _is_identity_color(*rgb):
            counts[rgb] += 1

    if not counts:
        return None, None
    r, g, b = counts.most_common(1)[0][0]
    # SVG badges (Premier League) are already cropped tight to their artwork
    # in practice, and re-rasterising one just to trim it isn't worth it.
    return _normalise_for_wash(r, g, b), None


def _analyze_raster(data: bytes) -> tuple[str | None, str | None]:
    # Imported lazily so the rest of the fetcher still runs if Pillow is missing.
    from PIL import Image

    with Image.open(BytesIO(data)) as img:
        img = img.convert("RGBA")
        cropped_uri = _trim_to_data_uri(img)

        # Crests are small already; thumbnailing caps the work at a few
        # thousand pixels and incidentally blends away anti-aliasing fringes.
        thumb = img.copy()
        thumb.thumbnail((64, 64))
        color = _dominant_color(thumb.getdata())

    return color, cropped_uri


def analyze_crest(url: str) -> tuple[str | None, str | None]:
    """(primary_color, cropped_data_uri) for the crest at `url`.

    primary_color is #rrggbb or None if undetectable. cropped_data_uri is a
    PNG data: URI trimmed to the crest's actual artwork, or None if the
    source doesn't need it (SVG, or already tight).
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException:
        return None, None

    content_type = resp.headers.get("content-type", "")
    try:
        if "svg" in content_type or url.lower().endswith(".svg"):
            return _analyze_svg(resp.text)
        return _analyze_raster(resp.content)
    except Exception:
        # A single unreadable crest must never take the whole fetcher down.
        return None, None
