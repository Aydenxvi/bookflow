"""Application settings, loaded from environment variables (see .env.example)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "BookFlow API"
    environment: str = "development"  # development | test | production
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://bookflow:bookflow@localhost:5432/bookflow"

    # Auth / security
    telegram_bot_token: str | None = None  # required to verify real Telegram initData; None => Telegram auth disabled
    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_ttl_minutes: int = 60 * 24  # 24h
    telegram_init_data_max_age_seconds: int = 24 * 60 * 60  # reject initData older than this

    demo_mode_enabled: bool = True
    demo_business_slug: str = "atelier"

    # CORS
    cors_allow_origins: list[str] = ["http://localhost:5173", "http://localhost:4173"]

    # Rate limiting (simple in-process token bucket defaults; see app/core/rate_limit.py)
    rate_limit_booking_per_minute: int = 10

    # Business defaults
    default_timezone: str = "Europe/Istanbul"
    default_currency: str = "USD"


@lru_cache
def get_settings() -> Settings:
    return Settings()
