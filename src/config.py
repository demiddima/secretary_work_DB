# src/config.py

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database
    DB_HOST: str = Field(..., env="DB_HOST")
    DB_PORT: int = Field(3306, env="DB_PORT")  # MySQL по умолчанию
    DB_USER: str = Field(..., env="DB_USER")
    DB_PASSWORD: str = Field(..., env="DB_PASSWORD")
    DB_NAME: str = Field(..., env="DB_NAME")

    # Параметры пула (новые имена — предпочтительны)
    POOL_SIZE: int = Field(10, env="POOL_SIZE")
    MAX_OVERFLOW: int = Field(20, env="MAX_OVERFLOW")
    POOL_TIMEOUT: int = Field(30, env="POOL_TIMEOUT")       # секунды
    POOL_RECYCLE: int = Field(1800, env="POOL_RECYCLE")     # секунды

    # Совместимость со старыми именами
    POOL_MIN_SIZE: int | None = Field(None, env="POOL_MIN_SIZE")
    POOL_MAX_SIZE: int | None = Field(None, env="POOL_MAX_SIZE")

    # Прочее
    TELEGRAM_BOT_TOKEN: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    LOG_CHANNEL_ID: int = Field(..., env="LOG_CHANNEL_ID")

    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    API_KEY_VALUE: str = Field(..., env="API_KEY_VALUE")

    @property
    def resolved_pool_size(self) -> int:
        return int(self.POOL_MIN_SIZE) if self.POOL_MIN_SIZE not in (None, 0) else int(self.POOL_SIZE)

    @property
    def resolved_max_overflow(self) -> int:
        return int(self.POOL_MAX_SIZE) if self.POOL_MAX_SIZE not in (None, 0) else int(self.MAX_OVERFLOW)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
