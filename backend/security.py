from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from config import API_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str | None = Security(api_key_header)) -> None:
    """Reject requests without the correct X-API-Key header.

    If API_KEY is unset in the environment, auth is disabled (local dev).
    """
    if not API_KEY:
        return
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
