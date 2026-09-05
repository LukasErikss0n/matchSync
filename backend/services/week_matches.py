from datetime import datetime, timedelta, timezone

from models.models import League, Match, Sport, Team
from schemas.schemas import LeagueOut, MatchOut
from services.cache import MISSING, TTLCache
from services.match_out import build_match_out
from sqlmodel import Session, col, select
from utils import ensure_utc

WEEK_AHEAD = timedelta(days=7)
WEEK_LOOKBACK = timedelta(hours=3)

MAX_WEEK_MATCHES = 60

DOMESTIC_ONLY_LEAGUES: dict[str, set[str]] = {
    "SE": {"allsvenskan", "shl", "sdhl", "sbl-herrar", "sbl-damer"},
}


def _hidden_for_region(league_slug: str, region: str | None) -> bool:
    for home_region, slugs in DOMESTIC_ONLY_LEAGUES.items():
        if league_slug in slugs and region != home_region:
            return True
    return False

_cache: TTLCache[list[MatchOut]] = TTLCache(ttl_seconds=300)


def get_week_matches(
    session: Session, region: str | None = None, limit: int = MAX_WEEK_MATCHES
) -> list[MatchOut]:
    region = region.upper() if region else None
    cache_key = region or "global"
    cached = _cache.get(cache_key)
    if cached is not MISSING:
        return cached[:limit]

    now = datetime.now(timezone.utc)
    stmt = (
        select(Match, Team, League, Sport)
        .join(Team, col(Match.team_id) == col(Team.id))
        .join(League, col(Team.league_id) == col(League.id))
        .join(Sport, col(League.sport_id) == col(Sport.id))
        .where(
            Match.external_id.endswith("_home"),
            Match.start_time >= now - WEEK_LOOKBACK,
            Match.start_time <= now + WEEK_AHEAD,
        )
    )
    rows = session.exec(stmt).all()

    league_ids = {lg.id for _, _, lg, _ in rows}
    away_lookup: dict[tuple[int, str], Team] = {}
    if league_ids:
        for team in session.exec(
            select(Team).where(col(Team.league_id).in_(league_ids))
        ).all():
            away_lookup[(team.league_id, team.name)] = team

    ranked: list[tuple[datetime, int, Match, Team, League, Sport]] = []
    for index, (match, home_team, lg, sp) in enumerate(rows):
        if _hidden_for_region(lg.slug, region):
            continue
        start = ensure_utc(match.start_time)
        ranked.append((start, index, match, home_team, lg, sp))

    ranked.sort(key=lambda r: (r[0], r[1]))

    results: list[MatchOut] = []
    for start, _, match, home_team, lg, sp in ranked[:MAX_WEEK_MATCHES]:
        assert match.id is not None and lg.id is not None
        away_team = away_lookup.get((lg.id, match.away_team))
        results.append(
            build_match_out(match, home_team, away_team, LeagueOut(name=lg.name, slug=lg.slug), sp.slug, start=start)
        )

    _cache.set(cache_key, results)
    return results[:limit]
