from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class AvailabilityRequest(BaseModel):
    service_id: str
    staff_id: str | None = None  # None / "any" => any available specialist
    date_from: date
    date_to: date


class SlotOut(BaseModel):
    staff_id: str
    starts_at: datetime  # UTC
    ends_at: datetime  # UTC


class DayAvailabilityOut(BaseModel):
    date: date
    has_availability: bool
    slots: list[SlotOut]
