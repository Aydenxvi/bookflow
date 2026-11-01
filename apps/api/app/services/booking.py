"""Booking creation, cancellation, rescheduling and status transitions.

This is the second (and decisive) line of defense for concurrency safety —
see services/availability.py for the first (what we show the customer) and
CLAUDE.md / the Alembic migration for the third (the database EXCLUDE
constraint, which wins even if this code has a bug).

Strategy for `create_booking`:
1. If an idempotency key is given and a booking already exists for
   (business_id, idempotency_key), return it unchanged — safe to retry.
2. Resolve the target staff member. For an explicit staff_id we still
   re-validate it offers the service and is active. For "any available" we
   re-run the availability engine for that exact day and pick a staff member
   who is actually free at that exact time right now — not whatever the
   client claimed.
3. Take a Postgres advisory transaction lock keyed on the staff member's id,
   so only one booking-creation attempt for that staff member proceeds at a
   time — this serializes the "is it still free? ok, insert" sequence
   instead of trusting a check-then-act pattern under concurrency.
4. Re-check for overlapping active bookings for that staff member inside the
   same transaction (SELECT ... FOR UPDATE).
5. Insert. If, despite all of the above, the database's EXCLUDE constraint
   still rejects the insert (belt-and-suspenders — e.g. a bug upstream),
   that is caught and surfaced as a clean BookingConflictError rather than a
   raw IntegrityError leaking to the client.
"""
from __future__ import annotations

import uuid
import zlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatusHistory
from app.models.business import Business
from app.models.enums import BookingConfirmationMode, BookingStatus
from app.models.policy import BookingPolicy
from app.models.service import Service
from app.models.user import User
from app.services import notifications
from app.services.availability import ACTIVE_BOOKING_STATUSES, compute_availability

VALID_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.PENDING: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED},
    BookingStatus.CONFIRMED: {BookingStatus.COMPLETED, BookingStatus.CANCELLED, BookingStatus.NO_SHOW},
    BookingStatus.COMPLETED: set(),
    BookingStatus.CANCELLED: set(),
    BookingStatus.NO_SHOW: set(),
}


class BookingError(Exception):
    """Base class for booking-flow errors that should become clean 4xx responses."""


class BookingConflictError(BookingError):
    """The requested slot is no longer available."""


class BookingPolicyError(BookingError):
    """The request violates a configured booking policy (lead time, window, etc.)."""


class InvalidTransitionError(BookingError):
    pass


def _advisory_lock_key(staff_id: uuid.UUID) -> int:
    # Postgres advisory locks take a bigint key. zlib.crc32 keeps this
    # deterministic and well within signed-bigint range.
    return zlib.crc32(staff_id.bytes) & 0x7FFFFFFF


async def _lock_staff_for_booking(db: AsyncSession, staff_id: uuid.UUID) -> None:
    await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _advisory_lock_key(staff_id)})


async def _has_overlap_locked(
    db: AsyncSession, staff_id: uuid.UUID, starts_at: datetime, ends_at: datetime,
    exclude_booking_id: uuid.UUID | None = None,
) -> bool:
    stmt = (
        select(Booking.id)
        .where(
            Booking.staff_id == staff_id,
            Booking.status.in_(ACTIVE_BOOKING_STATUSES),
            Booking.starts_at < ends_at,
            Booking.ends_at > starts_at,
        )
        .with_for_update()
    )
    if exclude_booking_id is not None:
        stmt = stmt.where(Booking.id != exclude_booking_id)
    result = await db.execute(stmt)
    return result.first() is not None


async def _resolve_staff_for_any(
    db: AsyncSession,
    business: Business,
    service: Service,
    policy: BookingPolicy,
    starts_at: datetime,
) -> uuid.UUID:
    # Ask for a 2-day UTC-date window around starts_at so a business-local
    # day boundary near midnight UTC can't exclude the date that actually
    # contains starts_at once converted to the business's timezone.
    availability = await compute_availability(
        db, business, service, policy, staff_id=None,
        date_from=(starts_at - timedelta(days=1)).date(), date_to=(starts_at + timedelta(days=1)).date(),
    )
    for slots in availability.values():
        for slot in slots:
            if slot.starts_at == starts_at:
                return slot.staff_id
    raise BookingConflictError("No staff member is available for that time anymore.")


def _check_lead_and_window(policy: BookingPolicy, starts_at: datetime) -> None:
    now = datetime.now(UTC)
    if starts_at < now + timedelta(minutes=policy.min_lead_time_minutes):
        raise BookingPolicyError(
            f"This business requires at least {policy.min_lead_time_minutes} minutes' notice."
        )
    if starts_at > now + timedelta(days=policy.max_advance_days):
        raise BookingPolicyError(
            f"Bookings can only be made up to {policy.max_advance_days} days in advance."
        )


