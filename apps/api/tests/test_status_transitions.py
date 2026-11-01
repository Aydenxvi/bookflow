"""Booking status transition rules, plus cancellation/reschedule policy windows."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.models.enums import BookingConfirmationMode, BookingStatus
from app.services.booking import (
    BookingPolicyError,
    InvalidTransitionError,
    cancel_booking,
    create_booking,
    reschedule_booking,
    transition_status,
)
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


async def _booked_fixture(db, **policy_overrides):
    business = await make_business(db)
    policy = await make_policy(db, business, min_lead_time_minutes=0, **policy_overrides)
    service = await make_service(db, business, duration_minutes=30)
    staff = await make_staff(db, business)
    await link_staff_service(db, staff, service)
    await make_all_week_schedule(db, business, None)
    await make_all_week_schedule(db, business, staff)
    customer = await make_user(db)
    await db.commit()

    starts_at = datetime.now(UTC).replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=3)
    booking = await create_booking(
        db, business=business, service=service, policy=policy, customer=customer, staff_id=staff.id,
        starts_at=starts_at, customer_notes=None, idempotency_key=None, is_demo=True,
    )
    return business, policy, service, staff, customer, booking


async def test_automatic_confirmation_mode_confirms_immediately(db):
    *_, booking = await _booked_fixture(db)
    assert booking.status == BookingStatus.CONFIRMED


async def test_manual_confirmation_mode_starts_pending(db):
    *_, booking = await _booked_fixture(db, confirmation_mode=BookingConfirmationMode.MANUAL)
    assert booking.status == BookingStatus.PENDING


async def test_valid_transition_pending_to_confirmed(db):
    *_, booking = await _booked_fixture(db)
    # Force it back to pending to test the transition explicitly.
    booking.status = BookingStatus.PENDING
    updated = await transition_status(db, booking, target=BookingStatus.CONFIRMED, actor_user_id=None)
    assert updated.status == BookingStatus.CONFIRMED


async def test_invalid_transition_completed_to_confirmed_rejected(db):
    *_, booking = await _booked_fixture(db)
    booking.status = BookingStatus.COMPLETED
    with pytest.raises(InvalidTransitionError):
        await transition_status(db, booking, target=BookingStatus.CONFIRMED, actor_user_id=None)


async def test_cancel_within_window_succeeds(db):
    _, policy, *_rest = await _booked_fixture(db, cancellation_window_minutes=60)
    booking = _rest[-1]
    cancelled = await cancel_booking(db, booking, policy, actor_user_id=None, reason="changed my mind")
    assert cancelled.status == BookingStatus.CANCELLED
    assert cancelled.cancel_reason == "changed my mind"


async def test_cancel_outside_window_rejected(db):
    # Booking starts in 3 days (see _booked_fixture); set an absurdly long
    # cancellation window so "now" is inside it and cancellation is rejected.
    _, policy, *_rest = await _booked_fixture(db, cancellation_window_minutes=999_999)
    booking = _rest[-1]
    with pytest.raises(BookingPolicyError):
        await cancel_booking(db, booking, policy, actor_user_id=None, reason="too late")


async def test_staff_override_bypasses_cancellation_window(db):
    _, policy, *_rest = await _booked_fixture(db, cancellation_window_minutes=999_999)
    booking = _rest[-1]
    cancelled = await cancel_booking(
        db, booking, policy, actor_user_id=None, reason="business cancelled", is_staff_override=True
    )
    assert cancelled.status == BookingStatus.CANCELLED


async def test_reschedule_creates_new_booking_and_cancels_old(db):
    business, policy, service, staff, customer, booking = await _booked_fixture(db)
    new_time = booking.starts_at + timedelta(hours=2)

    new_booking = await reschedule_booking(
        db, booking, business=business, service=service, policy=policy, customer=customer,
        new_starts_at=new_time, new_staff_id=staff.id,
    )

    assert new_booking.id != booking.id
    assert new_booking.starts_at == new_time
    assert new_booking.rescheduled_from_booking_id == booking.id

    await db.refresh(booking)
    assert booking.status == BookingStatus.CANCELLED
    assert booking.cancel_reason == "rescheduled"
