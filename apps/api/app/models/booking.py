"""Booking and BookingStatusHistory models.

Concurrency-safety note: the actual overlap-prevention constraint — a
PostgreSQL EXCLUDE constraint over (staff_id, during tstzrange) using
btree_gist, scoped to active statuses — is created directly in the Alembic
migration (see versions/0001_initial_schema.py) rather than declared through
the ORM, because it depends on a generated `during` column that application
code never needs to read or write. The ORM only ever touches starts_at/ends_at;
the database guarantees no two active bookings for the same staff member can
overlap, regardless of what the application layer does.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import BookingStatus
from app.models.mixins import TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.business import Business
    from app.models.service import Service
    from app.models.staff import Staff
    from app.models.user import User


class Booking(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "bookings"
    __table_args__ = (
        # Idempotency keys are only unique within a business, so two different
        # businesses can't collide, but the same business can't accept the
        # same client-generated key twice.
        UniqueConstraint("business_id", "idempotency_key", name="uq_booking_business_idempotency_key"),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("staff.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Always stored in UTC. Business-local display conversion happens in the
    # service/presentation layer using Business.timezone.
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, native_enum=False, length=16), nullable=False, default=BookingStatus.PENDING
    )

    # Snapshot of price/duration at booking time, so later edits to the
    # Service don't rewrite history.
    price_minor_units_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    currency_snapshot: Mapped[str] = mapped_column(String(8), nullable=False)
    duration_minutes_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)

    customer_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Set when this booking replaced an earlier one via reschedule, so history
    # is traceable without losing the old row.
    rescheduled_from_booking_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True
    )

    business: Mapped["Business"] = relationship(back_populates="bookings")
    staff: Mapped["Staff"] = relationship(back_populates="bookings")
    service: Mapped["Service"] = relationship(back_populates="bookings")
    customer: Mapped["User"] = relationship(back_populates="bookings", foreign_keys=[customer_user_id])
    status_history: Mapped[list["BookingStatusHistory"]] = relationship(
        back_populates="booking", cascade="all, delete-orphan", order_by="BookingStatusHistory.created_at"
    )


class BookingStatusHistory(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "booking_status_history"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[BookingStatus | None] = mapped_column(
        Enum(BookingStatus, native_enum=False, length=16), nullable=True
    )
    to_status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, native_enum=False, length=16), nullable=False
    )
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)

    booking: Mapped["Booking"] = relationship(back_populates="status_history")
