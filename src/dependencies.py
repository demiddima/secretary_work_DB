# src/dependencies.py
# commit: приведены импорты/типизация; зависимость get_api_key сохраняется для использования в роутерах через Depends

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from .database import AsyncSessionLocal
from .security import get_api_key  # noqa: F401  (используется как Depends(get_api_key) в роутерах)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
