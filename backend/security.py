import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from config import ADMIN_TOKEN, API_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
admin_token_header = APIKeyHeader(name="X-Admin-Token", auto_error=False)


def require_api_key(key: str | None = Security(api_key_header)) -> None:
    if not API_KEY:
        return
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def require_admin_token(token: str | None = Security(admin_token_header)) -> None:
    if not ADMIN_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Admin dashboard is not configured (ADMIN_TOKEN unset)",
        )
    if not token or not secrets.compare_digest(token, ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")
