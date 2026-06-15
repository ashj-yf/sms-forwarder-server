from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

FRPS_BIND_PORT = 7000


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
    frps_enabled: bool = False
    frps_internal_host: str = "127.0.0.1"
    frps_public_host: str = "localhost"
    frps_auth_token: str = "change-me-frps-token"
    frps_allow_port_min: int = 17000
    frps_allow_port_max: int = 17999
    frps_dashboard_port: int = 7500
    frps_dashboard_user: str = "admin"
    frps_dashboard_password: str = "change-me"
    tunnel_proxy_default_use_encryption: bool = True
    tunnel_proxy_default_use_compression: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
