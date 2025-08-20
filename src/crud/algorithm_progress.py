
from .base import retry_db, AsyncSession, select, delete
from src.models import UserAlgorithmProgress

@retry_db
async def get_user_step(session: AsyncSession, user_id: int):
    stmt = select(UserAlgorithmProgress.current_step).where(UserAlgorithmProgress.user_id == user_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()

@retry_db
async def set_user_step(session: AsyncSession, user_id: int, step: int):
    async with session.begin():
        obj = await session.get(UserAlgorithmProgress, user_id)
        if obj:
            obj.current_step = step
        else:
            obj = UserAlgorithmProgress(user_id=user_id, current_step=step)
            session.add(obj)
    return obj

@retry_db
async def get_basic_completed(session: AsyncSession, user_id: int):
    stmt = select(UserAlgorithmProgress.basic_completed).where(UserAlgorithmProgress.user_id == user_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()

@retry_db
async def set_basic_completed(session: AsyncSession, user_id: int, completed: bool):
    async with session.begin():
        obj = await session.get(UserAlgorithmProgress, user_id)
        if obj:
            obj.basic_completed = completed
        else:
            obj = UserAlgorithmProgress(user_id=user_id, basic_completed=completed)
            session.add(obj)
    return obj

@retry_db
async def get_advanced_completed(session: AsyncSession, user_id: int):
    stmt = select(UserAlgorithmProgress.advanced_completed).where(UserAlgorithmProgress.user_id == user_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()

@retry_db
async def set_advanced_completed(session: AsyncSession, user_id: int, completed: bool):
    async with session.begin():
        obj = await session.get(UserAlgorithmProgress, user_id)
        if obj:
            obj.advanced_completed = completed
        else:
            obj = UserAlgorithmProgress(user_id=user_id, advanced_completed=completed)
            session.add(obj)
    return obj

@retry_db
async def clear_user_data(session: AsyncSession, user_id: int):
    async with session.begin():
        await session.execute(delete(UserAlgorithmProgress).where(UserAlgorithmProgress.user_id == user_id))
