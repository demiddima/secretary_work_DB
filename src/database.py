# src/database.py

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from .config import settings

# DSN MySQL через aiomysql
DATABASE_URL = (
    f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# Асинхронный движок с явными параметрами пула
engine = create_async_engine(
    DATABASE_URL,
    pool_size=settings.resolved_pool_size,          # по умолчанию 10 или из LEGACY
    max_overflow=settings.resolved_max_overflow,    # по умолчанию 20 или из LEGACY
    pool_timeout=settings.POOL_TIMEOUT,             # ожидание свободного коннекта
    pool_recycle=settings.POOL_RECYCLE,             # рецикл раньше mysql wait_timeout
    pool_pre_ping=True,                             # проверка «мёртвых» коннектов
    echo=False,
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# База моделей
Base = declarative_base()


async def init_db() -> None:
    """Создать таблицы по моделям (опционально)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
