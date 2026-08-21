"""Chronological list of the coming week's matches for the home page's "This
week" panel.

Ordering used to lead with league prestige (and a region boost for the
visitor's home leagues), with kickoff time only breaking ties within the same
tier — league blocks were each internally in order, but concatenated back to
back the whole list read as scrambled (a Monday fixture from one block
sitting right before a Friday fixture from the next). Straight chronological
order is what "this week" actually promises, so that's the only sort key now.
"""

import time
from datetime import datetime, timedelta, timezone

from models.models import League, Match, Sport, Team
from schemas.schemas import LeagueOut, MatchOut
from services.crest_url import crest_url
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


def get_week_matches(
    session: Session, region: str | None = None, limit: int = MAX_WEEK_MATCHES
) -> list[MatchOut]:
    """The coming week's matches, earliest kickoff first."""
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

    ranked: list[tuple[datetime, int, Match, Team, League, Sport]] = []
    for index, (match, home_team, lg, sp) in enumerate(rows):
        if _hidden_for_region(lg.slug, region):
            continue

        start = match.start_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        # `index` only breaks exact kickoff ties, so the sort never has to
        # compare Match objects (which aren't orderable).
        ranked.append((start, index, match, home_team, lg, sp))

    ranked.sort(key=lambda r: (r[0], r[1]))

    results: list[MatchOut] = []
    for start, _, match, home_team, lg, sp in ranked[:MAX_WEEK_MATCHES]:
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
