# src/database.py
# commit: безопасная сборка DATABASE_URL (urlencode пароля) + неизменная async SQLAlchemy база

from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import settings


def _build_database_url() -> str:
    user = settings.DB_USER
    password = quote_plus(settings.DB_PASSWORD)
    host = settings.DB_HOST
    port = settings.DB_PORT
    name = settings.DB_NAME
    return f"mysql+aiomysql://{user}:{password}@{host}:{port}/{name}"


DATABASE_URL = _build_database_url()

engine = create_async_engine(
    DATABASE_URL,
    pool_size=settings.resolved_pool_size,
    max_overflow=settings.resolved_max_overflow,
    pool_timeout=settings.POOL_TIMEOUT,
    pool_recycle=settings.POOL_RECYCLE,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()


async def init_db() -> None:
    """Создать таблицы по текущим моделям (опционально)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
