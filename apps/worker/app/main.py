"""Entrypoint: `python -m app.main` runs the poll loop forever.

NOTE (session continuing Phase 4, 2026-11-02): no Telegram bot token was
available in this environment (same constraint as apps/bot — see repo root
CLAUDE.md/PROGRESS.md), so actual delivery to Telegram's servers has never
been exercised. Everything up to the network call (claiming jobs with
SELECT ... FOR UPDATE SKIP LOCKED, rendering messages from live booking
data, retry/backoff bookkeeping, daily-summary scheduling, idempotency) is
real and covered by tests/ against a real Postgres database — see
PROGRESS.md for exactly what was run. Without BOT_TOKEN set, this process
still runs the full loop; every send attempt fails fast with a clear
"TELEGRAM_BOT_TOKEN is not set" error and goes through the normal
retry/backoff path rather than crashing, so the rest of the system (and the
demo data) stays exercisable without a real bot.
"""
from __future__ import annotations

import asyncio
import logging

from app.config import get_settings
from app.db import make_engine
from app.worker import run


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    if not settings.telegram_bot_token:
        logging.getLogger("bookflow.worker").warning(
            "TELEGRAM_BOT_TOKEN is not set - jobs will be claimed and retried/failed "
            "but nothing will actually be sent. See apps/worker/README.md."
        )
    engine = make_engine()
    try:
        await run(engine, settings)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
