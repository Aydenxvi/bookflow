"""Claiming and resolving NotificationJob rows, against real PostgreSQL —
FOR UPDATE SKIP LOCKED behavior specifically needs a real database, not a
mock."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.claim import claim_next_job, mark_failed_or_retry, mark_sent
from app.tables import JobStatus, JobType, RecipientType, notification_jobs
from tests.factories import make_business, make_notification_job

pytestmark = pytest.mark.asyncio


async def _due_job(conn, business_id, **overrides):
    kwargs = dict(
        business_id=business_id,
        booking_id=None,
        job_type=JobType.BUSINESS_DAILY_SUMMARY,
        recipient_type=RecipientType.BUSINESS,
        recipient_telegram_user_id=12345,
        dedupe_key=f"test:{uuid.uuid4()}",
        scheduled_for=datetime.now(UTC) - timedelta(minutes=1),
    )
    kwargs.update(overrides)
    return await make_notification_job(conn, **kwargs)


async def test_claim_returns_none_when_queue_empty(engine):
    async with engine.begin() as conn:
        job = await claim_next_job(conn)
    assert job is None


async def test_claim_returns_a_due_pending_job(engine):
    async with engine.begin() as conn:
        business_id = await make_business(conn)
        job_id = await _due_job(conn, business_id)

    async with engine.begin() as conn:
        job = await claim_next_job(conn)
    assert job is not None
    assert job["id"] == job_id


async def test_claim_skips_future_scheduled_jobs(engine):
    async with engine.begin() as conn:
        business_id = await make_business(conn)
        await _due_job(conn, business_id, scheduled_for=datetime.now(UTC) + timedelta(hours=1))

    async with engine.begin() as conn:
        job = await claim_next_job(conn)
    assert job is None


async def test_claim_skips_non_pending_jobs(engine):
    async with engine.begin() as conn:
        business_id = await make_business(conn)
        await _due_job(conn, business_id, status=JobStatus.CANCELLED)

    async with engine.begin() as conn:
        job = await claim_next_job(conn)
    assert job is None


async def test_claim_does_not_double_claim_across_concurrent_transactions(engine):
    async with engine.begin() as conn:
        business_id = await make_business(conn)
        job_a = await _due_job(conn, business_id)
        job_b = await _due_job(conn, business_id)

    conn1 = await engine.connect()
    conn2 = await engine.connect()
    try:
        trans1 = await conn1.begin()
        trans2 = await conn2.begin()

        claimed1 = await claim_next_job(conn1)
        claimed2 = await claim_next_job(conn2)

        assert claimed1 is not None
        assert claimed2 is not None
        assert claimed1["id"] != claimed2["id"]
        assert {claimed1["id"], claimed2["id"]} == {job_a, job_b}

        await trans1.commit()
        await trans2.commit()
    finally:
        await conn1.close()
        await conn2.close()


async def test_mark_sent_sets_status_and_sent_at(engine):
    async with engine.begin() as conn:
        business_id = await make_business(conn)
        job_id = await _due_job(conn, business_id)
        await mark_sent(conn, job_id)

    async with engine.begin() as conn:
        row = (
            await conn.execute(select(notification_jobs).where(notification_jobs.c.id == job_id))
        ).mappings().first()
    assert row["status"] == JobStatus.SENT
    assert row["sent_at"] is not None
    assert row["attempts"] == 1


async def test_mark_failed_or_retry_stays_pending_with_backoff_before_max_attempts(engine):
    async with engine.begin() as conn:
        business_id = await make_business(conn)
        job_id = await _due_job(conn, business_id)
        await mark_failed_or_retry(
            conn, job_id, error="boom", attempts_before=0, max_attempts=5, base=30, cap=3600
        )

    async with engine.begin() as conn:
        row = (
            await conn.execute(select(notification_jobs).where(notification_jobs.c.id == job_id))
        ).mappings().first()
    assert row["status"] == JobStatus.PENDING
    assert row["attempts"] == 1
    assert row["last_error"] == "boom"
    assert row["scheduled_for"] > datetime.now(UTC)


async def test_mark_failed_or_retry_becomes_failed_at_max_attempts(engine):
    async with engine.begin() as conn:
        business_id = await make_business(conn)
        job_id = await _due_job(conn, business_id)
        await mark_failed_or_retry(
            conn, job_id, error="still broken", attempts_before=4, max_attempts=5, base=30, cap=3600
        )

    async with engine.begin() as conn:
        row = (
            await conn.execute(select(notification_jobs).where(notification_jobs.c.id == job_id))
        ).mappings().first()
    assert row["status"] == JobStatus.FAILED
    assert row["attempts"] == 5
