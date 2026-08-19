"""Ranked list of the coming week's matches for the home page's "This week".

Reuses featured_match's league weights and region boost so one editorial
opinion about league importance lives in a single place. What differs is the
emphasis: featured_match picks a single hero fixture, so kickoff proximity
dominates its score. This list is browsed as a week at a glance, so league
prestige leads and kickoff time only orders matches *within* the same tier —
a Premier League game on Saturday still outranks an Allsvenskan one tonight,
unless the visitor is Swedish and the region boost flips that round.

Rather than fold both into one number (which needs the time term kept small
enough never to jump a league tier — fragile as weights change), ordering is
an explicit sort key: live first, then league score, then kickoff.
"""

import time
from datetime import datetime, timedelta, timezone

from models.models import League, Match, Sport, Team
from schemas.schemas import LeagueOut, MatchOut
from services.crest_url import crest_url
from services.featured_match import (
    DEFAULT_LEAGUE_WEIGHT,
    F1_LOW_PRIORITY_SESSIONS,
    LEAGUE_WEIGHTS,
    LIVE_WINDOW,
    REGION_BOOST,
    REGION_LEAGUES,
)
from sqlmodel import Session, col, select

# A rolling seven days rather than "until Sunday" — a calendar week checked on
# a Friday would show two near-empty days and hide the weekend's fixtures.
WEEK_AHEAD = timedelta(days=7)
# Enough lookback to keep a match that kicked off recently (and may still be
# in progress) in the list instead of dropping it mid-game.
WEEK_LOOKBACK = timedelta(hours=3)

# The frontend collapses to a handful of rows and expands to the full week,
# so the whole ranked list is sent in one response.
MAX_WEEK_MATCHES = 60

# Leagues with effectively no following outside their home country — hidden
# from everyone else's week rather than merely ranked lower, since even at the
# bottom they'd crowd out fixtures the visitor might actually care about.
#
# Deliberately NOT featured_match's REGION_LEAGUES: that map exists to nudge
# ranking and also lists GB → Premier League, which is followed worldwide and
# must never be hidden. Only leagues that are genuinely domestic-interest
# belong here. Region comes from the visitor's timezone (see
# frontend/src/utils/region.ts); an undetected region is treated as "not
# local", so these stay hidden unless Sweden is positively identified.
DOMESTIC_ONLY_LEAGUES: dict[str, set[str]] = {
    "SE": {"allsvenskan", "shl", "sdhl", "sbl-herrar", "sbl-damer"},
}


def _hidden_for_region(league_slug: str, region: str | None) -> bool:
    for home_region, slugs in DOMESTIC_ONLY_LEAGUES.items():
        if league_slug in slugs and region != home_region:
            return True
    return False

_cache: dict[str, tuple[float, list[MatchOut]]] = {}
_CACHE_TTL_SECONDS = 300


def _league_score(league_slug: str, away_team: str, region: str | None) -> float:
    score = LEAGUE_WEIGHTS.get(league_slug, DEFAULT_LEAGUE_WEIGHT)
    # Same rule featured_match applies: an F1 weekend contributes one row per
    # session, and nobody browses the week for Practice 2 — without this the
    # top of the list is a single Grand Prix repeated five times.
    if league_slug == "formula-1" and any(
        p in away_team for p in F1_LOW_PRIORITY_SESSIONS
    ):
        score = DEFAULT_LEAGUE_WEIGHT
    if region and league_slug in REGION_LEAGUES.get(region, ()):
        score += REGION_BOOST
    return score


def get_week_matches(
    session: Session, region: str | None = None, limit: int = MAX_WEEK_MATCHES
) -> list[MatchOut]:
    """The coming week's matches, best leagues first, then by kickoff."""
    region = region.upper() if region else None
    cache_key = region or "global"
    now_ts = time.monotonic()
    cached = _cache.get(cache_key)
    if cached is not None and now_ts - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1][:limit]

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

    # Away teams resolved in one query for every league in play — one lookup
    # per match would be dozens of round trips for a full week.
    league_ids = {lg.id for _, _, lg, _ in rows}
    away_lookup: dict[tuple[int, str], Team] = {}
    if league_ids:
        for team in session.exec(
            select(Team).where(col(Team.league_id).in_(league_ids))
        ).all():
            away_lookup[(team.league_id, team.name)] = team

    ranked: list[tuple[tuple, Match, Team, League, Sport, datetime]] = []
    for index, (match, home_team, lg, sp) in enumerate(rows):
        if _hidden_for_region(lg.slug, region):
            continue

        start = match.start_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        has_score = match.home_score is not None and match.away_score is not None
        is_live = start <= now <= start + LIVE_WINDOW and not has_score

        # `index` only breaks exact ties, so the sort never has to compare
        # Match objects (which aren't orderable).
        key = (
            0 if is_live else 1,
            -_league_score(lg.slug, match.away_team, region),
            start,
            index,
        )
        ranked.append((key, match, home_team, lg, sp, start))

    ranked.sort(key=lambda r: r[0])

    results: list[MatchOut] = []
    for _, match, home_team, lg, sp, start in ranked[:MAX_WEEK_MATCHES]:
        assert match.id is not None and lg.id is not None  # persisted rows
        away_team = away_lookup.get((lg.id, match.away_team))
        results.append(
            MatchOut(
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
                home_color=home_team.color,
                away_color=away_team.color if away_team else None,
                home_icon_cropped=crest_url(home_team),
                away_icon_cropped=crest_url(away_team),
                home_score=match.home_score,
                away_score=match.away_score,
                start_time=start,
                venue=match.venue,
            )
        )

    _cache[cache_key] = (now_ts, results)
    return results[:limit]
