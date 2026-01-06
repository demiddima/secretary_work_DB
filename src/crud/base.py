# src/crud/base.py
# commit: унификация импорта и базовых sql helpers для CRUD; оставлен retry_db и часто используемые symbols

from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


retry_db = retry(
    reraise=True,
    retry=retry_if_exception_type(OperationalError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)

__all__ = [
    "retry_db",
    "AsyncSession",
    "select",
    "delete",
    "func",
    "update",
    "mysql_insert",
    "IntegrityError",
    "SQLAlchemyError",
    "HTTPException",
    "datetime",
]
