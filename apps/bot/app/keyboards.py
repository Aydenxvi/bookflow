"""Reply keyboard shown after /start (spec section 4: Open BookFlow /
My Appointments / How It Works / Contact Support)."""
from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from app.config import Settings

OPEN_BOOKFLOW = "📅 Open BookFlow"
MY_APPOINTMENTS = "🗓 My Appointments"
HOW_IT_WORKS = "ℹ️ How It Works"
CONTACT_SUPPORT = "💬 Contact Support"


def main_menu_keyboard(settings: Settings) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=OPEN_BOOKFLOW, web_app=WebAppInfo(url=settings.mini_app_url))],
            [
                KeyboardButton(
                    text=MY_APPOINTMENTS,
                    web_app=WebAppInfo(url=f"{settings.mini_app_url.rstrip('/')}/appointments"),
                )
            ],
            [KeyboardButton(text=HOW_IT_WORKS), KeyboardButton(text=CONTACT_SUPPORT)],
        ],
        resize_keyboard=True,
    )
