import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlmodel import Session, col, select
from database import get_session
from models.models import CalendarSubscription, League, Match, Sport, Team
from schemas.schemas import CalendarLink, LeagueOut
from services.ics_builder import build_ics
from config import BASE_WEBCAL_URL
from security import require_api_key

router = APIRouter()


def _parse_league_slugs(leagues: str | None) -> list[str]:
    if not leagues:
        return []
    return [s.strip() for s in leagues.split(",") if s.strip()]


def _resolve_team_rows(
    session: Session,
    sport_slug: str,
    team_slug: str,
    league_slugs: list[str] | None,
) -> list[tuple[Team, League]]:
    sport_row = session.exec(select(Sport).where(Sport.slug == sport_slug)).first()
    if not sport_row:
        raise HTTPException(status_code=404, detail="Sport not found")

    stmt = (
        select(Team, League)
        .join(League, col(Team.league_id) == col(League.id))
        .where(Team.slug == team_slug, League.sport_id == sport_row.id)
    )
    if league_slugs:
        stmt = stmt.where(col(League.slug).in_(league_slugs))

    rows = session.exec(stmt).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Team not found in given leagues")
    return list(rows)


@router.get(
    "/calendar",
    response_model=CalendarLink,
    dependencies=[Depends(require_api_key)],
)
def get_calendar_link(
    sport: str,
    team: str,
    leagues: str = Query(..., description="Comma-separated league slugs"),
    session: Session = Depends(get_session),
):
    league_slugs = _parse_league_slugs(leagues)
    if not league_slugs:
        raise HTTPException(status_code=400, detail="At least one league is required")

    rows = _resolve_team_rows(session, sport, team, league_slugs)
    team_name = rows[0][0].name
    league_outs = [LeagueOut(name=l.name, slug=l.slug) for _, l in rows]

    token = secrets.token_urlsafe(9)
    session.add(
        CalendarSubscription(
            token=token,
            sport_slug=sport,
            team_slug=team,
            team_name=team_name,
            leagues=",".join(sorted(league_slugs)),
            created_at=datetime.now(timezone.utc),
        )
    )
    session.commit()

    url = (
        f"{BASE_WEBCAL_URL}/{sport}/{team}.ics"
        f"?leagues={','.join(league_slugs)}&id={token}"
    )
    return CalendarLink(team=team_name, sport=sport, leagues=league_outs, url=url)


def _client_label(user_agent: str | None) -> str | None:
    if not user_agent:
        return None
    ua = user_agent.lower()
    if "google" in ua:
        return "Google Calendar"
    if "outlook" in ua or "microsoft" in ua:
        return "Outlook"
    if "thunderbird" in ua:
        return "Thunderbird"
    if any(k in ua for k in ("ical", "dataaccessd", "macos", "mac os", "ios", "cfnetwork")):
        return "Apple Calendar"
    if any(k in ua for k in ("mozilla", "chrome", "safari", "firefox")):
        return "Web browser"
    return "Other"


def _record_fetch(session: Session, token: str | None, user_agent: str | None) -> None:
    if not token:
        return
    try:
        row = session.exec(
            select(CalendarSubscription).where(CalendarSubscription.token == token)
        ).first()
        if row is None:
            return
        row.last_seen = datetime.now(timezone.utc)
        row.fetch_count += 1
        row.last_user_agent = _client_label(user_agent)
        session.add(row)
        session.commit()
    except Exception:
        session.rollback()


@router.get("/calendar/{sport_slug}/{team_slug}.ics")
def get_ics(
    request: Request,
    sport_slug: str,
    team_slug: str,
    leagues: str | None = None,
    id: str | None = None,
    session: Session = Depends(get_session),
):
    league_slugs = _parse_league_slugs(leagues)
    rows = _resolve_team_rows(session, sport_slug, team_slug, league_slugs or None)

    team_ids = [t.id for t, _ in rows if t.id is not None]
    now = datetime.now(timezone.utc)
    matches = session.exec(
        select(Match).where(col(Match.team_id).in_(team_ids), Match.start_time > now)
    ).all()

    team_name = rows[0][0].name
    league_by_team = {t.id: l.name for t, l in rows if t.id is not None}
    ics_bytes = build_ics(team_name, list(matches), league_by_team)
    _record_fetch(session, id, request.headers.get("user-agent"))
    return Response(
        content=ics_bytes,
        media_type="text/calendar",
        headers={"Cache-Control": "no-store"},
    )
