from datetime import timezone

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, col, select

from database import get_session
from models.models import League, Match, Sport, Team
from schemas.schemas import LeagueOut, MatchOut
from services.featured_match import (
    MAX_FEATURED,
    get_featured_match,
    get_featured_matches,
)
from services.standings import standings_supported
from services.week_matches import MAX_WEEK_MATCHES, get_week_matches

router = APIRouter()

_REGION_QUERY = Query(
    default=None,
    min_length=2,
    max_length=2,
    pattern="^[A-Za-z]{2}$",
    description="ISO 3166-1 alpha-2 country code, guessed client-side, to nudge the visitor's domestic league",
)


@router.get("/matches/featured", response_model=MatchOut | None)
def featured_match(
    region: str | None = _REGION_QUERY,
    session: Session = Depends(get_session),
):
    """The single highest-scoring live/upcoming/recent match, for the hero card."""
    return get_featured_match(session, region)


@router.get("/matches/featured/list", response_model=list[MatchOut])
def featured_matches(
    region: str | None = _REGION_QUERY,
    limit: int = Query(default=3, ge=1, le=MAX_FEATURED),
    session: Session = Depends(get_session),
):
    """Top-ranked matches (at most one per league) for the rotating hero card."""
    return get_featured_matches(session, region, limit)


@router.get("/matches/this-week", response_model=list[MatchOut])
def this_week(
    region: str | None = _REGION_QUERY,
    limit: int = Query(default=MAX_WEEK_MATCHES, ge=1, le=MAX_WEEK_MATCHES),
    session: Session = Depends(get_session),
):
    """The coming week's matches, ranked by league then kickoff."""
    return get_week_matches(session, region, limit)


@router.get("/matches", response_model=list[MatchOut])
def list_matches(
    sport: str | None = None,
    league: str | None = Query(default=None, description="League slug"),
    team: str | None = Query(default=None, description="Team slug"),
    limit: int = Query(default=500, ge=1, le=2000),
    session: Session = Depends(get_session),
):
    # Read only the home-perspective row so each fixture appears once.
    stmt = (
        select(Match, Team, League, Sport)
        .join(Team, col(Match.team_id) == col(Team.id))
        .join(League, col(Team.league_id) == col(League.id))
        .join(Sport, col(League.sport_id) == col(Sport.id))
        .where(Match.external_id.endswith("_home"))
    )
    if sport:
        stmt = stmt.where(Sport.slug == sport)
    if league:
        stmt = stmt.where(League.slug == league)

    rows = session.exec(stmt.order_by(col(Match.start_time))).all()
    if not rows:
        return []

    # Away crest/slug live on a different Team row — build a per-league lookup.
    league_ids = {lg.id for _, _, lg, _ in rows}
    team_rows = session.exec(
        select(Team).where(col(Team.league_id).in_(league_ids))
    ).all()
    teams_by_league: dict[tuple[int, str], Team] = {
        (t.league_id, t.name): t for t in team_rows
    }

    # `team` normally shows up as a match's home or away text — but a third,
    # text-less "_extra" perspective also exists (see tasks/fetcher.py's
    # DBStore.save/F1Filter — e.g. F1's "Formula 1" pseudo-team, which every
    # session belongs to without being the home_team/Grand-Prix or away_team/
    # session text). Resolve which events that covers up front.
    extra_event_ids: set[str] = set()
    if team:
        extra_rows = session.exec(
            select(Match.external_id)
            .join(Team, col(Match.team_id) == col(Team.id))
            .where(Team.slug == team, Match.external_id.endswith("_extra"))
        ).all()
        extra_event_ids = {eid.rsplit("_", 1)[0] for eid in extra_rows}

    result: list[MatchOut] = []
    for match, home_team, lg, sp in rows:
        assert match.id is not None and lg.id is not None  # persisted rows
        away_team = teams_by_league.get((lg.id, match.away_team))

        if team:
            base_id = match.external_id.rsplit("_", 1)[0]
            is_home_or_away = home_team.slug == team or (away_team is not None and away_team.slug == team)
            if not is_home_or_away and base_id not in extra_event_ids:
                continue

        # Stored naive but always UTC — stamp tz so the wire value is ISO-UTC.
        start = match.start_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        result.append(MatchOut(
            id=match.id,
            external_id=match.external_id,
            sport=sp.slug,
            league=LeagueOut(name=lg.name, slug=lg.slug, supports_standings=standings_supported(lg.slug)),
            home_team=match.home_team,
            away_team=match.away_team,
            home_slug=home_team.slug,
            away_slug=away_team.slug if away_team else None,
            home_icon=home_team.icon,
            away_icon=away_team.icon if away_team else None,
            home_score=match.home_score,
            away_score=match.away_score,
            start_time=start,
            venue=match.venue,
        ))

    return result[:limit]
