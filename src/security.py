# src/security.py

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from .config import settings

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


def get_api_key(api_key: str | None = Security(api_key_header)) -> str:
    expected_key = settings.API_KEY_VALUE

    if not expected_key:
        raise HTTPException(status_code=500, detail="API key is not configured on server")

    if not api_key or api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

    return api_key
