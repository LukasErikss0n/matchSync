import re
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Europe/Stockholm")


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


SPORT_META: dict[str, tuple[str, str, str]] = {
    "football": ("Football", "football", "football"),
    "hockey": ("Hockey", "hockey", "hockey"),
    "basketball": ("Basketball", "basketball", "basketball"),
    "motorsport": ("Motorsport", "motorsport", "flag"),
}

LEAGUE_DISPLAY: dict[str, str] = {
    "premier_league": "Premier League",
    "uefa_champions_league": "UEFA Champions League",
    "uefa_conference_league": "UEFA Conference League",
    "fa_cup": "FA Cup",
    "efl_cup": "EFL Cup",
    "uefa_europa_league": "UEFA Europa League",
    "allsvenskan": "Allsvenskan",
    "shl": "SHL",
    "sdhl": "SDHL",
    "sblherrar": "SBL Herrar",
    "sbldamer": "SBL Damer",
    "iihf_world_championship": "IIHF World Championship",
    "fifa_world_cup_2026": "FIFA World Cup 2026",
    "f1": "Formula 1",
}

PLAYOFF_FRAGMENTS = ("playoff", "slutspel", "kvalspel", "playout")


def is_playoff_game_type(item: dict) -> bool:
    for key in ("name", "Name", "description", "Description", "seriesName", "typeName"):
        val = item.get(key)
        if isinstance(val, str) and any(frag in val.lower() for frag in PLAYOFF_FRAGMENTS):
            return True
    return False


class ExpectedUpstreamGap(Exception):
    pass
