from sqlalchemy.ext.asyncio import AsyncSession
from .database import AsyncSessionLocal
from .security import get_api_key

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# get_api_key просто реэкспортируем, если нужно
