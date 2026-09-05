from io import BytesIO

import requests

_HEADERS = {"User-Agent": "Mozilla/5.0"}
_TIMEOUT = (5, 15)

_MIN_CROP_GAIN = 0.08
_CROP_MARGIN = 0.06
_CROP_MAX_SIZE = (320, 320)
_CROP_MIN_SIZE = 176

_HIGHRES_SUBSTITUTIONS = (
    ("/img/teamssm/", "/img/teams/"),
)


def _trim_to_png(img) -> bytes | None:
    w, h = img.size
    bbox = img.split()[-1].getbbox()
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
            Image.Resampling.LANCZOS,
        )
        cropped = cropped.filter(ImageFilter.UnsharpMask(radius=1.2, percent=40, threshold=3))

    cropped.thumbnail(_CROP_MAX_SIZE)
    buf = BytesIO()
    cropped.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _crop_raster(data: bytes) -> bytes | None:
    from PIL import Image

    with Image.open(BytesIO(data)) as img:
        img = img.convert("RGBA")
        return _trim_to_png(img)


def _fetch(url: str) -> requests.Response | None:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException:
        return None
    if not resp.headers.get("content-type", "").startswith("image"):
        return None
    return resp


def crop_crest(url: str) -> bytes | None:
    resp = None
    for small, large in _HIGHRES_SUBSTITUTIONS:
        if small in url:
            resp = _fetch(url.replace(small, large))
            break
    if resp is None:
        resp = _fetch(url)
    if resp is None:
        return None

    content_type = resp.headers.get("content-type", "")
    if "svg" in content_type or url.lower().endswith(".svg"):
        return None
    try:
        return _crop_raster(resp.content)
    except Exception:
        return None
