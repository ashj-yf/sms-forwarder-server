from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SmsForwarder Server"
    database_url: str = "sqlite:///./smsf.db"
    public_base_url: str = "http://localhost:8000"
    jwt_secret: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    app_secret: str = Field(default="change-me-app-secret-at-least-32-chars", min_length=16)
    http_timeout_seconds: float = 10.0
    webhook_rate_limit_per_minute: int = 120
    user_query_rate_limit_per_minute: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
