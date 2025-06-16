from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# Формируем URL для подключения к MySQL через aiomysql
DATABASE_URL = (
    f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# Создаём асинхронный движок с проверкой живости соединений и отладочным выводом в DEBUG
engine = create_async_engine(
    DATABASE_URL,
    pool_size=settings.POOL_MIN_SIZE,
    max_overflow=settings.POOL_MAX_SIZE,
    pool_pre_ping=True,
    echo=(settings.LOG_LEVEL == "DEBUG"),
)

# Фабрика сессий
AsyncSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# Базовый класс для моделей
Base = declarative_base()

async def init_db():
    """
    Инициализирует базу данных: создаёт все таблицы по описанным моделям.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
