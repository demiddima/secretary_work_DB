# src/config.py
# commit: нормализация настроек пула + стабилизация imports для pydantic_settings

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DB_HOST: str = Field(..., validation_alias="DB_HOST")
    DB_PORT: int = Field(3306, validation_alias="DB_PORT")
    DB_USER: str = Field(..., validation_alias="DB_USER")
    DB_PASSWORD: str = Field(..., validation_alias="DB_PASSWORD")
    DB_NAME: str = Field(..., validation_alias="DB_NAME")

    # Pool (предпочтительные имена)
    POOL_SIZE: int = Field(10, validation_alias="POOL_SIZE")
    MAX_OVERFLOW: int = Field(20, validation_alias="MAX_OVERFLOW")
    POOL_TIMEOUT: int = Field(30, validation_alias="POOL_TIMEOUT")   # seconds
    POOL_RECYCLE: int = Field(1800, validation_alias="POOL_RECYCLE")  # seconds

    # Legacy совместимость
    POOL_MIN_SIZE: int | None = Field(None, validation_alias="POOL_MIN_SIZE")
    POOL_MAX_SIZE: int | None = Field(None, validation_alias="POOL_MAX_SIZE")

    # Logging / Telegram
    TELEGRAM_BOT_TOKEN: str = Field(..., validation_alias="TELEGRAM_BOT_TOKEN")
    LOG_CHANNEL_ID: int = Field(..., validation_alias="LOG_CHANNEL_ID")

    # Auth
    JWT_SECRET_KEY: str = Field(..., validation_alias="JWT_SECRET_KEY")
    API_KEY_VALUE: str = Field(..., validation_alias="API_KEY_VALUE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @staticmethod
    def _safe_int(value: int | None, fallback: int) -> int:
        if value is None:
            return int(fallback)
        return int(value)

    @property
    def resolved_pool_size(self) -> int:
        v = self._safe_int(self.POOL_MIN_SIZE, self.POOL_SIZE)
        return max(0, v)

    @property
    def resolved_max_overflow(self) -> int:
        v = self._safe_int(self.POOL_MAX_SIZE, self.MAX_OVERFLOW)
        return max(0, v)


settings = Settings()
