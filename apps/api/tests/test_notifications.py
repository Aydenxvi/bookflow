"""Notification-job enqueueing (app/services/notifications.py), exercised
through the real booking-service hooks (create_booking / transition_status /
cancel_booking / reschedule_booking) rather than by calling notifications.py
functions directly — the hooks' placement is exactly what's under test."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.enums import (
    BookingConfirmationMode,
    BookingStatus,
    NotificationJobStatus,
    NotificationJobType,
    RecipientType,
)
from app.models.notification import NotificationJob
from app.services.booking import (
    cancel_booking,
    create_booking,
    reschedule_booking,
    transition_status,
)
from tests.factories import (
    link_staff_service,
    make_all_week_schedule,
    make_business,
    make_membership,
    make_policy,
    make_service,
    make_settings,
    make_staff,
    make_telegram_identity,
    make_user,
)

pytestmark = pytest.mark.asyncio

OWNER_TG_ID = 111111
CUSTOMER_TG_ID = 222222


async def _setup(db, *, confirmation_mode=BookingConfirmationMode.AUTOMATIC, settings_overrides=None):
    business = await make_business(db)
    policy = await make_policy(db, business, min_lead_time_minutes=0, confirmation_mode=confirmation_mode)
    await make_settings(db, business, **(settings_overrides or {}))
    service = await make_service(db, business, duration_minutes=30)
    staff = await make_staff(db, business)
    await link_staff_service(db, staff, service)
    await make_all_week_schedule(db, business, None)
    await make_all_week_schedule(db, business, staff)

    owner = await make_user(db, first_name="Owner")
    await make_membership(db, business, owner)
    await make_telegram_identity(db, owner, telegram_user_id=OWNER_TG_ID)

    customer = await make_user(db, first_name="Customer")
    await make_telegram_identity(db, customer, telegram_user_id=CUSTOMER_TG_ID)

    await db.commit()
    return business, policy, service, staff, customer


async def _jobs_for_booking(db, booking_id):
    result = await db.execute(select(NotificationJob).where(NotificationJob.booking_id == booking_id))
    return list(result.scalars().all())


def _starts_at(days=3):
    return datetime.now(UTC).replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=days)


async def test_automatic_confirmation_notifies_customer_business_and_schedules_reminders(db):
    business, policy, service, staff, customer = await _setup(db)
    starts_at = _starts_at()

    booking = await create_booking(
        db, business=business, service=service, policy=policy, customer=customer, staff_id=staff.id,
        starts_at=starts_at, customer_notes=None, idempotency_key=None, is_demo=True,
    )

    jobs = await _jobs_for_booking(db, booking.id)
    reminder_jobs = [j for j in jobs if j.job_type == NotificationJobType.REMINDER]
    customer_jobs = [
        j for j in jobs if j.recipient_type == RecipientType.CUSTOMER and j.job_type != NotificationJobType.REMINDER
    ]
    business_jobs = [j for j in jobs if j.recipient_type == RecipientType.BUSINESS]

    assert len(customer_jobs) == 1
    assert customer_jobs[0].job_type == NotificationJobType.BOOKING_CONFIRMED
    assert customer_jobs[0].recipient_telegram_user_id == CUSTOMER_TG_ID

    assert len(business_jobs) == 1
    assert business_jobs[0].job_type == NotificationJobType.BUSINESS_NEW_BOOKING
    assert business_jobs[0].recipient_telegram_user_id == OWNER_TG_ID

    assert {j.payload["offset_minutes"] for j in reminder_jobs} == {1440, 120, 30}
    for j in reminder_jobs:
        assert j.scheduled_for == starts_at - timedelta(minutes=j.payload["offset_minutes"])
        assert j.status == NotificationJobStatus.PENDING


async def test_manual_confirmation_sends_received_not_confirmed_and_defers_reminders(db):
    business, policy, service, staff, customer = await _setup(
        db, confirmation_mode=BookingConfirmationMode.MANUAL
    )
    booking = await create_booking(
        db, business=business, service=service, policy=policy, customer=customer, staff_id=staff.id,
        starts_at=_starts_at(), customer_notes=None, idempotency_key=None, is_demo=True,
    )
    assert booking.status == BookingStatus.PENDING

    jobs = await _jobs_for_booking(db, booking.id)
    customer_jobs = [j for j in jobs if j.recipient_type == RecipientType.CUSTOMER]
    assert len(customer_jobs) == 1
    assert customer_jobs[0].job_type == NotificationJobType.BOOKING_RECEIVED
    assert not any(j.job_type == NotificationJobType.REMINDER for j in jobs)

    # Admin confirms it later - this is the one path to CONFIRMED that
    # doesn't go through create_booking.
    confirmed = await transition_status(
        db, booking, target=BookingStatus.CONFIRMED, actor_user_id=None,
    )
    jobs_after = await _jobs_for_booking(db, confirmed.id)
    confirmed_jobs = [j for j in jobs_after if j.job_type == NotificationJobType.BOOKING_CONFIRMED]
    reminder_jobs = [j for j in jobs_after if j.job_type == NotificationJobType.REMINDER]
    assert len(confirmed_jobs) == 1
    assert len(reminder_jobs) == 3


async def test_guest_customer_without_telegram_identity_gets_no_job_but_business_still_notified(db):
    business, policy, service, staff, _owner_customer = await _setup(db)
    guest = await make_user(db, first_name="Walk-in")
    await db.commit()

    booking = await create_booking(
        db, business=business, service=service, policy=policy, customer=guest, staff_id=staff.id,
        starts_at=_starts_at(), customer_notes=None, idempotency_key=None, is_demo=True,
    )

    jobs = await _jobs_for_booking(db, booking.id)
    assert not any(j.recipient_type == RecipientType.CUSTOMER for j in jobs)
    assert any(j.job_type == NotificationJobType.BUSINESS_NEW_BOOKING for j in jobs)


async def test_business_notification_respects_settings_flag(db):
    business, policy, service, staff, customer = await _setup(
        db, settings_overrides={"notify_business_on_new_booking": False}
    )
    booking = await create_booking(
        db, business=business, service=service, policy=policy, customer=customer, staff_id=staff.id,
        starts_at=_starts_at(), customer_notes=None, idempotency_key=None, is_demo=True,
    )
    jobs = await _jobs_for_booking(db, booking.id)
    assert not any(j.recipient_type == RecipientType.BUSINESS for j in jobs)
    assert any(j.recipient_type == RecipientType.CUSTOMER for j in jobs)


async def test_cancel_booking_notifies_and_cancels_pending_reminders(db):
    business, policy, service, staff, customer = await _setup(db)
    booking = await create_booking(
        db, business=business, service=service, policy=policy, customer=customer, staff_id=staff.id,
        starts_at=_starts_at(), customer_notes=None, idempotency_key=None, is_demo=True,
    )
    pre_cancel_reminders = [
        j for j in await _jobs_for_booking(db, booking.id) if j.job_type == NotificationJobType.REMINDER
    ]
    assert len(pre_cancel_reminders) == 3

    await cancel_booking(db, booking, policy, actor_user_id=customer.id, reason="change of plans")

    jobs = await _jobs_for_booking(db, booking.id)
    cancelled_customer_jobs = [
        j for j in jobs if j.job_type == NotificationJobType.BOOKING_CANCELLED and j.recipient_type == RecipientType.CUSTOMER
    ]
    cancelled_business_jobs = [j for j in jobs if j.job_type == NotificationJobType.BUSINESS_CANCELLATION]
    reminder_jobs = [j for j in jobs if j.job_type == NotificationJobType.REMINDER]

    assert len(cancelled_customer_jobs) == 1
    assert len(cancelled_business_jobs) == 1
    assert len(reminder_jobs) == 3
    assert all(j.status == NotificationJobStatus.CANCELLED for j in reminder_jobs)


async def test_reschedule_sends_one_combined_notification_and_moves_reminders(db):
    business, policy, service, staff, customer = await _setup(db)
    original_starts_at = _starts_at(days=3)
    booking = await create_booking(
        db, business=business, service=service, policy=policy, customer=customer, staff_id=staff.id,
        starts_at=original_starts_at, customer_notes=None, idempotency_key=None, is_demo=True,
    )

    new_starts_at = _starts_at(days=5)
    new_booking = await reschedule_booking(
        db, booking, business=business, service=service, policy=policy, customer=customer,
        new_starts_at=new_starts_at, new_staff_id=staff.id,
    )

    # Old booking: no generic cancelled notification, reminders cancelled.
    old_jobs = await _jobs_for_booking(db, booking.id)
    assert not any(j.job_type == NotificationJobType.BOOKING_CANCELLED for j in old_jobs)
    old_reminders = [j for j in old_jobs if j.job_type == NotificationJobType.REMINDER]
    assert len(old_reminders) == 3
    assert all(j.status == NotificationJobStatus.CANCELLED for j in old_reminders)

    # New booking: exactly one combined reschedule notification each side,
    # no generic "received"/"confirmed" customer job, fresh reminders.
    new_jobs = await _jobs_for_booking(db, new_booking.id)
    assert not any(
        j.job_type in (NotificationJobType.BOOKING_RECEIVED, NotificationJobType.BOOKING_CONFIRMED)
        for j in new_jobs
    )
    rescheduled_customer_jobs = [
        j for j in new_jobs
        if j.job_type == NotificationJobType.BOOKING_RESCHEDULED and j.recipient_type == RecipientType.CUSTOMER
    ]
    rescheduled_business_jobs = [j for j in new_jobs if j.job_type == NotificationJobType.BUSINESS_RESCHEDULE]
    new_reminders = [j for j in new_jobs if j.job_type == NotificationJobType.REMINDER]

    assert len(rescheduled_customer_jobs) == 1
    assert rescheduled_customer_jobs[0].payload["previous_starts_at"] == original_starts_at.isoformat()
    assert len(rescheduled_business_jobs) == 1
    assert len(new_reminders) == 3
    assert all(j.status == NotificationJobStatus.PENDING for j in new_reminders)
    assert {j.payload["offset_minutes"] for j in new_reminders} == {1440, 120, 30}


async def test_dedupe_key_prevents_double_insert_on_repeated_hook_call(db):
    business, policy, service, staff, customer = await _setup(db)
    booking = await create_booking(
        db, business=business, service=service, policy=policy, customer=customer, staff_id=staff.id,
        starts_at=_starts_at(), customer_notes=None, idempotency_key=None, is_demo=True,
    )
    from app.services import notifications

    await notifications.enqueue_booking_created(db, booking)
    await db.commit()

    jobs = await _jobs_for_booking(db, booking.id)
    confirmed_customer_jobs = [j for j in jobs if j.job_type == NotificationJobType.BOOKING_CONFIRMED]
    assert len(confirmed_customer_jobs) == 1
