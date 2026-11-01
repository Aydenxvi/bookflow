"""Real availability endpoint — Step 4 of the booking flow. Slots here come
directly from app/services/availability.py; nothing is hardcoded."""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.business import Business
from app.routers.deps import (
    get_business_or_404,
    get_or_create_policy,
    get_service_in_business_or_404,
)
from app.schemas.availability import DayAvailabilityOut, SlotOut
from app.services.availability import AvailabilityError, compute_availability

router = APIRouter(prefix="/api/v1/businesses/{business_id}/availability", tags=["availability"])

MAX_RANGE_DAYS = 45


@router.get("", response_model=list[DayAvailabilityOut])
async def get_availability(
    service_id: uuid.UUID,
    date_from: date,
    date_to: date,
    staff_id: uuid.UUID | None = Query(default=None),
    business: Business = Depends(get_business_or_404),
    db: AsyncSession = Depends(get_db),
) -> list[DayAvailabilityOut]:
    if (date_to - date_from).days > MAX_RANGE_DAYS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Range cannot exceed {MAX_RANGE_DAYS} days.")

    service = await get_service_in_business_or_404(business.id, service_id, db)
    policy = await get_or_create_policy(db, business)

    try:
        availability = await compute_availability(
            db, business, service, policy, staff_id=staff_id, date_from=date_from, date_to=date_to
        )
    except AvailabilityError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    return [
        DayAvailabilityOut(
            date=d,
            has_availability=bool(slots),
            slots=[SlotOut(staff_id=str(s.staff_id), starts_at=s.starts_at, ends_at=s.ends_at) for s in slots],
        )
        for d, slots in sorted(availability.items())
    ]
