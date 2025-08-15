# src/dependencies.py

from sqlalchemy.ext.asyncio import AsyncSession
from .database import AsyncSessionLocal
from .security import get_api_key  # noqa: F401


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
