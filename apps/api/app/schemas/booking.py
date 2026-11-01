from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import BookingStatus
from app.schemas.business import BusinessOut
from app.schemas.common import ORMModel
from app.schemas.service import ServiceOut
from app.schemas.staff import StaffOut


class BookingCreate(BaseModel):
    business_id: uuid.UUID
    service_id: uuid.UUID
    staff_id: uuid.UUID | None = None  # None => "any available", resolved server-side
    starts_at: datetime  # UTC; must exactly match a slot the availability endpoint returned
    customer_notes: str | None = Field(default=None, max_length=1000)


class BookingRescheduleRequest(BaseModel):
    new_starts_at: datetime
    new_staff_id: uuid.UUID | None = None


class BookingCancelRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class BookingOut(ORMModel):
    id: uuid.UUID
    status: BookingStatus
    starts_at: datetime
    ends_at: datetime
    price_minor_units_snapshot: int
    currency_snapshot: str
    duration_minutes_snapshot: int
    customer_notes: str | None
    cancel_reason: str | None
    is_demo: bool

    business: BusinessOut
    service: ServiceOut
    staff: StaffOut


class BookingListOut(BaseModel):
    upcoming: list[BookingOut]
    completed: list[BookingOut]
    cancelled: list[BookingOut]
