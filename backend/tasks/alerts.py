from datetime import datetime

import resend

from config import ALERT_EMAIL, RESEND_API_KEY
from tasks.common import LOCAL_TZ


def send_error_email(error: str) -> None:
    if not RESEND_API_KEY or not ALERT_EMAIL:
        print("[fetcher] email not configured, skipping alert")
        return
    try:
        resend.api_key = RESEND_API_KEY
        resp = resend.Emails.send(
            {
                "from": "alerts@matchcalender.com",
                "to": ALERT_EMAIL,
                "subject": "MatchCalender fetcher error",
                "text": f"MatchCalender fetcher failed at {datetime.now(LOCAL_TZ).isoformat()}\n\nError:\n{error}",
            }
        )
        email_id = resp.get("id") if isinstance(resp, dict) else None
        print(f"[fetcher] error alert queued with Resend (id={email_id or 'unknown'})")
    except Exception as e:
        print(f"[fetcher] failed to send alert email: {e}")
