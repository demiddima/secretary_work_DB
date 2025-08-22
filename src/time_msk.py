# src/time_msk.py
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

MSK = ZoneInfo("Europe/Moscow")

def now_msk_aware() -> datetime:
    """Текущее московское время (aware, tzinfo=Europe/Moscow)."""
    return datetime.now(MSK)

def now_msk_naive() -> datetime:
    """Текущее московское время, но 'naive' (без tzinfo) — то, что пишем в БД."""
    return now_msk_aware().replace(tzinfo=None)

def to_msk_naive(dt: datetime) -> datetime:
    """
    Любой datetime → наивный МСК.
    - Если dt aware с любой TZ → перевод в MSK и drop tzinfo.
    - Если dt naive → считаем, что это уже МСК, просто возвращаем копию.
    """
    if dt.tzinfo is not None:
        return dt.astimezone(MSK).replace(tzinfo=None)
    return dt
