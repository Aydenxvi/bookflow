"""Bot settings, loaded from environment variables (see .env.example)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # From @BotFather. Left unset in this environment — see repo root
    # CLAUDE.md / PROGRESS.md: no real bot token was available when this was
    # built, so this module has been written and structurally reviewed but
    # never actually run against Telegram's servers.
    bot_token: str = ""

    # The deployed Telegram Mini App URL (must be https:// for Telegram to
    # accept it as a WebApp button — see README.md for BotFather setup).
    mini_app_url: str = "https://example.com"

    support_contact: str = "@bookflow_support"


def get_settings() -> Settings:
    return Settings()
