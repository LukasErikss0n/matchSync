"""Picks the single "featured" match for the hero card.

Scores every candidate in a cheap time window and returns the highest.
No status field exists on Match — "live"/"finished" is inferred from
start_time and whether scores have been recorded. Team-popularity and
rivalry aren't implemented (no such data exists yet) but the scoring
function is structured so they can be added as extra terms later.
Region is a light personalization signal: an optional ISO country code
guessed client-side from timezone/locale (never IP — see
frontend/src/utils/region.ts) that nudges a visitor's domestic league.
"""

import time
from datetime import datetime, timedelta, timezone

from models.models import League, Match, Sport, Team
from schemas.schemas import LeagueOut, MatchOut
from sqlmodel import Session, select

# Candidate pre-filter — cheap enough to avoid scoring the whole table.
LOOKBACK = timedelta(hours=3)
LOOKAHEAD = timedelta(days=14)
LIVE_WINDOW = timedelta(hours=2, minutes=30)  # approx match + stoppage time

# Below this score a match isn't worth featuring — caller should fall back
# to a static promo instead. League weight alone always clears this, so the
# only way to get nothing back is an empty candidate window (no match in
# LOOKBACK..LOOKAHEAD at all).
MIN_SCORE = 0

# --- How scores are built (see _score_match) --------------------------------
#
#   score = time_component + LEAGUE_WEIGHTS[league] + (REGION_BOOST if domestic)
#
# time_component is one of:
#   live match:            flat 1000                     (always wins —
#                                                          nothing below gets
#                                                          remotely close)
#   upcoming (start > now): 200 - hours_until*UPCOMING_DECAY
#                                                          (linear decay to 0
#                                                          right at LOOKAHEAD,
#                                                          so the soonest
#                                                          match always beats
#                                                          a later one in the
#                                                          same league)
#   just finished (<3h):    150 - hours_since*40          (decays fast —
#                                                          stale results drop
#                                                          out within 3h)
#
# Both terms share the same 0-200-ish scale, so a gap between two league
# weights converts directly to a gap in kickoff proximity:
#
#   equivalent_hours = weight_gap / UPCOMING_DECAY
#
UPCOMING_DECAY = 200 / (LOOKAHEAD.total_seconds() / 3600)

LEAGUE_WEIGHTS: dict[str, float] = {
    "fifa-world-cup-2026": 200,
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

# Client-guessed region (from timezone/locale, see frontend/src/utils/region.ts —
# there's no IP geolocation here) nudges the domestic league for that country
# above the global weights, without ever excluding other leagues. Chosen so it
# beats the gap between adjacent LEAGUE_WEIGHTS tiers but not a live match.
REGION_BOOST = 60
REGION_LEAGUES: dict[str, set[str]] = {
    "SE": {"allsvenskan", "shl", "sdhl", "sbl-herrar", "sbl-damer"},
    "GB": {"premier-league", "fa-cup", "efl-cup"},
}

# Cached per region so one visitor's boost doesn't leak into another's result.
_cache: dict[str, tuple[float, MatchOut | None]] = {}
_CACHE_TTL_SECONDS = 300


def _score_match(match: Match, league_slug: str, now: datetime, region: str | None) -> float:
    score = 0.0
    has_score = match.home_score is not None and match.away_score is not None
    start = match.start_time
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)

    if start <= now <= start + LIVE_WINDOW and not has_score:
        score += 1000
    elif start > now:
        hours_until = (start - now).total_seconds() / 3600
        score += max(0, 200 - hours_until * UPCOMING_DECAY)
    elif has_score:
        hours_since = (now - start).total_seconds() / 3600
        if hours_since < 3:
            score += 150 - hours_since * 40
        else:
            return -1
    else:
        # Past kickoff, no score yet, outside the live window — stale data, skip.
        return -1

    score += LEAGUE_WEIGHTS.get(league_slug, DEFAULT_LEAGUE_WEIGHT)
    if region and league_slug in REGION_LEAGUES.get(region, ()):
        score += REGION_BOOST

    return score


def get_featured_match(session: Session, region: str | None = None) -> MatchOut | None:
    region = region.upper() if region else None
    cache_key = region or "global"
    now_ts = time.monotonic()
    cached = _cache.get(cache_key)
    if cached is not None and now_ts - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    now = datetime.now(timezone.utc)
    stmt = (
        select(Match, Team, League, Sport)
        .join(Team, Match.team_id == Team.id)
        .join(League, Team.league_id == League.id)
        .join(Sport, League.sport_id == Sport.id)
        .where(
            Match.external_id.endswith("_home"),
            Match.start_time >= now - LOOKBACK,
            Match.start_time <= now + LOOKAHEAD,
        )
    )
    rows = session.exec(stmt).all()

    best: tuple[float, Match, Team, League, Sport] | None = None
    for match, home_team, lg, sp in rows:
        s = _score_match(match, lg.slug, now, region)
        if s <= MIN_SCORE:
            continue
        if best is None or s > best[0]:
            best = (s, match, home_team, lg, sp)

    result: MatchOut | None = None
    if best is not None:
        _, match, home_team, lg, sp = best
        away_team = session.exec(
            select(Team).where(Team.league_id == lg.id, Team.name == match.away_team)
        ).first()

        start = match.start_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        result = MatchOut(
            id=match.id,
            external_id=match.external_id,
            sport=sp.slug,
            league=LeagueOut(name=lg.name, slug=lg.slug),
            home_team=match.home_team,
            away_team=match.away_team,
            home_slug=home_team.slug,
            away_slug=away_team.slug if away_team else None,
            home_icon=home_team.icon,
            away_icon=away_team.icon if away_team else None,
            home_score=match.home_score,
            away_score=match.away_score,
            start_time=start,
        )

    _cache[cache_key] = (now_ts, result)
    return result
