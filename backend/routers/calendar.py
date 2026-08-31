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
    """Return all (Team, League) rows matching the given sport+team and (optionally) league filter."""
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

    # Every issued link gets its own token, which is the only thing that
    # distinguishes two people subscribing to the same team and leagues —
    # without it their feed requests are identical and count as one.
    # Sorted so the stored form doesn't depend on the order the user happened
    # to tick the league checkboxes.
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


def _record_fetch(session: Session, token: str | None, user_agent: str | None) -> None:
    """Stamp a subscription as alive.

    Deliberately never raises and never 404s on an unknown token: this runs on
    the path a subscriber's calendar app polls, and breaking someone's feed to
    protect a metric would be the wrong trade. Links issued before tokens
    existed simply carry no id and go unrecorded.
    """
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
        row.last_user_agent = (user_agent or None) and user_agent[:200]
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
    # league name per team row, so each event title can say which competition it is
    league_by_team = {t.id: l.name for t, l in rows if t.id is not None}
    ics_bytes = build_ics(team_name, list(matches), league_by_team)
    _record_fetch(session, id, request.headers.get("user-agent"))
    return Response(
        content=ics_bytes,
        media_type="text/calendar",
        # A cached feed is a poll that never reaches us — it would both serve
        # stale fixtures and make an active subscriber look dormant.
        headers={"Cache-Control": "no-store"},
    )
