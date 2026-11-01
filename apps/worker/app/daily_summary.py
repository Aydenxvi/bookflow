"""Keeps BUSINESS_DAILY_SUMMARY jobs flowing for businesses that opted in
(BusinessSettings.notify_business_daily_summary), with no in-memory
scheduler: each poll cycle just makes sure "the next one" exists as a
PENDING row with the right dedupe_key and scheduled_for, which is itself
enough to prevent duplicates and to naturally produce tomorrow's job once
today's has been sent (see _next_target below).
"""
from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from app.config import get_settings
from app.tables import (
    JobType,
    MembershipRole,
    RecipientType,
    business_memberships,
    business_settings,
    businesses,
    notification_jobs,
    telegram_identities,
)


def _next_target(now_utc: datetime, tz_name: str, local_hour: int) -> datetime:
    """The next business-local `local_hour:00` at or after `now_utc`, as a UTC
    datetime — today's if that hour hasn't passed yet in the business's own
    timezone, otherwise tomorrow's."""
    tz = ZoneInfo(tz_name)
    now_local = now_utc.astimezone(tz)
    candidate = now_local.replace(hour=local_hour, minute=0, second=0, microsecond=0)
    if candidate <= now_local:
        candidate += timedelta(days=1)
    return candidate.astimezone(UTC)


async def ensure_daily_summary_jobs(conn: AsyncConnection) -> int:
    """Returns how many new jobs were inserted this call (0 most of the
    time - idempotent via dedupe_key)."""
    settings = get_settings()
    now = datetime.now(UTC)

    opted_in = (
        await conn.execute(
            select(businesses.c.id, businesses.c.timezone).join(
                business_settings, business_settings.c.business_id == businesses.c.id
            ).where(business_settings.c.notify_business_daily_summary.is_(True))
        )
    ).mappings().all()

    inserted = 0
    for business in opted_in:
        target = _next_target(now, business["timezone"], settings.daily_summary_local_hour)
        target_date: date = target.astimezone(ZoneInfo(business["timezone"])).date()

        recipients = (
            await conn.execute(
                select(telegram_identities.c.telegram_user_id)
                .join(business_memberships, business_memberships.c.user_id == telegram_identities.c.user_id)
                .where(
                    business_memberships.c.business_id == business["id"],
                    business_memberships.c.role.in_(
                        [MembershipRole.BUSINESS_OWNER, MembershipRole.BUSINESS_MANAGER]
                    ),
                    telegram_identities.c.is_bot_blocked.is_(False),
                )
            )
        ).scalars().all()

        for telegram_user_id in recipients:
            dedupe_key = f"business_daily_summary:{business['id']}:{target_date.isoformat()}:{telegram_user_id}"
            existing = (
                await conn.execute(
                    select(notification_jobs.c.id).where(notification_jobs.c.dedupe_key == dedupe_key)
                )
            ).scalar_one_or_none()
            if existing is not None:
                continue

            await conn.execute(
                notification_jobs.insert().values(
                    id=uuid.uuid4(),
                    business_id=business["id"],
                    booking_id=None,
                    job_type=JobType.BUSINESS_DAILY_SUMMARY,
                    recipient_type=RecipientType.BUSINESS,
                    recipient_telegram_user_id=telegram_user_id,
                    payload={"date": target_date.isoformat()},
                    status="PENDING",
                    attempts=0,
                    last_error=None,
                    scheduled_for=target,
                    sent_at=None,
                    dedupe_key=dedupe_key,
                    created_at=now,
                    updated_at=now,
                )
            )
            inserted += 1
    return inserted
