"""Fetches the extra context a notification job's payload alone doesn't carry
(service/staff/business names, the booking's current time, business
timezone) so messages.py can render human-readable text. Deliberately reads
this fresh at send time rather than snapshotting it into the job's payload at
enqueue time — a renamed service or a business's timezone change should show
up correctly in a reminder sent days later, not a stale copy.
"""
from __future__ import annotations

import uuid
from datetime import date as date_type
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncConnection

from app.tables import bookings, businesses, services, staff, users


async def fetch_booking_context(conn: AsyncConnection, booking_id: uuid.UUID) -> dict | None:
    row = (
        await conn.execute(
            select(
                bookings.c.starts_at,
                bookings.c.status,
                services.c.name.label("service_name"),
                staff.c.display_name.label("staff_name"),
                businesses.c.name.label("business_name"),
                businesses.c.timezone.label("business_timezone"),
                users.c.first_name.label("customer_first_name"),
            )
            .select_from(bookings)
            .join(services, services.c.id == bookings.c.service_id)
            .join(staff, staff.c.id == bookings.c.staff_id)
            .join(businesses, businesses.c.id == bookings.c.business_id)
            .join(users, users.c.id == bookings.c.customer_user_id)
            .where(bookings.c.id == booking_id)
        )
    ).mappings().first()
    if row is None:
        return None
    return dict(row)


def local_time_str(dt_utc: datetime, tz_name: str) -> str:
    local = dt_utc.astimezone(ZoneInfo(tz_name))
    return local.strftime("%a %b %-d, %H:%M")


async def fetch_daily_summary_context(
    conn: AsyncConnection, business_id: uuid.UUID, summary_date: date_type
) -> dict:
    business_row = (
        await conn.execute(
            select(businesses.c.name, businesses.c.timezone, businesses.c.currency).where(
                businesses.c.id == business_id
            )
        )
    ).mappings().first()

    tz = ZoneInfo(business_row["timezone"])
    # The business-local day's bounds, computed in its own timezone so
    # bookings right at midnight land on the correct local day.
    window_start = datetime(summary_date.year, summary_date.month, summary_date.day, tzinfo=tz)
    window_end = window_start + timedelta(days=1)

    stats_row = (
        await conn.execute(
            select(
                func.count(bookings.c.id).label("booking_count"),
                func.coalesce(func.sum(bookings.c.price_minor_units_snapshot), 0).label("revenue_minor_units"),
            ).where(
                bookings.c.business_id == business_id,
                bookings.c.starts_at >= window_start,
                bookings.c.starts_at < window_end,
                bookings.c.status.in_(["CONFIRMED", "COMPLETED"]),
                bookings.c.is_demo.is_(False),
            )
        )
    ).mappings().first()

    return {
        "business_name": business_row["name"],
        "currency": business_row["currency"],
        "booking_count": stats_row["booking_count"],
        "revenue_minor_units": stats_row["revenue_minor_units"],
    }
