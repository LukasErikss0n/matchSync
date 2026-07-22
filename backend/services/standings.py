"""Live league standings — thin caching wrapper around services/
standings_local.py (computed from our own Match table; see that module for
why we don't rely on an external standings API)."""

import time as time_module

from services.standings_local import SUPPORTED_LOCAL_LEAGUE_SLUGS, get_local_standings

_CACHE_TTL_SECONDS = 30 * 60
_cache: dict[str, tuple[float, list[dict] | None]] = {}


def standings_supported(league_slug: str) -> bool:
    """Cheap membership check — lets the frontend disable the "view standings"
    affordance up front for leagues we know don't have one, instead of only
    finding out after opening the modal."""
    return league_slug in SUPPORTED_LOCAL_LEAGUE_SLUGS


def get_standings(league_slug: str) -> list[dict] | None:
    """Returns the full table for a league, or None if standings aren't
    supported for it at all (distinct from an empty/unpublished table)."""
    now = time_module.monotonic()
    cached = _cache.get(league_slug)
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    result = get_local_standings(league_slug)
    _cache[league_slug] = (now, result)
    return result
