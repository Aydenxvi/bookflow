"""Staff model — a staff profile within a business, optionally linked to a login User."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.business import Business
    from app.models.schedule import ScheduleException, WorkingSchedule
    from app.models.service import StaffService
    from app.models.user import User


class Staff(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "staff"

    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Nullable: a business owner can create a staff profile before that person
    # has a Telegram-linked login, or for staff who never log in themselves.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    specialization: Mapped[str | None] = mapped_column(String(160), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    business: Mapped[Business] = relationship(back_populates="staff")
    user: Mapped[User | None] = relationship(back_populates="staff_profiles")
    staff_services: Mapped[list[StaffService]] = relationship(
        back_populates="staff", cascade="all, delete-orphan"
    )
    working_schedules: Mapped[list[WorkingSchedule]] = relationship(
        back_populates="staff", cascade="all, delete-orphan"
    )
    schedule_exceptions: Mapped[list[ScheduleException]] = relationship(
        back_populates="staff", cascade="all, delete-orphan"
    )
    bookings: Mapped[list[Booking]] = relationship(back_populates="staff")
