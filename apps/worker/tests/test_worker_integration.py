"""End-to-end process_one(): claim -> render -> send -> mark, against real
PostgreSQL with the Telegram HTTP call mocked (no real bot token exists in
this environment - see README.md)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import httpx
import pytest
from sqlalchemy import select

from app.config import Settings
from app.tables import JobType, RecipientType, notification_jobs
from app.telegram_client import TelegramSendError
from app.worker import process_one
from tests.factories import (
    make_booking,
    make_business,
    make_notification_job,
    make_service,
    make_staff,
    make_user,
)

pytestmark = pytest.mark.asyncio


def _settings(**overrides) -> Settings:
    defaults = dict(telegram_bot_token="fake-token-for-tests", max_attempts=3, backoff_base_seconds=30, backoff_max_seconds=3600)
    defaults.update(overrides)
    return Settings(**defaults)


async def _booking_fixture(conn):
    business_id = await make_business(conn, name="ATELIER", timezone="UTC")
    service_id = await make_service(conn, business_id, name="Haircut")
    staff_id = await make_staff(conn, display_name="Jamie")
    customer_id = await make_user(conn, first_name="Alex")
    starts_at = datetime.now(UTC).replace(microsecond=0) + timedelta(days=2)
    booking_id = await make_booking(
        conn, business_id=business_id, staff_id=staff_id, service_id=service_id,
        customer_user_id=customer_id, starts_at=starts_at, ends_at=starts_at + timedelta(minutes=30),
    )
    return business_id, booking_id


async def test_process_one_returns_false_when_queue_empty(engine):
    async with httpx.AsyncClient() as client:
        claimed = await process_one(engine, _settings(), client)
    assert claimed is False


async def test_process_one_sends_and_marks_sent_on_success(engine, monkeypatch):
    async with engine.begin() as conn:
        business_id, booking_id = await _booking_fixture(conn)
        job_id = await make_notification_job(
            conn, business_id=business_id, booking_id=booking_id, job_type=JobType.BOOKING_CONFIRMED,
            recipient_type=RecipientType.CUSTOMER, recipient_telegram_user_id=4242,
            dedupe_key=f"test:{uuid.uuid4()}", scheduled_for=datetime.now(UTC) - timedelta(seconds=1),
        )

    send_mock = AsyncMock(return_value=None)
    monkeypatch.setattr("app.worker.send_message", send_mock)

    async with httpx.AsyncClient() as client:
        claimed = await process_one(engine, _settings(), client)
    assert claimed is True
    send_mock.assert_awaited_once()
    assert send_mock.await_args.kwargs["chat_id"] == 4242
    assert "Haircut" in send_mock.await_args.kwargs["text"]

    async with engine.begin() as conn:
        row = (
            await conn.execute(select(notification_jobs).where(notification_jobs.c.id == job_id))
        ).mappings().first()
    assert row["status"] == "SENT"
    assert row["sent_at"] is not None


async def test_process_one_retries_on_send_failure(engine, monkeypatch):
    async with engine.begin() as conn:
        business_id, booking_id = await _booking_fixture(conn)
        job_id = await make_notification_job(
            conn, business_id=business_id, booking_id=booking_id, job_type=JobType.BOOKING_CANCELLED,
            recipient_type=RecipientType.CUSTOMER, recipient_telegram_user_id=4242,
            dedupe_key=f"test:{uuid.uuid4()}", scheduled_for=datetime.now(UTC) - timedelta(seconds=1),
        )

    send_mock = AsyncMock(side_effect=TelegramSendError("Telegram API error (403): bot was blocked by the user"))
    monkeypatch.setattr("app.worker.send_message", send_mock)

    async with httpx.AsyncClient() as client:
        claimed = await process_one(engine, _settings(max_attempts=3), client)
    assert claimed is True

    async with engine.begin() as conn:
        row = (
            await conn.execute(select(notification_jobs).where(notification_jobs.c.id == job_id))
        ).mappings().first()
    assert row["status"] == "PENDING"
    assert row["attempts"] == 1
    assert "blocked" in row["last_error"]
    assert row["scheduled_for"] > datetime.now(UTC)


async def test_process_one_without_bot_token_does_not_call_telegram(engine, monkeypatch):
    async with engine.begin() as conn:
        business_id, booking_id = await _booking_fixture(conn)
        job_id = await make_notification_job(
            conn, business_id=business_id, booking_id=booking_id, job_type=JobType.BOOKING_CONFIRMED,
            recipient_type=RecipientType.CUSTOMER, recipient_telegram_user_id=4242,
            dedupe_key=f"test:{uuid.uuid4()}", scheduled_for=datetime.now(UTC) - timedelta(seconds=1),
        )

    send_mock = AsyncMock()
    monkeypatch.setattr("app.worker.send_message", send_mock)

    async with httpx.AsyncClient() as client:
        claimed = await process_one(engine, _settings(telegram_bot_token=""), client)
    assert claimed is True
    send_mock.assert_not_awaited()

    async with engine.begin() as conn:
        row = (
            await conn.execute(select(notification_jobs).where(notification_jobs.c.id == job_id))
        ).mappings().first()
    assert row["status"] == "PENDING"
    assert "TELEGRAM_BOT_TOKEN" in row["last_error"]


async def test_process_one_handles_missing_booking_context_without_crashing(engine):
    async with engine.begin() as conn:
        business_id = await make_business(conn)
        job_id = await make_notification_job(
            conn, business_id=business_id, booking_id=uuid.uuid4(), job_type=JobType.BOOKING_CONFIRMED,
            recipient_type=RecipientType.CUSTOMER, recipient_telegram_user_id=4242,
            dedupe_key=f"test:{uuid.uuid4()}", scheduled_for=datetime.now(UTC) - timedelta(seconds=1),
        )

    async with httpx.AsyncClient() as client:
        claimed = await process_one(engine, _settings(), client)
    assert claimed is True

    async with engine.begin() as conn:
        row = (
            await conn.execute(select(notification_jobs).where(notification_jobs.c.id == job_id))
        ).mappings().first()
    assert row["status"] == "PENDING"
    assert "no longer exists" in row["last_error"]
