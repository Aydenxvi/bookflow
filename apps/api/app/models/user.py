"""User and TelegramIdentity models.

A User is the platform-wide identity. TelegramIdentity holds the Telegram-specific
auth data (kept separate per the spec so a User could, in principle, have other
identity sources later without reshaping the core User table).
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.business import BusinessMembership
    from app.models.staff import Staff


class User(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    is_platform_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Demo users are synthetic identities created for browser-demo-mode sessions.
    # They can place real rows in the booking engine, but are excluded from
    # business-facing analytics/exports.
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    telegram_identity: Mapped[TelegramIdentity | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    memberships: Mapped[list[BusinessMembership]] = relationship(back_populates="user")
    staff_profiles: Mapped[list[Staff]] = relationship(back_populates="user")
    bookings: Mapped[list[Booking]] = relationship(
        back_populates="customer", foreign_keys="Booking.customer_user_id"
    )

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() if self.last_name else self.first_name


class TelegramIdentity(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "telegram_identities"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_bot_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship(back_populates="telegram_identity")
