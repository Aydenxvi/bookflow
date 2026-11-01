from __future__ import annotations

from pydantic import BaseModel


class TelegramAuthRequest(BaseModel):
    init_data: str  # raw window.Telegram.WebApp.initData string


class DemoAuthRequest(BaseModel):
    business_slug: str | None = None  # defaults to settings.demo_business_slug


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_demo: bool
