# src/audience_sql.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List
import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AudienceSQLValidationError(ValueError):
    """SQL-запрос для аудитории не прошёл валидацию."""


# Базовые запреты: не даём выполнить DDL/DML и прочие опасные штуки.
_FORBIDDEN = (
    r"\binsert\b",
    r"\bupdate\b",
    r"\bdelete\b",
    r"\bdrop\b",
    r"\balter\b",
    r"\bcreate\b",
    r"\btruncate\b",
    r"\bgrant\b",
    r"\brevoke\b",
    r"\battach\b",
    r"\bcommit\b",
    r"\brollback\b",
    r";",              # несколько стейтментов
)
_FORBIDDEN_RE = re.compile("|".join(_FORBIDDEN), flags=re.IGNORECASE | re.DOTALL)

# Требуем, чтобы в итоговой выборке был столбец user_id (int).
# Мы всё равно оборачиваем запрос снаружи, но это помогает отлавливать явные ошибки раньше.
_USER_ID_RE = re.compile(r"\buser_id\b", flags=re.IGNORECASE)


def validate_sql(sql: str) -> None:
    """
    Минимальная безопасная валидация пользовательского SQL.
    Разрешаем только SELECT-подзапрос, без точек с запятой и DDL/DML.
    Запрос должен возвращать user_id (мы позже оборачиваем DISTINCT+LIMIT).
    """
    if not sql or not isinstance(sql, str):
        raise AudienceSQLValidationError("SQL пустой")

    sql_stripped = sql.strip()

    # Должен начинаться с SELECT (или с комментариев + SELECT)
    if not re.search(r"^\s*select\b", sql_stripped, flags=re.IGNORECASE):
        raise AudienceSQLValidationError("Разрешён только SELECT-запрос")

    # Запрещённые конструкции
    if _FORBIDDEN_RE.search(sql_stripped):
        raise AudienceSQLValidationError("Запрос содержит запрещённые конструкции")

    # Должен фигурировать user_id (хотя бы где-то в запросе)
    if not _USER_ID_RE.search(sql_stripped):
        raise AudienceSQLValidationError("Запрос должен возвращать поле user_id")

    # Небольшая защита от слишком длинных запросов
    if len(sql_stripped) > 100_000:
        raise AudienceSQLValidationError("Слишком длинный SQL")


async def exec_preview(session: AsyncSession, sql: str, limit: int = 1000) -> List[int]:
    """
    Выполнить пользовательский SQL безопасно и вернуть список уникальных user_id.
    Реальный запрос исполняется как:

        SELECT DISTINCT user_id
        FROM (
            <ПОЛЬЗОВАТЕЛЬСКИЙ_SQL>
        ) AS _aud
        LIMIT :limit

    Параметр limit связывается через bind-параметры.
    """
    validate_sql(sql)

    # Оборачиваем во внешний SELECT, чтобы навязать DISTINCT user_id + LIMIT.
    wrapper = (
        "SELECT DISTINCT user_id "
        "FROM ( " + sql + " ) AS _aud "
        "LIMIT :limit"
    )

    res = await session.execute(text(wrapper), {"limit": int(max(0, limit))})
    rows: Iterable[tuple] = res.fetchall()  # ожидаем одну колонку: user_id
    ids: List[int] = [int(r[0]) for r in rows if r and r[0] is not None]
    return ids
