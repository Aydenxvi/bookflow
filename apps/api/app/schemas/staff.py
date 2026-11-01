from __future__ import annotations

import uuid

from app.schemas.common import ORMModel

ANY_STAFF_SENTINEL = "any"


class StaffOut(ORMModel):
    id: uuid.UUID
    display_name: str
    photo_url: str | None
    specialization: str | None
    bio: str | None
    is_active: bool
