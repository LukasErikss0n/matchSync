from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, col, select

from database import get_session
from models.models import CalendarSubscription
from schemas.schemas import CalendarSubscriptionOut, SubscriptionDashboardOut
from security import require_admin_token
from utils import ensure_utc

router = APIRouter()

DEFAULT_ACTIVE_WINDOW_DAYS = 7


@router.get(
    "/admin/subscriptions",
    response_model=SubscriptionDashboardOut,
    dependencies=[Depends(require_admin_token)],
)
def list_subscriptions(
    window_days: int = Query(
        DEFAULT_ACTIVE_WINDOW_DAYS, ge=1, le=90, description="Active-window length"
    ),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(CalendarSubscription).order_by(
            col(CalendarSubscription.last_seen).desc().nullslast(),
            col(CalendarSubscription.created_at).desc(),
        )
    ).all()

    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    out: list[CalendarSubscriptionOut] = []
    active = pending = dormant = 0

    for row in rows:
        last_seen = ensure_utc(row.last_seen) if row.last_seen is not None else None

        if last_seen is None:
            pending += 1
            is_active = False
        elif last_seen >= cutoff:
            active += 1
            is_active = True
        else:
            dormant += 1
            is_active = False

        out.append(
            CalendarSubscriptionOut(
                token=row.token,
                sport=row.sport_slug,
                team=row.team_name,
                leagues=[s for s in row.leagues.split(",") if s],
                created_at=row.created_at,
                last_seen=last_seen,
                fetch_count=row.fetch_count,
                last_user_agent=row.last_user_agent,
                active=is_active,
            )
        )

    return SubscriptionDashboardOut(
        active_count=active,
        pending_count=pending,
        dormant_count=dormant,
        active_window_days=window_days,
        subscriptions=out,
    )
