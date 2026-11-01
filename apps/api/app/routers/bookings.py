"""Booking creation + "My Appointments" (spec sections 6 & 7).

Every write here re-derives business/service/staff/price from the database
by id — the request body only ever supplies ids and a timestamp, never a
price, a status, or anything else that would need to be trusted from the
client (spec section 18: "Never trust client-provided prices, permissions,
booking statuses, or staff availability").
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.authz import get_current_user
from app.core.config import Settings, get_settings
from app.core.rate_limit import check_rate_limit
from app.db.session import get_db
from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.models.user import User
from app.routers.deps import (
    get_business_or_404,
    get_or_create_policy,
    get_service_in_business_or_404,
)
from app.schemas.booking import (
    BookingCancelRequest,
    BookingCreate,
    BookingListOut,
    BookingOut,
    BookingRescheduleRequest,
)
from app.services import booking as booking_service

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


_WITH_RELATIONS = (
    selectinload(Booking.business),
    selectinload(Booking.service),
    selectinload(Booking.staff),
)


async def _get_own_booking_or_404(booking_id: uuid.UUID, user: User, db: AsyncSession) -> Booking:
    result = await db.execute(select(Booking).where(Booking.id == booking_id).options(*_WITH_RELATIONS))
    booking = result.scalar_one_or_none()
    if booking is None or booking.customer_user_id != user.id:
        # Deliberately the same 404 either way — don't reveal that a
        # booking exists but belongs to someone else.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found.")
    return booking


async def _reload_with_relations(db: AsyncSession, booking_id: uuid.UUID) -> Booking:
    result = await db.execute(select(Booking).where(Booking.id == booking_id).options(*_WITH_RELATIONS))
    return result.scalar_one()


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(
    body: BookingCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> BookingOut:
    check_rate_limit(f"create_booking:{user.id}", settings.rate_limit_booking_per_minute)

    business = await get_business_or_404(body.business_id, db)
    service = await get_service_in_business_or_404(business.id, body.service_id, db)
    policy = await get_or_create_policy(db, business)

    try:
        booking = await booking_service.create_booking(
            db,
            business=business,
            service=service,
            policy=policy,
            customer=user,
            staff_id=body.staff_id,
            starts_at=body.starts_at,
            customer_notes=body.customer_notes,
            idempotency_key=idempotency_key,
            is_demo=user.is_demo,
        )
    except booking_service.BookingConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except booking_service.BookingPolicyError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    return await _reload_with_relations(db, booking.id)


@router.get("/mine", response_model=BookingListOut)
async def list_my_bookings(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> BookingListOut:
    result = await db.execute(
        select(Booking)
        .where(Booking.customer_user_id == user.id)
        .order_by(Booking.starts_at.desc())
        .options(*_WITH_RELATIONS)
    )
    bookings = list(result.scalars().all())

    upcoming = [b for b in bookings if b.status in (BookingStatus.PENDING, BookingStatus.CONFIRMED)]
    completed = [b for b in bookings if b.status in (BookingStatus.COMPLETED, BookingStatus.NO_SHOW)]
    cancelled = [b for b in bookings if b.status == BookingStatus.CANCELLED]
    upcoming.sort(key=lambda b: b.starts_at)  # soonest first for what's ahead
    return BookingListOut(upcoming=upcoming, completed=completed, cancelled=cancelled)


@router.post("/{booking_id}/cancel", response_model=BookingOut)
async def cancel_booking(
    booking_id: uuid.UUID,
    body: BookingCancelRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingOut:
    booking = await _get_own_booking_or_404(booking_id, user, db)
    business = await get_business_or_404(booking.business_id, db)
    policy = await get_or_create_policy(db, business)
    try:
        cancelled = await booking_service.cancel_booking(
            db, booking, policy, actor_user_id=user.id, reason=body.reason
        )
    except booking_service.InvalidTransitionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except booking_service.BookingPolicyError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return await _reload_with_relations(db, cancelled.id)


@router.post("/{booking_id}/reschedule", response_model=BookingOut)
async def reschedule_booking(
    booking_id: uuid.UUID,
    body: BookingRescheduleRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingOut:
    booking = await _get_own_booking_or_404(booking_id, user, db)
    business = await get_business_or_404(booking.business_id, db)
    service = await get_service_in_business_or_404(business.id, booking.service_id, db)
    policy = await get_or_create_policy(db, business)
    try:
        rescheduled = await booking_service.reschedule_booking(
            db,
            booking,
            business=business,
            service=service,
            policy=policy,
            customer=user,
            new_starts_at=body.new_starts_at,
            new_staff_id=body.new_staff_id,
        )
    except (booking_service.InvalidTransitionError, booking_service.BookingPolicyError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except booking_service.BookingConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return await _reload_with_relations(db, rescheduled.id)
