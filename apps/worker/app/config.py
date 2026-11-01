"""Worker settings, loaded from environment variables (see .env.example)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://bookflow:bookflow@localhost:5432/bookflow"

    # From @BotFather. Left unset in this environment — see repo root
    # CLAUDE.md / PROGRESS.md: no real bot token was available when this was
    # built, so sending has been written and unit-tested against a mocked
    # Telegram HTTP call, but never exercised against Telegram's real servers.
    telegram_bot_token: str = ""

    poll_interval_seconds: float = 5.0

    # Retry/backoff for a failed send (network error, non-2xx from Telegram).
    max_attempts: int = 5
    backoff_base_seconds: int = 30
    backoff_max_seconds: int = 3600

    # Local hour (in each business's own timezone) at which that business's
    # daily summary job is scheduled, when notify_business_daily_summary is on.
    daily_summary_local_hour: int = 20


def get_settings() -> Settings:
    return Settings()
