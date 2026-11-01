from __future__ import annotations

import uuid

from app.schemas.common import ORMModel


class ServiceOut(ORMModel):
    id: uuid.UUID
    name: str
    description: str | None
    category: str | None
    image_url: str | None
    duration_minutes: int
    price_minor_units: int
    currency: str
    is_active: bool
