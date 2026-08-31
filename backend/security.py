import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from config import ADMIN_TOKEN, API_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
admin_token_header = APIKeyHeader(name="X-Admin-Token", auto_error=False)


def require_api_key(key: str | None = Security(api_key_header)) -> None:
    """Reject requests without the correct X-API-Key header.

    If API_KEY is unset in the environment, auth is disabled (local dev).
    """
    if not API_KEY:
        return
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def require_admin_token(token: str | None = Security(admin_token_header)) -> None:
    """Gate the admin dashboard behind a secret the browser proxy never adds.

    Fails closed when ADMIN_TOKEN is unset, unlike require_api_key. That
    asymmetry is deliberate: an unset API_KEY only opens read-only public
    fixture data in local dev, whereas leaving this open would publish every
    subscriber's feed token to anyone who guessed the URL.
    """
    if not ADMIN_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Admin dashboard is not configured (ADMIN_TOKEN unset)",
        )
    # Constant-time: this token is guessable-by-brute-force in a way the
    # fixture endpoints' key is not.
    if not token or not secrets.compare_digest(token, ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")
