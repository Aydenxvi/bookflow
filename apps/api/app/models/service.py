"""Service and StaffService (join table) models."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.business import Business
    from app.models.staff import Staff


class Service(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "services"

    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    # Price stored as an exact integer in minor currency units (cents). Never float.
    price_minor_units: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    business: Mapped["Business"] = relationship(back_populates="services")
    staff_services: Mapped[list["StaffService"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )
    bookings: Mapped[list["Booking"]] = relationship(back_populates="service")


class StaffService(UUIDPkMixin, TimestampMixin, Base):
    """Which staff members can perform which services."""

    __tablename__ = "staff_services"
    __table_args__ = (UniqueConstraint("staff_id", "service_id", name="uq_staff_service"),)

    staff_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("staff.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True
    )

    staff: Mapped["Staff"] = relationship(back_populates="staff_services")
    service: Mapped["Service"] = relationship(back_populates="staff_services")
