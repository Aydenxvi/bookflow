"""Admin appointment calendar + manual booking + status management
(spec section 8: Appointment Calendar / Appointment Management).

View access: owner, manager, or staff (a staff member only ever sees their
own bookings — enforced here, never trusted from a query param). Manual
booking creation is owner/manager only (front-desk / reception action);
status changes and cancellation are owner/manager, or staff acting on their
own bookings only.
"""
from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.authz import RequireBusinessRole
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.booking import Booking
from app.models.business import Business, BusinessMembership
from app.models.enums import AuditAction, BookingStatus, MembershipRole
from app.models.staff import Staff
from app.models.user import User
from app.routers.deps import (
    get_business_or_404,
    get_or_create_policy,
    get_service_in_business_or_404,
)
from app.schemas.admin import AdminBookingOut, BookingStatusUpdate, ManualBookingCreate
from app.services import booking as booking_service

router = APIRouter(prefix="/api/v1/admin/businesses/{business_id}/bookings", tags=["admin:bookings"])

_CAN_VIEW = RequireBusinessRole(MembershipRole.BUSINESS_OWNER, MembershipRole.BUSINESS_MANAGER, MembershipRole.STAFF)
_CAN_MANAGE_STATUS = _CAN_VIEW  # staff may act on their own bookings; filtered below
_CAN_CREATE = RequireBusinessRole(MembershipRole.BUSINESS_OWNER, MembershipRole.BUSINESS_MANAGER)

_WITH_RELATIONS = (
    selectinload(Booking.service),
    selectinload(Booking.staff),
    selectinload(Booking.customer),
)


async def _own_staff_id(db: AsyncSession, business_id: uuid.UUID, user_id: uuid.UUID) -> uuid.UUID | None:
    result = await db.execute(
        select(Staff.id).where(Staff.business_id == business_id, Staff.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def _get_booking_or_404(business_id: uuid.UUID, booking_id: uuid.UUID, db: AsyncSession) -> Booking:
    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking_id, Booking.business_id == business_id)
        .options(*_WITH_RELATIONS)
    )
    booking = result.scalar_one_or_none()
    if booking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found for this business.")
    return booking


async def _assert_can_touch(
    db: AsyncSession, membership: BusinessMembership, booking: Booking
) -> None:
    if membership.role in (MembershipRole.BUSINESS_OWNER, MembershipRole.BUSINESS_MANAGER, MembershipRole.PLATFORM_ADMIN):
        return
    own_staff_id = await _own_staff_id(db, booking.business_id, membership.user_id)
    if own_staff_id is None or own_staff_id != booking.staff_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only manage your own appointments.")


@router.get("", response_model=list[AdminBookingOut])
async def list_calendar_bookings(
    business_id: uuid.UUID,
    date_from: date = Query(...),
    date_to: date = Query(...),
    staff_id: uuid.UUID | None = Query(default=None),
    service_id: uuid.UUID | None = Query(default=None),
    status_filter: BookingStatus | None = Query(default=None, alias="status"),
    business: Business = Depends(get_business_or_404),
    membership: BusinessMembership = Depends(_CAN_VIEW),
    db: AsyncSession = Depends(get_db),
) -> list[Booking]:
    if (date_to - date_from).days > 92:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Range cannot exceed 92 days.")

    # Query in UTC using a generous pad on each side of the business-local
    # day boundary, since starts_at is stored in UTC but the calendar is
    # framed in the business's own local days.
    stmt = (
        select(Booking)
        .where(
            Booking.business_id == business_id,
            Booking.starts_at >= _local_midnight_as_utc_floor(date_from),
            Booking.starts_at < _local_midnight_as_utc_ceiling(date_to),
        )
        .options(*_WITH_RELATIONS)
        .order_by(Booking.starts_at)
    )
    if staff_id is not None:
        stmt = stmt.where(Booking.staff_id == staff_id)
    if service_id is not None:
        stmt = stmt.where(Booking.service_id == service_id)
    if status_filter is not None:
        stmt = stmt.where(Booking.status == status_filter)

    if membership.role == MembershipRole.STAFF:
        own_staff_id = await _own_staff_id(db, business_id, membership.user_id)
        if own_staff_id is None:
            return []
        stmt = stmt.where(Booking.staff_id == own_staff_id)

    result = await db.execute(stmt)
    return list(result.scalars().all())


def _local_midnight_as_utc_floor(d: date) -> datetime:
    # A wide, cheap-to-compute pad (14h, comfortably over the largest UTC
    # offset) rather than resolving the business's exact timezone here —
    # correct in every case, never excludes a booking that genuinely falls
    # on that local date. The frontend still groups strictly by local date
    # for display, so a little overfetching at the edges is harmless.
    return datetime.combine(d, time.min, tzinfo=UTC) - timedelta(hours=14)


def _local_midnight_as_utc_ceiling(d: date) -> datetime:
    return datetime.combine(d, time.max, tzinfo=UTC) + timedelta(hours=14)


@router.post("", response_model=AdminBookingOut, status_code=status.HTTP_201_CREATED)
async def create_manual_booking(
    business_id: uuid.UUID,
    body: ManualBookingCreate,
    business: Business = Depends(get_business_or_404),
    membership: BusinessMembership = Depends(_CAN_CREATE),
    db: AsyncSession = Depends(get_db),
) -> Booking:
    service = await get_service_in_business_or_404(business_id, body.service_id, db)
    policy = await get_or_create_policy(db, business)

    guest = User(first_name=body.customer_name, phone=body.customer_phone, is_demo=business.is_demo)
    db.add(guest)
    await db.flush()

    try:
        booking = await booking_service.create_booking(
            db,
            business=business,
            service=service,
            policy=policy,
            customer=guest,
            staff_id=body.staff_id,
            starts_at=body.starts_at,
            customer_notes=body.customer_notes,
            idempotency_key=None,
            is_demo=business.is_demo,
        )
    except booking_service.BookingConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except booking_service.BookingPolicyError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    db.add(
        AuditLog(
            business_id=business_id,
            actor_user_id=membership.user_id,
            action=AuditAction.BOOKING_CREATED_MANUALLY,
            target_type="booking",
            target_id=str(booking.id),
            details={"customer_name": body.customer_name},
        )
    )
    await db.commit()

    return await _get_booking_or_404(business_id, booking.id, db)


@router.post("/{booking_id}/status", response_model=AdminBookingOut)
async def change_booking_status(
    business_id: uuid.UUID,
    booking_id: uuid.UUID,
    body: BookingStatusUpdate,
    membership: BusinessMembership = Depends(_CAN_MANAGE_STATUS),
    db: AsyncSession = Depends(get_db),
) -> Booking:
    booking = await _get_booking_or_404(business_id, booking_id, db)
    await _assert_can_touch(db, membership, booking)

    try:
        if body.status == BookingStatus.CANCELLED:
            business = await get_business_or_404(business_id, db)
            policy = await get_or_create_policy(db, business)
            await booking_service.cancel_booking(
                db, booking, policy, actor_user_id=membership.user_id, reason=body.note, is_staff_override=True
            )
        else:
            await booking_service.transition_status(
                db, booking, target=body.status, actor_user_id=membership.user_id, note=body.note
            )
    except booking_service.InvalidTransitionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except booking_service.BookingPolicyError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    db.add(
        AuditLog(
            business_id=business_id,
            actor_user_id=membership.user_id,
            action=AuditAction.BOOKING_STATUS_CHANGED,
            target_type="booking",
            target_id=str(booking_id),
            details={"status": body.status.value, "note": body.note},
        )
    )
    await db.commit()

    return await _get_booking_or_404(business_id, booking_id, db)
