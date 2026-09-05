from services.cache import MISSING, TTLCache
from services.standings_local import SUPPORTED_LOCAL_LEAGUE_SLUGS, get_local_standings

_cache: TTLCache[list[dict] | None] = TTLCache(ttl_seconds=30 * 60)


def standings_supported(league_slug: str) -> bool:
    return league_slug in SUPPORTED_LOCAL_LEAGUE_SLUGS


def get_standings(league_slug: str) -> list[dict] | None:
    cached = _cache.get(league_slug)
    if cached is not MISSING:
        return cached

    result = get_local_standings(league_slug)
    _cache.set(league_slug, result)
    return result
