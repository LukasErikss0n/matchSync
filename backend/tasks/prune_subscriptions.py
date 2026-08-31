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

# A subscription that has gone a full year without a single fetch is gone —
# unsubscribed, or the calendar it lived in was deleted. Well beyond any
# plausible refresh interval (Apple's slowest setting is weekly), so an active
# subscriber can't be caught by it, and it gives the privacy policy a concrete
# retention figure instead of "as long as it exists".
DORMANT_TTL_DAYS = 365


def prune_subscriptions() -> tuple[int, int]:
    """Delete abandoned and long-dead calendar links.

    Returns (pending_deleted, dormant_deleted).
    """
    now = datetime.now(timezone.utc)
    pending_cutoff = now - timedelta(days=PENDING_TTL_DAYS)
    dormant_cutoff = now - timedelta(days=DORMANT_TTL_DAYS)

    with Session(engine) as session:
        # Issued but never once fetched.
        pending = session.exec(
            delete(CalendarSubscription).where(
                col(CalendarSubscription.last_seen).is_(None),
                col(CalendarSubscription.created_at) < pending_cutoff,
            )
        )
        # Fetched at some point, then silent for a year. Comparing last_seen
        # against a date is enough to exclude never-fetched rows on its own:
        # in SQL, NULL < value is NULL, never true, so those fall to the
        # pending rule above rather than being caught by both.
        dormant = session.exec(
            delete(CalendarSubscription).where(
                col(CalendarSubscription.last_seen) < dormant_cutoff
            )
        )
        session.commit()
        return pending.rowcount or 0, dormant.rowcount or 0
