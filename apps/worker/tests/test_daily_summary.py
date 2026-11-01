"""ensure_daily_summary_jobs: idempotent per-business-per-day enqueueing."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.daily_summary import ensure_daily_summary_jobs
from app.tables import JobType, notification_jobs
from tests.factories import (
    make_business,
    make_membership,
    make_settings,
    make_telegram_identity,
    make_user,
)

pytestmark = pytest.mark.asyncio


async def test_no_opted_in_businesses_inserts_nothing(engine):
    async with engine.begin() as conn:
        business_id = await make_business(conn)
        await make_settings(conn, business_id, notify_business_daily_summary=False)
        inserted = await ensure_daily_summary_jobs(conn)
    assert inserted == 0


async def test_opted_in_business_with_owner_gets_one_job(engine):
    async with engine.begin() as conn:
        business_id = await make_business(conn, timezone="UTC")
        await make_settings(conn, business_id, notify_business_daily_summary=True)
        owner_id = await make_user(conn)
        await make_membership(conn, business_id, owner_id, role="BUSINESS_OWNER")
        await make_telegram_identity(conn, owner_id, telegram_user_id=777)

        inserted = await ensure_daily_summary_jobs(conn)
        assert inserted == 1

        row = (
            await conn.execute(
                select(notification_jobs).where(notification_jobs.c.job_type == JobType.BUSINESS_DAILY_SUMMARY)
            )
        ).mappings().first()
    assert row["recipient_telegram_user_id"] == 777
    assert row["booking_id"] is None
    assert "date" in row["payload"]


async def test_second_call_is_idempotent(engine):
    async with engine.begin() as conn:
        business_id = await make_business(conn, timezone="UTC")
        await make_settings(conn, business_id, notify_business_daily_summary=True)
        owner_id = await make_user(conn)
        await make_membership(conn, business_id, owner_id, role="BUSINESS_OWNER")
        await make_telegram_identity(conn, owner_id, telegram_user_id=777)

        first = await ensure_daily_summary_jobs(conn)
        second = await ensure_daily_summary_jobs(conn)
    assert first == 1
    assert second == 0


async def test_blocked_telegram_identity_is_skipped(engine):
    async with engine.begin() as conn:
        business_id = await make_business(conn, timezone="UTC")
        await make_settings(conn, business_id, notify_business_daily_summary=True)
        owner_id = await make_user(conn)
        await make_membership(conn, business_id, owner_id, role="BUSINESS_OWNER")
        await make_telegram_identity(conn, owner_id, telegram_user_id=777, is_bot_blocked=True)

        inserted = await ensure_daily_summary_jobs(conn)
    assert inserted == 0


async def test_staff_role_is_not_a_business_recipient(engine):
    async with engine.begin() as conn:
        business_id = await make_business(conn, timezone="UTC")
        await make_settings(conn, business_id, notify_business_daily_summary=True)
        staff_user_id = await make_user(conn)
        await make_membership(conn, business_id, staff_user_id, role="STAFF")
        await make_telegram_identity(conn, staff_user_id, telegram_user_id=999)

        inserted = await ensure_daily_summary_jobs(conn)
    assert inserted == 0
