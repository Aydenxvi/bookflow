"""Turns booking-lifecycle events into persistent NotificationJob rows.

This module only ever INSERTS (or cancels) NotificationJob rows, in the same
session/transaction as the booking change that caused them — see CLAUDE.md:
"NotificationJob rows in Postgres, picked up by apps/worker ... No in-memory
scheduler." It never talks to Telegram itself; apps/worker does that by
polling for PENDING jobs whose scheduled_for <= now().

Design decisions, recorded here because they aren't obvious from the call
sites in services/booking.py:

- A customer recipient is resolved via a direct TelegramIdentity lookup by
  user_id, not by touching `User.telegram_identity` as a lazy relationship
  (under async SQLAlchemy that would need an explicit eager-load everywhere
  the User object is touched; a direct query is simpler and matches this
  file's only job). Demo/guest users (browser demo mode, admin walk-in manual
  bookings via admin_bookings.py::create_manual_booking) have no
  TelegramIdentity row — no job is created for them. That's correct, not a
  gap: there is no Telegram chat to send to.
- A business recipient is every BUSINESS_OWNER/BUSINESS_MANAGER member of the
  business who has a non-blocked TelegramIdentity. One job per such member.
  An owner who only ever used browser demo mode has no Telegram identity and
  is silently skipped, same reasoning as above.
- Business-facing notifications additionally respect BusinessSettings'
  notify_business_on_new_booking / notify_business_on_cancellation flags.
  (notify_business_daily_summary is Phase 4's BUSINESS_DAILY_SUMMARY job type,
  enqueued periodically by apps/worker itself, not from here.)
- Reminders are just rows with a future scheduled_for, one per offset in
  BookingPolicy.reminder_offsets_minutes (default [1440, 120, 30] minutes —
  the "24h/2h/30m, configurable" from ROADMAP.md). They're scheduled once a
  booking is actually CONFIRMED (at creation, or later via admin manual
  confirmation) and cancelled — NotificationJobStatus.CANCELLED, not deleted,
  so there's an audit trail — if the booking is later cancelled or
  superseded by a reschedule. No in-memory scheduler: apps/worker's ordinary
  poll picks a reminder up naturally once its scheduled_for arrives. A
  reminder whose scheduled_for would already be in the past (e.g. a very
  short-lead-time manual booking) is skipped rather than enqueued to fire
  immediately — a "reminder" after the fact isn't one.
- Reschedule is the one case worth spelling out: services/booking.py
  ::reschedule_booking creates the replacement booking with
  suppress_notifications=True (so the customer doesn't get a generic "new
  booking" message) and cancels the original via transition_status(...,
  suppress_notifications=True) (so the customer doesn't also get a generic
  "cancelled" message) — then calls enqueue_rescheduled() here exactly once,
  which sends the one message that actually describes what happened and
  schedules reminders for the new time.
- dedupe_key (unique at the DB level per NotificationJob's own docstring) is
  checked defensively before every insert in this file, so a hook that ever
  ran twice for the same event could not double-insert. Call sites in this
  codebase don't currently retry these hooks, so this is a belt-and-suspenders
  guarantee, not something routinely exercised — but it means a bug in this
  file fails safe (duplicate job silently skipped) instead of raising
  IntegrityError and rolling back the booking change that triggered it.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.business import BusinessMembership, BusinessSettings
from app.models.enums import (
    BookingStatus,
    MembershipRole,
    NotificationJobStatus,
    NotificationJobType,
    RecipientType,
)
from app.models.notification import NotificationJob
from app.models.policy import BookingPolicy
from app.models.user import TelegramIdentity

_BUSINESS_FACING_ROLES = (MembershipRole.BUSINESS_OWNER, MembershipRole.BUSINESS_MANAGER)


async def _get_or_create_settings(db: AsyncSession, business_id: uuid.UUID) -> BusinessSettings:
    result = await db.execute(select(BusinessSettings).where(BusinessSettings.business_id == business_id))
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = BusinessSettings(business_id=business_id)
        db.add(settings)
        await db.flush()
    return settings


async def _get_policy(db: AsyncSession, business_id: uuid.UUID) -> BookingPolicy | None:
    result = await db.execute(select(BookingPolicy).where(BookingPolicy.business_id == business_id))
    return result.scalar_one_or_none()


async def _customer_telegram_id(db: AsyncSession, user_id: uuid.UUID) -> int | None:
    result = await db.execute(
        select(TelegramIdentity.telegram_user_id).where(
            TelegramIdentity.user_id == user_id, TelegramIdentity.is_bot_blocked.is_(False)
        )
    )
    return result.scalar_one_or_none()


async def _business_recipient_telegram_ids(db: AsyncSession, business_id: uuid.UUID) -> list[int]:
    result = await db.execute(
        select(TelegramIdentity.telegram_user_id)
        .join(BusinessMembership, BusinessMembership.user_id == TelegramIdentity.user_id)
        .where(
            BusinessMembership.business_id == business_id,
            BusinessMembership.role.in_(_BUSINESS_FACING_ROLES),
            TelegramIdentity.is_bot_blocked.is_(False),
        )
    )
    return [row[0] for row in result.all()]


async def _enqueue(
    db: AsyncSession,
    *,
    business_id: uuid.UUID,
    booking_id: uuid.UUID | None,
    job_type: NotificationJobType,
    recipient_type: RecipientType,
    recipient_telegram_user_id: int,
    dedupe_key: str,
    payload: dict | None = None,
    scheduled_for: datetime | None = None,
) -> None:
    existing = await db.execute(select(NotificationJob.id).where(NotificationJob.dedupe_key == dedupe_key))
    if existing.scalar_one_or_none() is not None:
        return
    db.add(
        NotificationJob(
            business_id=business_id,
            booking_id=booking_id,
            job_type=job_type,
            recipient_type=recipient_type,
            recipient_telegram_user_id=recipient_telegram_user_id,
            payload=payload or {},
            scheduled_for=scheduled_for or datetime.now(UTC),
            dedupe_key=dedupe_key,
        )
    )


async def _schedule_reminders(db: AsyncSession, booking: Booking) -> None:
    policy = await _get_policy(db, booking.business_id)
    if policy is None:
        return
    telegram_id = await _customer_telegram_id(db, booking.customer_user_id)
    if telegram_id is None:
        return
    now = datetime.now(UTC)
    for offset in policy.reminder_offsets_minutes:
        scheduled_for = booking.starts_at - timedelta(minutes=offset)
        if scheduled_for <= now:
            continue
        await _enqueue(
            db,
            business_id=booking.business_id,
            booking_id=booking.id,
            job_type=NotificationJobType.REMINDER,
            recipient_type=RecipientType.CUSTOMER,
            recipient_telegram_user_id=telegram_id,
            dedupe_key=f"reminder_{offset}:{booking.id}",
            payload={"offset_minutes": offset},
            scheduled_for=scheduled_for,
        )


async def enqueue_booking_created(db: AsyncSession, booking: Booking) -> None:
    """Call from services/booking.py::create_booking right after the booking
    row and its initial BookingStatusHistory have been added, before commit.
    """
    customer_job_type = (
        NotificationJobType.BOOKING_CONFIRMED
        if booking.status == BookingStatus.CONFIRMED
        else NotificationJobType.BOOKING_RECEIVED
    )
    telegram_id = await _customer_telegram_id(db, booking.customer_user_id)
    if telegram_id is not None:
        await _enqueue(
            db,
            business_id=booking.business_id,
            booking_id=booking.id,
            job_type=customer_job_type,
            recipient_type=RecipientType.CUSTOMER,
            recipient_telegram_user_id=telegram_id,
            dedupe_key=f"{customer_job_type.value}:{booking.id}:customer",
        )

    settings = await _get_or_create_settings(db, booking.business_id)
    if settings.notify_business_on_new_booking:
        for tg_id in await _business_recipient_telegram_ids(db, booking.business_id):
            await _enqueue(
                db,
                business_id=booking.business_id,
                booking_id=booking.id,
                job_type=NotificationJobType.BUSINESS_NEW_BOOKING,
                recipient_type=RecipientType.BUSINESS,
                recipient_telegram_user_id=tg_id,
                dedupe_key=f"business_new_booking:{booking.id}:{tg_id}",
            )

    if booking.status == BookingStatus.CONFIRMED:
        await _schedule_reminders(db, booking)


async def enqueue_confirmed(db: AsyncSession, booking: Booking) -> None:
    """Call from transition_status when an existing PENDING booking moves to
    CONFIRMED — the only path to CONFIRMED that doesn't go through
    create_booking (a manual-confirmation-mode business, admin confirms a
    pending booking). Schedules reminders for the first time, since a PENDING
    booking never had any.
    """
    telegram_id = await _customer_telegram_id(db, booking.customer_user_id)
    if telegram_id is not None:
        await _enqueue(
            db,
            business_id=booking.business_id,
            booking_id=booking.id,
            job_type=NotificationJobType.BOOKING_CONFIRMED,
            recipient_type=RecipientType.CUSTOMER,
            recipient_telegram_user_id=telegram_id,
            dedupe_key=f"booking_confirmed:{booking.id}:customer_manual",
        )
    await _schedule_reminders(db, booking)


async def cancel_pending_reminders(db: AsyncSession, booking_id: uuid.UUID) -> None:
    """Mark any still-PENDING REMINDER jobs for this booking as CANCELLED so
    apps/worker's ordinary poll never sends a reminder for an appointment
    that no longer holds at that time (cancelled, or superseded by reschedule).
    """
    result = await db.execute(
        select(NotificationJob).where(
            NotificationJob.booking_id == booking_id,
            NotificationJob.job_type == NotificationJobType.REMINDER,
            NotificationJob.status == NotificationJobStatus.PENDING,
        )
    )
    for job in result.scalars().all():
        job.status = NotificationJobStatus.CANCELLED


async def enqueue_cancelled(db: AsyncSession, booking: Booking) -> None:
    """Call from transition_status when a booking moves to CANCELLED for its
    own sake (not as part of a reschedule — see enqueue_rescheduled)."""
    telegram_id = await _customer_telegram_id(db, booking.customer_user_id)
    if telegram_id is not None:
        await _enqueue(
            db,
            business_id=booking.business_id,
            booking_id=booking.id,
            job_type=NotificationJobType.BOOKING_CANCELLED,
            recipient_type=RecipientType.CUSTOMER,
            recipient_telegram_user_id=telegram_id,
            dedupe_key=f"booking_cancelled:{booking.id}:customer",
        )

    settings = await _get_or_create_settings(db, booking.business_id)
    if settings.notify_business_on_cancellation:
        for tg_id in await _business_recipient_telegram_ids(db, booking.business_id):
            await _enqueue(
                db,
                business_id=booking.business_id,
                booking_id=booking.id,
                job_type=NotificationJobType.BUSINESS_CANCELLATION,
                recipient_type=RecipientType.BUSINESS,
                recipient_telegram_user_id=tg_id,
                dedupe_key=f"business_cancellation:{booking.id}:{tg_id}",
            )

    await cancel_pending_reminders(db, booking.id)


async def enqueue_rescheduled(db: AsyncSession, *, old_booking: Booking, new_booking: Booking) -> None:
    """Call once from reschedule_booking, after the new booking exists and the
    old one has been cancelled with suppress_notifications=True. Sends the one
    message that actually describes what happened (instead of a separate
    "cancelled" + "new booking" pair) and schedules reminders for the new
    time.
    """
    telegram_id = await _customer_telegram_id(db, new_booking.customer_user_id)
    if telegram_id is not None:
        await _enqueue(
            db,
            business_id=new_booking.business_id,
            booking_id=new_booking.id,
            job_type=NotificationJobType.BOOKING_RESCHEDULED,
            recipient_type=RecipientType.CUSTOMER,
            recipient_telegram_user_id=telegram_id,
            dedupe_key=f"booking_rescheduled:{new_booking.id}:customer",
            payload={"previous_starts_at": old_booking.starts_at.isoformat()},
        )

    settings = await _get_or_create_settings(db, new_booking.business_id)
    if settings.notify_business_on_new_booking:
        for tg_id in await _business_recipient_telegram_ids(db, new_booking.business_id):
            await _enqueue(
                db,
                business_id=new_booking.business_id,
                booking_id=new_booking.id,
                job_type=NotificationJobType.BUSINESS_RESCHEDULE,
                recipient_type=RecipientType.BUSINESS,
                recipient_telegram_user_id=tg_id,
                dedupe_key=f"business_reschedule:{new_booking.id}:{tg_id}",
                payload={"previous_starts_at": old_booking.starts_at.isoformat()},
            )

    if new_booking.status == BookingStatus.CONFIRMED:
        await _schedule_reminders(db, new_booking)
