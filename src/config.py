from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DB_HOST: str = Field(..., env='DB_HOST')
    DB_PORT: int = Field(5432, env='DB_PORT')
    DB_USER: str = Field(..., env='DB_USER')
    DB_PASSWORD: str = Field(..., env='DB_PASSWORD')
    DB_NAME: str = Field(..., env='DB_NAME')
    POOL_MIN_SIZE: int = Field(1, env='POOL_MIN_SIZE')
    POOL_MAX_SIZE: int = Field(10, env='POOL_MAX_SIZE')

    LOG_LEVEL: str = Field('INFO', env='LOG_LEVEL')
    TELEGRAM_BOT_TOKEN: str = Field(..., env='TELEGRAM_BOT_TOKEN')
    LOG_CHANNEL_ID: int = Field(..., env='LOG_CHANNEL_ID')

    JWT_SECRET_KEY: str = Field(..., env='jwt_secret_key')
    API_KEY_VALUE: str = Field(..., env='api_key_value')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()
