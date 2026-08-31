from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, col, select

from database import get_session
from models.models import CalendarSubscription
from schemas.schemas import CalendarSubscriptionOut, SubscriptionDashboardOut
from security import require_admin_token

router = APIRouter()

# Calendar clients refresh on their own schedule and are not in a hurry about
# it — Google in particular can leave many hours between polls, and Apple lets
# the user pick an interval as slow as once a week. A window much tighter than
# this would report healthy subscriptions as dead.
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
        # Rows written before this column existed, and SQLite/Postgres driver
        # differences, can hand back a naive datetime — compare in UTC or the
        # subtraction raises.
        last_seen = row.last_seen
        if last_seen is not None and last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)

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
