"""Конфигурация приложения."""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки из переменных окружения или .env файла."""

    model_config = SettingsConfigDict(env_file=".env")

    provider_base_url: str = "http://student-system-events-provider-web.student-system-events-provider.svc:8000"
    provider_api_key: str = "RsOB79YmORuaILmZoVrDJIl5mPq8R091jpR8HW7UbnM"
    host: str = "0.0.0.0"
    port: int = 8000
    sync_interval_hours: int = 24
    request_timeout: float = 10.0
    database_url: str = ""


settings = Settings()

if not settings.database_url:
    conn_str = os.getenv("POSTGRES_CONNECTION_STRING", "")
    if conn_str:
        settings.database_url = conn_str.replace("postgres://", "postgresql+asyncpg://")
