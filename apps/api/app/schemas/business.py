from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.schemas.common import ORMModel


class BusinessHoursOut(BaseModel):
    weekday: int
    start_time: str  # "HH:MM"
    end_time: str


class BusinessOut(ORMModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    logo_url: str | None
    cover_image_url: str | None
    address: str | None
    contact_phone: str | None
    contact_email: str | None
    timezone: str
    currency: str
    is_demo: bool


class BusinessProfileOut(BusinessOut):
    """Business profile plus its weekly operating hours, for the profile screen."""

    hours: list[BusinessHoursOut]