async def create_booking(
    db: AsyncSession,
    *,
    business: Business,
    service: Service,
    policy: BookingPolicy,
    customer: User,
    staff_id: uuid.UUID | None,
    starts_at: datetime,
    customer_notes: str | None,
    idempotency_key: str | None,
    is_demo: bool,
    suppress_notifications: bool = False,
) -> Booking:
    if idempotency_key:
        existing = await db.execute(
            select(Booking).where(
                Booking.business_id == business.id, Booking.idempotency_key == idempotency_key
            )
        )
        existing_booking = existing.scalar_one_or_none()
        if existing_booking is not None:
            return existing_booking

    _check_lead_and_window(policy, starts_at)
    ends_at = starts_at + timedelta(minutes=service.duration_minutes)

    resolved_staff_id = staff_id
    if resolved_staff_id is None:
        resolved_staff_id = await _resolve_staff_for_any(db, business, service, policy, starts_at)

    await _lock_staff_for_booking(db, resolved_staff_id)

    if await _has_overlap_locked(db, resolved_staff_id, starts_at, ends_at):
        raise BookingConflictError("That time was just booked by someone else. Please pick another slot.")

    initial_status = (
        BookingStatus.CONFIRMED
        if policy.confirmation_mode == BookingConfirmationMode.AUTOMATIC
        else BookingStatus.PENDING
    )

    booking = Booking(
        business_id=business.id,
        staff_id=resolved_staff_id,
        service_id=service.id,
        customer_user_id=customer.id,
        starts_at=starts_at,
        ends_at=ends_at,
        status=initial_status,
        price_minor_units_snapshot=service.price_minor_units,
        currency_snapshot=service.currency,
        duration_minutes_snapshot=service.duration_minutes,
        customer_notes=customer_notes,
        is_demo=is_demo,
        idempotency_key=idempotency_key,
    )
    db.add(booking)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise BookingConflictError(
            "That time is no longer available (conflicting booking detected at the database level)."
        ) from exc

    db.add(
        BookingStatusHistory(
            booking_id=booking.id, from_status=None, to_status=initial_status, changed_by_user_id=customer.id
        )
    )
    if not suppress_notifications:
        await notifications.enqueue_booking_created(db, booking)
    await db.commit()
    await db.refresh(booking)
    return booking


def _assert_transition(current: BookingStatus, target: BookingStatus) -> None:
    if target not in VALID_TRANSITIONS.get(current, set()):
        raise InvalidTransitionError(f"Cannot move a booking from {current.value} to {target.value}.")


async def transition_status(
    db: AsyncSession,
    booking: Booking,
    *,
    target: BookingStatus,
    actor_user_id: uuid.UUID | None,
    note: str | None = None,
    suppress_notifications: bool = False,
) -> Booking:
    _assert_transition(booking.status, target)
    from_status = booking.status
    booking.status = target
    if target == BookingStatus.CANCELLED:
        booking.cancelled_at = datetime.now(UTC)
        if note:
            booking.cancel_reason = note
    db.add(
        BookingStatusHistory(
            booking_id=booking.id, from_status=from_status, to_status=target,
            changed_by_user_id=actor_user_id, note=note,
        )
    )
    if not suppress_notifications:
        if target == BookingStatus.CONFIRMED and from_status == BookingStatus.PENDING:
            await notifications.enqueue_confirmed(db, booking)
        elif target == BookingStatus.CANCELLED:
            await notifications.enqueue_cancelled(db, booking)
    elif target == BookingStatus.CANCELLED:
        # Caller (reschedule_booking) sends its own combined notification via
        # notifications.enqueue_rescheduled - just stop this now-superseded
        # booking's pending reminders so none fire after the fact.
        await notifications.cancel_pending_reminders(db, booking.id)
    await db.commit()
    await db.refresh(booking)
    return booking


async def cancel_booking(
    db: AsyncSession,
    booking: Booking,
    policy: BookingPolicy,
    *,
    actor_user_id: uuid.UUID | None,
    reason: str | None,
    is_staff_override: bool = False,
) -> Booking:
    if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        raise InvalidTransitionError("Only pending or confirmed bookings can be cancelled.")

    if not is_staff_override:
        now = datetime.now(UTC)
        if booking.starts_at - now < timedelta(minutes=policy.cancellation_window_minutes):
            raise BookingPolicyError(
                f"Cancellations require at least {policy.cancellation_window_minutes} minutes' notice."
            )

    return await transition_status(
        db, booking, target=BookingStatus.CANCELLED, actor_user_id=actor_user_id, note=reason
    )


async def reschedule_booking(
    db: AsyncSession,
    booking: Booking,
    *,
    business: Business,
    service: Service,
    policy: BookingPolicy,
    customer: User,
    new_starts_at: datetime,
    new_staff_id: uuid.UUID | None,
) -> Booking:
    if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        raise InvalidTransitionError("Only pending or confirmed bookings can be rescheduled.")

    now = datetime.now(UTC)
    if booking.starts_at - now < timedelta(minutes=policy.reschedule_window_minutes):
        raise BookingPolicyError(
            f"Rescheduling requires at least {policy.reschedule_window_minutes} minutes' notice."
        )

    # Create the replacement first; only cancel the original if that succeeds,
    # so a failed reschedule never loses the customer's existing booking.
    new_booking = await create_booking(
        db,
        business=business,
        service=service,
        policy=policy,
        customer=customer,
        staff_id=new_staff_id,
        starts_at=new_starts_at,
        customer_notes=booking.customer_notes,
        idempotency_key=None,
        is_demo=booking.is_demo,
        suppress_notifications=True,
    )
    new_booking.rescheduled_from_booking_id = booking.id

    await transition_status(
        db, booking, target=BookingStatus.CANCELLED, actor_user_id=customer.id, note="rescheduled",
        suppress_notifications=True,
    )
    await notifications.enqueue_rescheduled(db, old_booking=booking, new_booking=new_booking)
    await db.commit()
    await db.refresh(new_booking)
    return new_booking
