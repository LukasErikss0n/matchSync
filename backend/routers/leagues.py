from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from database import get_session
from models.models import League, Sport, Team
from schemas.schemas import LeagueOut, SeasonStatsOut, SportOut, TeamOut
from services.season_stats import get_season_stats


router = APIRouter()

# National teams only ever show up here as one-off World Cup entries with no
# club-level league — they clutter the team search/picker without being
# useful there (the tournament still has its own SEO landing page).
TEAM_SEARCH_EXCLUDED_LEAGUE_SLUGS = {"fifa-world-cup-2026"}


@router.get("/sports", response_model=list[SportOut])
def get_sports(session: Session = Depends(get_session)):
    sports = session.exec(select(Sport)).all()
    result = []
    for sport in sports:
        leagues = session.exec(select(League).where(League.sport_id == sport.id)).all()
        result.append(SportOut(
            id=sport.slug,
            label=sport.name,
            icon=sport.icon,
            leagues=[LeagueOut(name=l.name, slug=l.slug) for l in leagues],
        ))
    return result


def _collect_teams(rows: list[tuple[Team, League, Sport]]) -> list[TeamOut]:
    """Group (team, league, sport) rows into TeamOut entries keyed by (sport_slug, team_slug)."""
    by_key: dict[tuple[str, str], TeamOut] = {}
    for team, league, sport in rows:
        key = (sport.slug, team.slug)
        entry = by_key.get(key)
        league_out = LeagueOut(name=league.name, slug=league.slug)
        if entry is None:
            by_key[key] = TeamOut(
                name=team.name,
                slug=team.slug,
                sport=sport.slug,
                icon=team.icon,
                leagues=[league_out],
            )
        elif entry.icon is None and team.icon:
            entry.icon = team.icon
        elif not any(l.slug == league.slug for l in entry.leagues):
            entry.leagues.append(league_out)
    return list(by_key.values())


@router.get("/teams", response_model=list[TeamOut])
def list_teams(
    sport: str | None = None,
    q: str | None = None,
    limit: int = Query(default=12, ge=1, le=200),
    session: Session = Depends(get_session),
):
    """List teams, optionally filtered by sport slug and search query.

    Returns deduplicated teams (one entry per (sport, team)) with all leagues
    each team competes in. Sorted by league count desc, then alphabetical.
    """
    stmt = (
        select(Team, League, Sport)
        .join(League, Team.league_id == League.id)
        .join(Sport, League.sport_id == Sport.id)
        .where(League.slug.not_in(TEAM_SEARCH_EXCLUDED_LEAGUE_SLUGS))
    )
    if sport:
        stmt = stmt.where(Sport.slug == sport)

    rows = session.exec(stmt).all()
    teams = _collect_teams(rows)

    if q:
        ql = q.lower()
        teams = [t for t in teams if ql in t.name.lower()]

    teams.sort(key=lambda t: (-len(t.leagues), t.name.lower()))
    return teams[:limit]


@router.get("/teams/{team_slug}", response_model=TeamOut)
def get_team(
    team_slug: str,
    sport: str | None = None,
    session: Session = Depends(get_session),
):
    """Fetch a single team (by slug) and its leagues. Sport disambiguates name collisions."""
    stmt = (
        select(Team, League, Sport)
        .join(League, Team.league_id == League.id)
        .join(Sport, League.sport_id == Sport.id)
        .where(Team.slug == team_slug)
    )
    if sport:
        stmt = stmt.where(Sport.slug == sport)

    rows = session.exec(stmt).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Team not found")

    teams = _collect_teams(rows)
    teams.sort(key=lambda t: -len(t.leagues))
    return teams[0]


@router.get("/leagues/{league_slug}/season-stats", response_model=SeasonStatsOut)
def league_season_stats(league_slug: str):
    """Season start date + regular-season match count, fetched live from the
    same external providers the fetcher uses (see services/season_stats.py) —
    not our own DB, which may only hold a partial rolling window."""
    stats = get_season_stats(league_slug)
    if stats is None:
        raise HTTPException(status_code=404, detail="Unknown league")
    return SeasonStatsOut(
        published=stats.published,
        season_start=stats.season_start,
        regular_season_count=stats.regular_season_count,
        progressive_knockout=stats.progressive_knockout,
    )
