"""Polling entrypoint for local dev.

NOTE (session 1, 2026-11-01): no Telegram bot token was available in this
environment (see repo root CLAUDE.md / PROGRESS.md), so this has been
written and read through carefully against aiogram 3.x's documented API,
but has NEVER been run against Telegram's servers. `python -m app.main`
will fail fast and loudly if BOT_TOKEN is unset, rather than pretending to
start — see the check below.
"""
from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import get_settings
from app.handlers import router


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()

    if not settings.bot_token:
        print(
            "BOT_TOKEN is not set (see apps/bot/.env.example). "
            "This bot has not been run against real Telegram servers in this "
            "environment — get a token from @BotFather first (see README.md).",
            file=sys.stderr,
        )
        sys.exit(1)

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, settings=settings)


if __name__ == "__main__":
    asyncio.run(main())
