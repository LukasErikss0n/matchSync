from datetime import datetime, timedelta, timezone

from sqlmodel import Session, col, delete

from database import engine
from models.models import CalendarSubscription

# A calendar client fetches within seconds of the user subscribing, so a link
# still unfetched days later was generated and abandoned — someone reached the
# final wizard step, looked at the URL, and closed the tab. Generous anyway:
# the cost of keeping a row too long is a bit of dashboard noise, while
# deleting one too early would break a real subscriber's feed.
PENDING_TTL_DAYS = 7


def prune_pending_subscriptions() -> int:
    """Delete links that were issued but never once fetched.

    Only ever touches rows with `last_seen IS NULL`. Anything that has been
    fetched even once is a real subscription and is kept regardless of age —
    a dormant row is meaningful (someone unsubscribed), an unfetched one is
    not.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=PENDING_TTL_DAYS)
    with Session(engine) as session:
        result = session.exec(
            delete(CalendarSubscription).where(
                col(CalendarSubscription.last_seen).is_(None),
                col(CalendarSubscription.created_at) < cutoff,
            )
        )
        session.commit()
        return result.rowcount or 0
