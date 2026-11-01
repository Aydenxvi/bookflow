"""The actual race-condition test the spec calls for: two concurrent
booking-creation attempts for the exact same staff member and time slot,
from two independent DB sessions/connections (simulating two different API
requests arriving at nearly the same instant). Exactly one must win."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from app.services.booking import BookingConflictError, create_booking
from tests.factories import (
    link_staff_service,
    make_all_week_schedule,
    make_business,
    make_policy,
    make_service,
    make_staff,
    make_user,
)

pytestmark = pytest.mark.asyncio


async def test_concurrent_booking_attempts_only_one_succeeds(db, db_factory):
    # Set up fixtures on the primary session, then commit so other
    # connections can see this data.
    business = await make_business(db)
    policy = await make_policy(db, business, min_lead_time_minutes=0)
    service = await make_service(db, business, duration_minutes=30)
    staff = await make_staff(db, business)
    await link_staff_service(db, staff, service)
    await make_all_week_schedule(db, business, None)
    await make_all_week_schedule(db, business, staff)
    customer_a = await make_user(db, first_name="CustomerA")
    customer_b = await make_user(db, first_name="CustomerB")
    await db.commit()

    starts_at = datetime.now(UTC).replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)

    session_a = db_factory()
    session_b = db_factory()

    async def attempt(session, customer):
        # Re-fetch within each session so each has its own identity map / connection.
        biz = await session.get(type(business), business.id)
        svc = await session.get(type(service), service.id)
        pol = await session.get(type(policy), policy.id)
        cust = await session.get(type(customer), customer.id)
        return await create_booking(
            session, business=biz, service=svc, policy=pol, customer=cust, staff_id=staff.id,
            starts_at=starts_at, customer_notes=None, idempotency_key=None, is_demo=True,
        )

    try:
        results = await asyncio.gather(
            attempt(session_a, customer_a), attempt(session_b, customer_b), return_exceptions=True
        )
    finally:
        await session_a.close()
        await session_b.close()

    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]

    assert len(successes) == 1, f"expected exactly one booking to succeed, got {len(successes)}: {results}"
    assert len(failures) == 1
    assert isinstance(failures[0], BookingConflictError)
