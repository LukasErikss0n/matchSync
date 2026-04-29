from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlmodel import Session, select
from database import get_session
from models.models import League, Match, Team
from schemas.schemas import CalendarLink
from services.ics_builder import build_ics
from config import BASE_WEBCAL_URL

router = APIRouter()


@router.get("/calendar", response_model=CalendarLink)
def get_calendar_link(team: str, league: str, session: Session = Depends(get_session)):
    league_row = session.exec(select(League).where(League.name == league)).first()
    if not league_row:
        raise HTTPException(status_code=404, detail="League not found")
    team_row = session.exec(
        select(Team).where(Team.name == team, Team.league_id == league_row.id)
    ).first()
    if not team_row:
        raise HTTPException(status_code=404, detail="Team not found")
    url = f"{BASE_WEBCAL_URL}/{league_row.slug}/{team_row.slug}.ics"
    return CalendarLink(team=team, league=league, url=url)


@router.get("/calendar/{league_slug}/{team_slug}.ics")
def get_ics(league_slug: str, team_slug: str, session: Session = Depends(get_session)):
    league_row = session.exec(select(League).where(League.slug == league_slug)).first()
    if not league_row:
        raise HTTPException(status_code=404, detail="League not found")
    team_row = session.exec(
        select(Team).where(Team.slug == team_slug, Team.league_id == league_row.id)
    ).first()
    if not team_row:
        raise HTTPException(status_code=404, detail="Team not found")
    matches = session.exec(select(Match).where(Match.team_id == team_row.id)).all()
    ics_bytes = build_ics(team_row.name, list(matches))
    return Response(content=ics_bytes, media_type="text/calendar")
