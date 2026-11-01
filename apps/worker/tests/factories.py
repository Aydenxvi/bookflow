"""Row-insert helpers for the worker's test suite, built on its own Core
tables (app/tables.py) — see conftest.py for why these don't borrow apps/api's
ORM models. Each helper takes an open AsyncConnection (inside the test's
`engine.begin()` block) and returns the row's id."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncConnection

from app.tables import (
    bookings,
    business_memberships,
    business_settings,
    businesses,
    notification_jobs,
    services,
    staff,
    telegram_identities,
    users,
)


async def make_business(conn: AsyncConnection, **overrides) -> uuid.UUID:
    business_id = uuid.uuid4()
    defaults = dict(name="Test Biz", timezone="Europe/Istanbul", currency="USD", is_demo=False)
    defaults.update(overrides)
    await conn.execute(businesses.insert().values(id=business_id, **defaults))
    return business_id


async def make_service(conn: AsyncConnection, business_id: uuid.UUID, **overrides) -> uuid.UUID:
    service_id = uuid.uuid4()
    defaults = dict(name="Haircut")
    defaults.update(overrides)
    await conn.execute(services.insert().values(id=service_id, **defaults))
    return service_id


async def make_staff(conn: AsyncConnection, **overrides) -> uuid.UUID:
    staff_id = uuid.uuid4()
    defaults = dict(display_name="Jamie Stylist")
    defaults.update(overrides)
    await conn.execute(staff.insert().values(id=staff_id, **defaults))
    return staff_id


async def make_user(conn: AsyncConnection, **overrides) -> uuid.UUID:
    user_id = uuid.uuid4()
    defaults = dict(first_name="Customer", last_name=None)
    defaults.update(overrides)
    await conn.execute(users.insert().values(id=user_id, **defaults))
    return user_id


async def make_telegram_identity(conn: AsyncConnection, user_id: uuid.UUID, *, telegram_user_id: int, **overrides):
    defaults = dict(is_bot_blocked=False)
    defaults.update(overrides)
    await conn.execute(
        telegram_identities.insert().values(
            id=uuid.uuid4(), user_id=user_id, telegram_user_id=telegram_user_id, **defaults
        )
    )


async def make_membership(conn: AsyncConnection, business_id: uuid.UUID, user_id: uuid.UUID, *, role: str):
    await conn.execute(
        business_memberships.insert().values(
            id=uuid.uuid4(), business_id=business_id, user_id=user_id, role=role
        )
    )


async def make_settings(conn: AsyncConnection, business_id: uuid.UUID, **overrides):
    defaults = dict(
        notify_business_on_new_booking=True,
        notify_business_on_cancellation=True,
        notify_business_daily_summary=False,
    )
    defaults.update(overrides)
    await conn.execute(business_settings.insert().values(id=uuid.uuid4(), business_id=business_id, **defaults))


async def make_booking(
    conn: AsyncConnection, *, business_id, staff_id, service_id, customer_user_id,
    starts_at: datetime, ends_at: datetime, status: str = "CONFIRMED", **overrides,
) -> uuid.UUID:
    booking_id = uuid.uuid4()
    defaults = dict(price_minor_units_snapshot=5000, currency_snapshot="USD", is_demo=False)
    defaults.update(overrides)
    await conn.execute(
        bookings.insert().values(
            id=booking_id, business_id=business_id, staff_id=staff_id, service_id=service_id,
            customer_user_id=customer_user_id, starts_at=starts_at, ends_at=ends_at, status=status, **defaults,
        )
    )
    return booking_id


async def make_notification_job(
    conn: AsyncConnection, *, business_id, booking_id, job_type: str, recipient_type: str,
    recipient_telegram_user_id: int, dedupe_key: str, scheduled_for: datetime, **overrides,
) -> uuid.UUID:
    job_id = uuid.uuid4()
    defaults = dict(payload={}, status="PENDING", attempts=0, last_error=None, sent_at=None)
    defaults.update(overrides)
    await conn.execute(
        notification_jobs.insert().values(
            id=job_id, business_id=business_id, booking_id=booking_id, job_type=job_type,
            recipient_type=recipient_type, recipient_telegram_user_id=recipient_telegram_user_id,
            dedupe_key=dedupe_key, scheduled_for=scheduled_for, **defaults,
        )
    )
    return job_id
