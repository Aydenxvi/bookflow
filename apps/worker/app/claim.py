"""Claiming and resolving a single NotificationJob row.

One job is claimed and fully processed (rendered, sent, status updated) per
transaction — see CLAUDE.md: "claims jobs with SELECT ... FOR UPDATE SKIP
LOCKED". Holding the row lock for the duration of one Telegram HTTP call is a
deliberate, documented trade-off for a single low-throughput worker: if the
process crashes mid-send, the lock releases with the connection and the job
is still PENDING for the next poll to retry — exactly the safety property
wanted, without introducing an undocumented "processing" status value that
the rest of the codebase's NotificationJobStatus enum doesn't know about.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from app.tables import JobStatus, notification_jobs


async def claim_next_job(conn: AsyncConnection) -> dict | None:
    """Must be called within an open transaction the caller will commit (to
    release the row lock) or roll back (to leave the job untouched for
    another worker/poll)."""
    row = (
        await conn.execute(
            select(notification_jobs)
            .where(
                notification_jobs.c.status == JobStatus.PENDING,
                notification_jobs.c.scheduled_for <= datetime.now(UTC),
            )
            .order_by(notification_jobs.c.scheduled_for)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
    ).mappings().first()
    return dict(row) if row is not None else None


async def mark_sent(conn: AsyncConnection, job_id) -> None:
    await conn.execute(
        update(notification_jobs)
        .where(notification_jobs.c.id == job_id)
        .values(
            status=JobStatus.SENT,
            sent_at=datetime.now(UTC),
            attempts=notification_jobs.c.attempts + 1,
        )
    )


def _backoff_seconds(attempts: int, *, base: int, cap: int) -> int:
    return min(base * (2**attempts), cap)


async def mark_failed_or_retry(
    conn: AsyncConnection, job_id, *, error: str, attempts_before: int, max_attempts: int, base: int, cap: int
) -> None:
    attempts_after = attempts_before + 1
    error = error[:1000]
    if attempts_after >= max_attempts:
        await conn.execute(
            update(notification_jobs)
            .where(notification_jobs.c.id == job_id)
            .values(status=JobStatus.FAILED, attempts=attempts_after, last_error=error)
        )
        return

    retry_at = datetime.now(UTC) + timedelta(seconds=_backoff_seconds(attempts_after, base=base, cap=cap))
    await conn.execute(
        update(notification_jobs)
        .where(notification_jobs.c.id == job_id)
        .values(attempts=attempts_after, last_error=error, scheduled_for=retry_at)
    )
