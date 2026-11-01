"""Dashboard overview (spec section 8: today's/upcoming/completed/cancelled
counts, booking trends via popular services, specialist workload, and a
revenue *estimate* from completed bookings — never labeled as a verified
payment figure, per spec)."""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
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
from app.schemas.admin import (
    DailyStatsOut,
    DashboardAnalyticsOut,
    DashboardSummaryOut,
    ServiceCountOut,
    StaffCountOut,
    StatusBreakdownOut,
)

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


@router.get("/analytics", response_model=DashboardAnalyticsOut)
async def get_dashboard_analytics(
    business_id: uuid.UUID,
    days: int = Query(default=30, ge=1, le=365),
    business: Business = Depends(get_business_or_404),
    membership: BusinessMembership = Depends(_CAN_VIEW),
    db: AsyncSession = Depends(get_db),
) -> DashboardAnalyticsOut:
    """Daily booking/revenue series and a status breakdown over the last
    `days` days, for the Recharts analytics page (ROADMAP Phase 4).

    Bucketing is done in Python against the business's own timezone rather
    than in SQL, per CLAUDE.md's "conversion to/from business-local time
    happens at the service layer" — a date_trunc('day', ...) in UTC would
    put bookings near local midnight on the wrong day for a business whose
    timezone isn't UTC.
    """
    tz = ZoneInfo(business.timezone)
    now_local = datetime.now(UTC).astimezone(tz)
    range_end_local = now_local.date()
    range_start_local = range_end_local - timedelta(days=days - 1)

    # Wide UTC padding around the local range, same reasoning as the
    # calendar/dashboard-summary endpoints above.
    window_start_utc = datetime.combine(range_start_local, datetime.min.time(), tzinfo=tz).astimezone(UTC)
    window_end_utc = datetime.combine(range_end_local, datetime.min.time(), tzinfo=tz).astimezone(UTC) + timedelta(
        days=1
    )

    result = await db.execute(
        select(Booking.starts_at, Booking.status, Booking.price_minor_units_snapshot, Booking.currency_snapshot)
        .where(
            Booking.business_id == business_id,
            Booking.starts_at >= window_start_utc,
            Booking.starts_at < window_end_utc,
        )
    )
    rows = result.all()

    daily_counts: dict = defaultdict(int)
    daily_revenue: dict = defaultdict(int)
    status_counts: dict = defaultdict(int)

    for starts_at, booking_status, price_minor_units, currency in rows:
        local_date = starts_at.astimezone(tz).date()
        if local_date < range_start_local or local_date > range_end_local:
            continue
        daily_counts[local_date] += 1
        status_counts[booking_status] += 1
        if booking_status == BookingStatus.COMPLETED and currency == business.currency:
            daily_revenue[local_date] += price_minor_units

    daily = [
        DailyStatsOut(
            date=range_start_local + timedelta(days=offset),
            bookings_count=daily_counts.get(range_start_local + timedelta(days=offset), 0),
            revenue_minor_units=daily_revenue.get(range_start_local + timedelta(days=offset), 0),
        )
        for offset in range(days)
    ]
    status_breakdown = [
        StatusBreakdownOut(status=s, count=c) for s, c in sorted(status_counts.items(), key=lambda kv: kv[0].value)
    ]

    return DashboardAnalyticsOut(daily=daily, status_breakdown=status_breakdown, currency=business.currency)


async def _count(db: AsyncSession, business_id: uuid.UUID, *conditions) -> int:
    result = await db.execute(
        select(func.count(Booking.id)).where(Booking.business_id == business_id, *conditions)
    )
    return int(result.scalar_one())
