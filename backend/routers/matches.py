from datetime import timezone

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from database import get_session
from models.models import League, Match, Sport, Team
from schemas.schemas import LeagueOut, MatchOut
from services.featured_match import get_featured_match
from services.standings import standings_supported

router = APIRouter()


@router.get("/matches/featured", response_model=MatchOut | None)
def featured_match(
    region: str | None = Query(
        default=None,
        min_length=2,
        max_length=2,
        pattern="^[A-Za-z]{2}$",
        description="ISO 3166-1 alpha-2 country code, guessed client-side, to nudge the visitor's domestic league",
    ),
    session: Session = Depends(get_session),
):
    """The single highest-scoring live/upcoming/recent match, for the hero card."""
    return get_featured_match(session, region)


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
        .join(Team, Match.team_id == Team.id)
        .join(League, Team.league_id == League.id)
        .join(Sport, League.sport_id == Sport.id)
        .where(Match.external_id.endswith("_home"))
    )
    if sport:
        stmt = stmt.where(Sport.slug == sport)
    if league:
        stmt = stmt.where(League.slug == league)

    rows = session.exec(stmt.order_by(Match.start_time)).all()
    if not rows:
        return []

    # Away crest/slug live on a different Team row — build a per-league lookup.
    league_ids = {lg.id for _, _, lg, _ in rows}
    team_rows = session.exec(
        select(Team).where(Team.league_id.in_(league_ids))
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
            .join(Team, Match.team_id == Team.id)
            .where(Team.slug == team, Match.external_id.endswith("_extra"))
        ).all()
        extra_event_ids = {eid.rsplit("_", 1)[0] for eid in extra_rows}

    result: list[MatchOut] = []
    for match, home_team, lg, sp in rows:
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
        ))

    return result[:limit]
