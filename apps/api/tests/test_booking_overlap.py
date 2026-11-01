"""Overlap prevention at both layers: the database EXCLUDE constraint
directly, and the booking service that sits in front of it."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.booking import Booking
from app.models.enums import BookingStatus
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


async def test_database_rejects_overlapping_insert_directly(db):
    """Bypasses all application logic — inserts two overlapping bookings for
    the same staff member via raw ORM adds — and asserts the database
    constraint itself rejects the second one."""
    business = await make_business(db)
    service = await make_service(db, business, duration_minutes=30)
    staff = await make_staff(db, business)
    customer = await make_user(db)
    await db.commit()

    start = datetime.now(UTC) + timedelta(days=1)
    b1 = Booking(
        business_id=business.id, staff_id=staff.id, service_id=service.id, customer_user_id=customer.id,
        starts_at=start, ends_at=start + timedelta(minutes=30), status=BookingStatus.CONFIRMED,
        price_minor_units_snapshot=1000, currency_snapshot="USD", duration_minutes_snapshot=30, is_demo=True,
    )
    db.add(b1)
    await db.commit()

    overlapping_start = start + timedelta(minutes=15)
    b2 = Booking(
        business_id=business.id, staff_id=staff.id, service_id=service.id, customer_user_id=customer.id,
        starts_at=overlapping_start, ends_at=overlapping_start + timedelta(minutes=30),
        status=BookingStatus.CONFIRMED,
        price_minor_units_snapshot=1000, currency_snapshot="USD", duration_minutes_snapshot=30, is_demo=True,
    )
    db.add(b2)
    with pytest.raises(IntegrityError):
        await db.commit()


async def test_cancelled_booking_does_not_block_the_slot(db):
    business = await make_business(db)
    service = await make_service(db, business, duration_minutes=30)
    staff = await make_staff(db, business)
    customer = await make_user(db)
    await db.commit()

    start = datetime.now(UTC) + timedelta(days=1)
    cancelled = Booking(
        business_id=business.id, staff_id=staff.id, service_id=service.id, customer_user_id=customer.id,
        starts_at=start, ends_at=start + timedelta(minutes=30), status=BookingStatus.CANCELLED,
        price_minor_units_snapshot=1000, currency_snapshot="USD", duration_minutes_snapshot=30, is_demo=True,
    )
    db.add(cancelled)
    await db.commit()

    # Same exact time, new booking — must succeed because the first is cancelled.
    new = Booking(
        business_id=business.id, staff_id=staff.id, service_id=service.id, customer_user_id=customer.id,
        starts_at=start, ends_at=start + timedelta(minutes=30), status=BookingStatus.CONFIRMED,
        price_minor_units_snapshot=1000, currency_snapshot="USD", duration_minutes_snapshot=30, is_demo=True,
    )
    db.add(new)
    await db.commit()  # should not raise


async def test_booking_service_rejects_overlap_for_explicit_staff(db):
    business = await make_business(db)
    policy = await make_policy(db, business, min_lead_time_minutes=0)
    service = await make_service(db, business, duration_minutes=30)
    staff = await make_staff(db, business)
    await link_staff_service(db, staff, service)
    await make_all_week_schedule(db, business, None)
    await make_all_week_schedule(db, business, staff)
    customer1 = await make_user(db, first_name="Customer1")
    customer2 = await make_user(db, first_name="Customer2")
    await db.commit()

    starts_at = datetime.now(UTC).replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)

    await create_booking(
        db, business=business, service=service, policy=policy, customer=customer1, staff_id=staff.id,
        starts_at=starts_at, customer_notes=None, idempotency_key=None, is_demo=True,
    )

    with pytest.raises(BookingConflictError):
        await create_booking(
            db, business=business, service=service, policy=policy, customer=customer2, staff_id=staff.id,
            starts_at=starts_at, customer_notes=None, idempotency_key=None, is_demo=True,
        )


async def test_idempotency_key_returns_same_booking(db):
    business = await make_business(db)
    policy = await make_policy(db, business, min_lead_time_minutes=0)
    service = await make_service(db, business, duration_minutes=30)
    staff = await make_staff(db, business)
    await link_staff_service(db, staff, service)
    await make_all_week_schedule(db, business, None)
    await make_all_week_schedule(db, business, staff)
    customer = await make_user(db)
    await db.commit()

    starts_at = datetime.now(UTC).replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)

    b1 = await create_booking(
        db, business=business, service=service, policy=policy, customer=customer, staff_id=staff.id,
        starts_at=starts_at, customer_notes=None, idempotency_key="abc-123", is_demo=True,
    )
    b2 = await create_booking(
        db, business=business, service=service, policy=policy, customer=customer, staff_id=staff.id,
        starts_at=starts_at, customer_notes=None, idempotency_key="abc-123", is_demo=True,
    )
    assert b1.id == b2.id
