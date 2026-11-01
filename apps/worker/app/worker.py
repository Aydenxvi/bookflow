"""The poll loop: claim one job, render it, send it, mark the outcome,
repeat until nothing's left to claim, then sleep. Also keeps daily-summary
jobs flowing (see daily_summary.py) once per sleep cycle.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date as date_type

import httpx
from sqlalchemy.ext.asyncio import AsyncEngine

from app.claim import claim_next_job, mark_failed_or_retry, mark_sent
from app.config import Settings
from app.context import fetch_booking_context, fetch_daily_summary_context
from app.daily_summary import ensure_daily_summary_jobs
from app.messages import (
    render_business_message,
    render_customer_message,
    render_daily_summary_message,
)
from app.tables import JobType, RecipientType
from app.telegram_client import TelegramSendError, send_message

logger = logging.getLogger("bookflow.worker")


async def _render(conn, job: dict) -> str | None:
    """Returns the message text, or None if the job has no renderable
    context anymore (e.g. the booking was hard-deleted — shouldn't happen
    given ON DELETE CASCADE, but failing fast with a clear FAILED job beats
    crashing the whole worker on a bad row)."""
    if job["job_type"] == JobType.BUSINESS_DAILY_SUMMARY:
        summary_date = job["payload"]["date"]
        ctx = await fetch_daily_summary_context(conn, job["business_id"], date_type.fromisoformat(summary_date))
        return render_daily_summary_message(ctx, summary_date)

    ctx = await fetch_booking_context(conn, job["booking_id"])
    if ctx is None:
        return None
    if job["recipient_type"] == RecipientType.CUSTOMER:
        return render_customer_message(job["job_type"], job["payload"], ctx)
    return render_business_message(job["job_type"], job["payload"], ctx)


async def process_one(engine: AsyncEngine, settings: Settings, http_client: httpx.AsyncClient) -> bool:
    """Claims and fully resolves at most one job. Returns True if a job was
    claimed (whether it ultimately sent, retried, or failed), False if the
    queue was empty."""
    async with engine.begin() as conn:
        job = await claim_next_job(conn)
        if job is None:
            return False

        try:
            text = await _render(conn, job)
            if text is None:
                await mark_failed_or_retry(
                    conn, job["id"], error="booking/context no longer exists",
                    attempts_before=job["attempts"], max_attempts=settings.max_attempts,
                    base=settings.backoff_base_seconds, cap=settings.backoff_max_seconds,
                )
            elif not settings.telegram_bot_token:
                await mark_failed_or_retry(
                    conn, job["id"], error="TELEGRAM_BOT_TOKEN is not set",
                    attempts_before=job["attempts"], max_attempts=settings.max_attempts,
                    base=settings.backoff_base_seconds, cap=settings.backoff_max_seconds,
                )
            else:
                await send_message(
                    bot_token=settings.telegram_bot_token,
                    chat_id=job["recipient_telegram_user_id"],
                    text=text,
                    client=http_client,
                )
                await mark_sent(conn, job["id"])
        except TelegramSendError as exc:
            logger.warning("notification job %s failed to send: %s", job["id"], exc)
            await mark_failed_or_retry(
                conn, job["id"], error=str(exc), attempts_before=job["attempts"],
                max_attempts=settings.max_attempts, base=settings.backoff_base_seconds,
                cap=settings.backoff_max_seconds,
            )
        return True


async def run(engine: AsyncEngine, settings: Settings, *, iterations: int | None = None) -> None:
    """Runs the poll loop. `iterations=None` runs forever (production);
    tests pass a small integer to run a bounded number of poll cycles."""
    done = 0
    async with httpx.AsyncClient(timeout=10.0) as http_client:
        while iterations is None or done < iterations:
            async with engine.begin() as conn:
                await ensure_daily_summary_jobs(conn)

            claimed_any = True
            while claimed_any:
                claimed_any = await process_one(engine, settings, http_client)

            done += 1
            if iterations is None or done < iterations:
                await asyncio.sleep(settings.poll_interval_seconds)
