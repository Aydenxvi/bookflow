"""BookingPolicy — the configurable rules the availability/booking engine enforces."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import BookingConfirmationMode
from app.models.mixins import TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.business import Business


class BookingPolicy(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "booking_policies"

    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    confirmation_mode: Mapped[BookingConfirmationMode] = mapped_column(
        Enum(BookingConfirmationMode, native_enum=False, length=16),
        nullable=False,
        default=BookingConfirmationMode.AUTOMATIC,
    )

    slot_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    buffer_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_lead_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    max_advance_days: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    cancellation_window_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    reschedule_window_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=120)

    # List of ints, minutes-before-appointment, e.g. [1440, 120, 30]
    reminder_offsets_minutes: Mapped[list[int]] = mapped_column(
        JSON, nullable=False, default=lambda: [1440, 120, 30]
    )

    business: Mapped[Business] = relationship(back_populates="policy")
