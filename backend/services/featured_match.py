from datetime import datetime, timedelta, timezone

from models.models import League, Match, Sport, Team
from schemas.schemas import (
    STATUS_FINISHED,
    STATUS_LIVE,
    STATUS_SCHEDULED,
    LeagueOut,
    MatchOut,
)
from services.cache import MISSING, TTLCache
from services.match_out import build_match_out
from sqlmodel import Session, col, select
from utils import ensure_utc

LOOKBACK = timedelta(hours=3)
LOOKAHEAD = timedelta(days=14)
LIVE_WINDOW = timedelta(hours=2, minutes=30)

MIN_SCORE = 0

UPCOMING_DECAY = 200 / (LOOKAHEAD.total_seconds() / 3600)

LEAGUE_WEIGHTS: dict[str, float] = {
    "fifa-world-cup-2026": 200,
    "formula-1": 145,
    "uefa-champions-league": 150,
    "premier-league": 140,
    "iihf-world-championship": 130,
    "uefa-europa-league": 90,
    "allsvenskan": 90,
    "shl": 75,
    "uefa-conference-league": 65,
    "fa-cup": 60,
    "sdhl": 55,
    "efl-cup": 40,
    "sbl-herrar": 40,
    "sbl-damer": 35,
}
DEFAULT_LEAGUE_WEIGHT = 10

F1_LOW_PRIORITY_SESSIONS = ("Practice",)

REGION_BOOST = 60
REGION_LEAGUES: dict[str, set[str]] = {
    "SE": {"allsvenskan", "shl", "sdhl", "sbl-herrar", "sbl-damer"},
    "GB": {"premier-league", "fa-cup", "efl-cup"},
}

MAX_FEATURED = 6

_cache: TTLCache[list[MatchOut]] = TTLCache(ttl_seconds=300)


def _is_live_now(match: Match, start: datetime, now: datetime) -> bool:
    within_live_window = start <= now <= start + LIVE_WINDOW
    if match.status == STATUS_FINISHED:
        return False
    if match.status == STATUS_LIVE:
        return within_live_window
    if match.status == STATUS_SCHEDULED and now < start:
        return False
    return within_live_window


def _score_match(match: Match, league_slug: str, now: datetime, region: str | None) -> float:
    has_score = match.home_score is not None and match.away_score is not None
    start = ensure_utc(match.start_time)

    if _is_live_now(match, start, now):
        score = 1000.0
    elif start > now:
        hours_until = (start - now).total_seconds() / 3600
        score = max(0, 200 - hours_until * UPCOMING_DECAY)
    elif has_score:
        hours_since = (now - start).total_seconds() / 3600
        if hours_since >= 3:
            return -1
        score = 150 - hours_since * 40
    else:
        return -1

    league_weight = LEAGUE_WEIGHTS.get(league_slug, DEFAULT_LEAGUE_WEIGHT)
    if league_slug == "formula-1" and any(p in match.away_team for p in F1_LOW_PRIORITY_SESSIONS):
        league_weight = DEFAULT_LEAGUE_WEIGHT
    score += league_weight
    if region and league_slug in REGION_LEAGUES.get(region, ()):
        score += REGION_BOOST

    return score


def get_featured_matches(
    session: Session, region: str | None = None, limit: int = MAX_FEATURED
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
            Match.start_time >= now - LOOKBACK,
            Match.start_time <= now + LOOKAHEAD,
        )
    )
    rows = session.exec(stmt).all()

    scored: list[tuple[float, Match, Team, League, Sport]] = []
    for match, home_team, lg, sp in rows:
        s = _score_match(match, lg.slug, now, region)
        if s <= MIN_SCORE:
            continue
        scored.append((s, match, home_team, lg, sp))

    scored.sort(key=lambda r: (-r[0], r[1].start_time))

    results: list[MatchOut] = []
    seen_leagues: set[str] = set()
    for _, match, home_team, lg, sp in scored:
        if lg.slug in seen_leagues:
            continue
        seen_leagues.add(lg.slug)
        assert match.id is not None and lg.id is not None

        away_team = session.exec(
            select(Team).where(Team.league_id == lg.id, Team.name == match.away_team)
        ).first()

        results.append(
            build_match_out(match, home_team, away_team, LeagueOut(name=lg.name, slug=lg.slug), sp.slug)
        )
        if len(results) >= MAX_FEATURED:
            break

    _cache.set(cache_key, results)
    return results[:limit]


def get_featured_match(session: Session, region: str | None = None) -> MatchOut | None:
    matches = get_featured_matches(session, region, limit=1)
    return matches[0] if matches else None
