# src/crud/base.py

from __future__ import annotations

from contextlib import asynccontextmanager

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.exc import OperationalError, IntegrityError, SQLAlchemyError
from sqlalchemy import select, delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.mysql import insert as mysql_insert


# Ретрай только на сетевые/коннектовые проблемы с БД
retry_db = retry(
    reraise=True,
    retry=retry_if_exception_type(OperationalError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)


@asynccontextmanager
async def db_tx(session: AsyncSession):
    """
    Единый менеджер транзакций для CRUD.

    - Если транзакции НЕТ: открываем обычную transaction (BEGIN) и на выходе COMMIT/ROLLBACK.
    - Если транзакция ЕСТЬ: открываем SAVEPOINT (BEGIN NESTED),
      чтобы вложенные CRUD-функции не ломали родителя и могли безопасно ретраиться.
    """
    if session.in_transaction():
        async with session.begin_nested():
            yield
    else:
        async with session.begin():
            yield
