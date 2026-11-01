"""NotificationJob — a persistent, idempotent, retryable unit of work for the worker.

The worker claims pending jobs whose scheduled_for <= now() using
`SELECT ... FOR UPDATE SKIP LOCKED`, so multiple worker replicas never send
the same notification twice. `dedupe_key` gives a second, stronger guarantee:
it's unique, built as f"{job_type}:{booking_id}:{extra}" so even a retried
job-creation call can't double-insert.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, BigInteger, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import NotificationJobStatus, NotificationJobType, RecipientType
from app.models.mixins import TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.business import Business


class NotificationJob(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "notification_jobs"

    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), nullable=True, index=True
    )

    job_type: Mapped[NotificationJobType] = mapped_column(
        Enum(NotificationJobType, native_enum=False, length=32), nullable=False
    )
    recipient_type: Mapped[RecipientType] = mapped_column(
        Enum(RecipientType, native_enum=False, length=16), nullable=False
    )
    recipient_telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    status: Mapped[NotificationJobStatus] = mapped_column(
        Enum(NotificationJobStatus, native_enum=False, length=16),
        nullable=False,
        default=NotificationJobStatus.PENDING,
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Unique key preventing duplicate job creation, e.g. "reminder_1440:<booking_id>"
    dedupe_key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)

    business: Mapped["Business"] = relationship()
    booking: Mapped["Booking | None"] = relationship()
