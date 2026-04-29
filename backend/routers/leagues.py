import re
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.models import League, Sport, Team
from schemas.schemas import SportOut


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

router = APIRouter()


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
            leagues=[l.name for l in leagues],
        ))
    return result


@router.get("/leagues/{slug}/teams", response_model=list[str])
def get_teams(slug: str, session: Session = Depends(get_session)):
    # Try stored slug first, then fall back to matching against slugified display name
    # (handles mismatch between key-based slugs in DB and name-based slugs from frontend)
    league = session.exec(select(League).where(League.slug == slug)).first()
    if not league:
        all_leagues = session.exec(select(League)).all()
        league = next((l for l in all_leagues if _slugify(l.name) == slug), None)
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    teams = session.exec(select(Team).where(Team.league_id == league.id)).all()
    return [t.name for t in teams]
