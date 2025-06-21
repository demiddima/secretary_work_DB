import os
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-KEY")  # Имя заголовка (можно поменять)

def get_api_key(api_key: str = Security(api_key_header)):
    expected_key = os.getenv("API_KEY_VALUE")
    if api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    return api_key
