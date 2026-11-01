"""Dashboard overview (spec section 8: today's/upcoming/completed/cancelled
counts, booking trends via popular services, specialist workload, and a
revenue *estimate* from completed bookings — never labeled as a verified
payment figure, per spec)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import RequireBusinessRole
from app.db.session import get_db
from app.models.booking import Booking
from app.models.business import Business, BusinessMembership
from app.models.enums import BookingStatus, MembershipRole
from app.models.service import Service
from app.models.staff import Staff
from app.routers.deps import get_business_or_404
from app.schemas.admin import DashboardSummaryOut, ServiceCountOut, StaffCountOut

router = APIRouter(prefix="/api/v1/admin/businesses/{business_id}/dashboard", tags=["admin:dashboard"])

_CAN_VIEW = RequireBusinessRole(MembershipRole.BUSINESS_OWNER, MembershipRole.BUSINESS_MANAGER)

_ACTIVE = (BookingStatus.PENDING, BookingStatus.CONFIRMED)


@router.get("", response_model=DashboardSummaryOut)
async def get_dashboard(
    business_id: uuid.UUID,
    business: Business = Depends(get_business_or_404),
    membership: BusinessMembership = Depends(_CAN_VIEW),
    db: AsyncSession = Depends(get_db),
) -> DashboardSummaryOut:
    now = datetime.now(UTC)
    # A wide local-day pad, same reasoning as the calendar endpoint — avoids
    # needing to resolve the business's exact timezone just to bucket "today".
    today_start = now - timedelta(hours=14)
    today_end = now + timedelta(hours=38)

    today_count = await _count(
        db, business_id, Booking.starts_at >= today_start, Booking.starts_at < today_end,
        Booking.status.in_(_ACTIVE),
    )
    upcoming_count = await _count(
        db, business_id, Booking.starts_at >= now, Booking.status.in_(_ACTIVE),
    )
    completed_count = await _count(db, business_id, Booking.status == BookingStatus.COMPLETED)
    cancelled_count = await _count(db, business_id, Booking.status == BookingStatus.CANCELLED)

    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Booking.price_minor_units_snapshot), 0))
        .where(
            Booking.business_id == business_id,
            Booking.status == BookingStatus.COMPLETED,
            Booking.currency_snapshot == business.currency,
        )
    )
    revenue_minor_units = int(revenue_result.scalar_one())

    popular_result = await db.execute(
        select(Service.id, Service.name, func.count(Booking.id))
        .join(Booking, Booking.service_id == Service.id)
        .where(Booking.business_id == business_id, Booking.status != BookingStatus.CANCELLED)
        .group_by(Service.id, Service.name)
        .order_by(func.count(Booking.id).desc())
        .limit(5)
    )
    popular_services = [
        ServiceCountOut(service_id=sid, name=name, count=count) for sid, name, count in popular_result.all()
    ]

    workload_result = await db.execute(
        select(Staff.id, Staff.display_name, func.count(Booking.id))
        .join(Booking, Booking.staff_id == Staff.id)
        .where(Booking.business_id == business_id, Booking.status.in_(_ACTIVE))
        .group_by(Staff.id, Staff.display_name)
        .order_by(func.count(Booking.id).desc())
        .limit(10)
    )
    staff_workload = [
        StaffCountOut(staff_id=sid, display_name=name, count=count) for sid, name, count in workload_result.all()
    ]

    return DashboardSummaryOut(
        today_count=today_count,
        upcoming_count=upcoming_count,
        completed_count=completed_count,
        cancelled_count=cancelled_count,
        revenue_minor_units=revenue_minor_units,
        revenue_currency=business.currency,
        popular_services=popular_services,
        staff_workload=staff_workload,
    )


async def _count(db: AsyncSession, business_id: uuid.UUID, *conditions) -> int:
    result = await db.execute(
        select(func.count(Booking.id)).where(Booking.business_id == business_id, *conditions)
    )
    return int(result.scalar_one())
