from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# Строка подключения к базе данных
DATABASE_URL = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# Создание асинхронного движка и сессии
engine = create_async_engine(
    DATABASE_URL,
    pool_size=settings.POOL_MIN_SIZE,
    max_overflow=settings.POOL_MAX_SIZE,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()

async def init_db():
    '''
    Инициализирует базу данных: создает все таблицы, описанные в моделях.
    '''
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
