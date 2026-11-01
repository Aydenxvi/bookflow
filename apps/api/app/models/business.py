"""Business, BusinessMembership, BusinessSettings models."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import MembershipRole
from app.models.mixins import TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.policy import BookingPolicy
    from app.models.schedule import ScheduleException, WorkingSchedule
    from app.models.service import Service
    from app.models.staff import Staff
    from app.models.user import User


class Business(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "businesses"

    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(160), nullable=True)

    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Istanbul")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    memberships: Mapped[list["BusinessMembership"]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )
    staff: Mapped[list["Staff"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    services: Mapped[list["Service"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="business")
    working_schedules: Mapped[list["WorkingSchedule"]] = relationship(back_populates="business")
    schedule_exceptions: Mapped[list["ScheduleException"]] = relationship(back_populates="business")
    settings: Mapped["BusinessSettings | None"] = relationship(
        back_populates="business", uselist=False, cascade="all, delete-orphan"
    )
    policy: Mapped["BookingPolicy | None"] = relationship(
        back_populates="business", uselist=False, cascade="all, delete-orphan"
    )


class BusinessMembership(UUIDPkMixin, TimestampMixin, Base):
    """Links a User to a Business with a role. Platform admins are not tied to a
    specific business (see User.is_platform_admin) and therefore have no row here."""

    __tablename__ = "business_memberships"
    __table_args__ = (UniqueConstraint("business_id", "user_id", name="uq_membership_business_user"),)

    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[MembershipRole] = mapped_column(
        Enum(MembershipRole, native_enum=False, length=32), nullable=False
    )

    business: Mapped["Business"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="memberships")


class BusinessSettings(UUIDPkMixin, TimestampMixin, Base):
    """Branding, localization and notification preferences. Booking rules
    (lead time, cancellation windows, etc.) live in BookingPolicy instead."""

    __tablename__ = "business_settings"

    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    primary_language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    supported_languages: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    brand_color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    notify_business_on_new_booking: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_business_on_cancellation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_business_daily_summary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    business: Mapped["Business"] = relationship(back_populates="settings")
