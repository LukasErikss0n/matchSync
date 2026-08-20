import logging
from datetime import datetime, timezone

import resend
from config import RESEND_API_KEY, SUPPORT_EMAIL
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

SUPPORT_TYPE_LABELS = {"bug": "Bug", "improvement": "Improvement", "other": "Other"}


class SupportRequest(BaseModel):
    type: str = Field(pattern="^(bug|improvement|other)$")
    text: str = Field(min_length=1, max_length=4000)
    page: str | None = None
    device: str = Field(min_length=1, max_length=200)
    email: str | None = None


@router.post("/support")
def send_support_request(payload: SupportRequest):
    if not RESEND_API_KEY:
        logger.error("Support request received but RESEND_API_KEY is not configured")
        raise HTTPException(status_code=503, detail="Couldn't send your report, please try again later")

    lines = [
        f"Type: {SUPPORT_TYPE_LABELS.get(payload.type, payload.type)}",
        f"Device: {payload.device}",
    ]
    if payload.page:
        lines.append(f"Page: {payload.page}")
    if payload.email:
        lines.append(f"Reply-to: {payload.email}")
    lines.append("")
    lines.append(payload.text)

    try:
        resend.api_key = RESEND_API_KEY
        email_payload: dict = {
            "from": "support-form@matchcalender.com",
            "to": SUPPORT_EMAIL,
            "subject": f"[{SUPPORT_TYPE_LABELS.get(payload.type, payload.type)}] MatchCalender report — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "text": "\n".join(lines),
        }
        if payload.email:
            email_payload["reply_to"] = payload.email
        resend.Emails.send(email_payload)
    except Exception as e:
        logger.error("Failed to send support report via Resend: %s", e)
        raise HTTPException(status_code=502, detail="Couldn't send your report, please try again later")

    return {"status": "ok"}
