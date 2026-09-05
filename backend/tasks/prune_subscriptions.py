from datetime import datetime, timedelta, timezone

from sqlmodel import Session, col, delete

from database import engine
from models.models import CalendarSubscription

PENDING_TTL_DAYS = 7
DORMANT_TTL_DAYS = 365


def prune_subscriptions() -> tuple[int, int]:
    now = datetime.now(timezone.utc)
    pending_cutoff = now - timedelta(days=PENDING_TTL_DAYS)
    dormant_cutoff = now - timedelta(days=DORMANT_TTL_DAYS)

    with Session(engine) as session:
        pending = session.exec(
            delete(CalendarSubscription).where(
                col(CalendarSubscription.last_seen).is_(None),
                col(CalendarSubscription.created_at) < pending_cutoff,
            )
        )
        dormant = session.exec(
            delete(CalendarSubscription).where(
                col(CalendarSubscription.last_seen) < dormant_cutoff
            )
        )
        session.commit()
        return pending.rowcount or 0, dormant.rowcount or 0
