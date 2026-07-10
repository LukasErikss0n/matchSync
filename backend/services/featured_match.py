"""Picks the single "featured" match for the hero card.

Scores every candidate in a cheap time window and returns the highest.
No status field exists on Match — "live"/"finished" is inferred from
start_time and whether scores have been recorded. Team-popularity,
rivalry, and per-user personalization aren't implemented (no such data
exists yet) but the scoring function is structured so they can be added
as extra terms later.
"""

import time
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from models.models import League, Match, Sport, Team
from schemas.schemas import LeagueOut, MatchOut

# Candidate pre-filter — cheap enough to avoid scoring the whole table.
LOOKBACK = timedelta(hours=3)
LOOKAHEAD = timedelta(hours=72)
LIVE_WINDOW = timedelta(hours=2, minutes=30)  # approx match + stoppage time

# Below this score a match isn't worth featuring — caller should fall back
# to a static promo instead.
MIN_SCORE = 0

LEAGUE_WEIGHTS: dict[str, float] = {
    "fifa-world-cup-2026": 200,
    "uefa-champions-league": 150,
    "premier-league": 120,
    "uefa-europa-league": 90,
    "uefa-conference-league": 80,
    "allsvenskan": 90,
    "shl": 80,
    "sdhl": 70,
    "fa-cup": 60,
    "efl-cup": 50,
    "sbl-herrar": 50,
    "sbl-damer": 45,
    "iihf-world-championship": 110,
}
DEFAULT_LEAGUE_WEIGHT = 10

# This is a Swedish product — Swedish leagues get a fixed boost.
# (Would become per-request locale detection if the audience broadens.)
SE_BOOST_LEAGUES = {"allsvenskan", "shl", "sdhl", "sbl-herrar", "sbl-damer"}
SE_BOOST = 80

_cache: dict[str, object] = {"result": None, "computed_at": 0.0}
_CACHE_TTL_SECONDS = 300


def _score_match(match: Match, league_slug: str, now: datetime) -> float:
    score = 0.0
    has_score = match.home_score is not None and match.away_score is not None
    start = match.start_time
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)

    if start <= now <= start + LIVE_WINDOW and not has_score:
        score += 1000
    elif start > now:
        hours_until = (start - now).total_seconds() / 3600
        score += max(0, 200 - hours_until * 4)
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
    if league_slug in SE_BOOST_LEAGUES:
        score += SE_BOOST

    return score


def get_featured_match(session: Session) -> MatchOut | None:
    now_ts = time.monotonic()
    if now_ts - _cache["computed_at"] < _CACHE_TTL_SECONDS:
        return _cache["result"]  # type: ignore[return-value]

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
        s = _score_match(match, lg.slug, now)
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

    _cache["result"] = result
    _cache["computed_at"] = now_ts
    return result
