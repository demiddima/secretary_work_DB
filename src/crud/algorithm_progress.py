# src/crud/algorithm_progress.py
# commit: единый стиль get/set через ORM + транзакции; возврат ORM объекта для response_model

from __future__ import annotations

from .base import AsyncSession, delete, retry_db, select
from src.models import UserAlgorithmProgress


@retry_db
async def get_progress(session: AsyncSession, *, user_id: int) -> UserAlgorithmProgress | None:
    return await session.get(UserAlgorithmProgress, user_id)


@retry_db
async def set_user_step(session: AsyncSession, *, user_id: int, step: int) -> UserAlgorithmProgress:
    async with session.begin():
        obj = await session.get(UserAlgorithmProgress, user_id)
        if obj is None:
            obj = UserAlgorithmProgress(user_id=user_id, current_step=step)
            session.add(obj)
        else:
            obj.current_step = step
    return obj


@retry_db
async def set_basic_completed(session: AsyncSession, *, user_id: int, completed: bool) -> UserAlgorithmProgress:
    async with session.begin():
        obj = await session.get(UserAlgorithmProgress, user_id)
        if obj is None:
            obj = UserAlgorithmProgress(user_id=user_id, basic_completed=completed)
            session.add(obj)
        else:
            obj.basic_completed = completed
    return obj


@retry_db
async def set_advanced_completed(session: AsyncSession, *, user_id: int, completed: bool) -> UserAlgorithmProgress:
    async with session.begin():
        obj = await session.get(UserAlgorithmProgress, user_id)
        if obj is None:
            obj = UserAlgorithmProgress(user_id=user_id, advanced_completed=completed)
            session.add(obj)
        else:
            obj.advanced_completed = completed
    return obj


@retry_db
async def clear_user_data(session: AsyncSession, *, user_id: int) -> None:
    async with session.begin():
        await session.execute(delete(UserAlgorithmProgress).where(UserAlgorithmProgress.user_id == user_id))
