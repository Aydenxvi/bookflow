"""Public, read-only business/service/staff endpoints — the data behind
Steps 1-3 of the customer booking flow (spec section 6)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.business import Business
from app.models.schedule import WorkingSchedule
from app.models.service import Service, StaffService
from app.models.staff import Staff
from app.routers.deps import get_business_by_slug_or_404, get_business_or_404
from app.schemas.business import BusinessHoursOut, BusinessOut, BusinessProfileOut
from app.schemas.service import ServiceOut
from app.schemas.staff import StaffOut

router = APIRouter(prefix="/api/v1/businesses", tags=["businesses"])


@router.get("/{slug}", response_model=BusinessProfileOut)
async def get_business_profile(
    business: Business = Depends(get_business_by_slug_or_404), db: AsyncSession = Depends(get_db)
) -> BusinessProfileOut:
    result = await db.execute(
        select(WorkingSchedule).where(
            WorkingSchedule.business_id == business.id, WorkingSchedule.staff_id.is_(None)
        )
    )
    hours = [
        BusinessHoursOut(
            weekday=s.weekday, start_time=s.start_time.strftime("%H:%M"), end_time=s.end_time.strftime("%H:%M")
        )
        for s in sorted(result.scalars().all(), key=lambda s: s.weekday)
    ]
    base = BusinessOut.model_validate(business)
    return BusinessProfileOut(**base.model_dump(), hours=hours)


@router.get("/{business_id}/services", response_model=list[ServiceOut])
async def list_services(
    business: Business = Depends(get_business_or_404), db: AsyncSession = Depends(get_db)
) -> list[ServiceOut]:
    result = await db.execute(
        select(Service)
        .where(Service.business_id == business.id, Service.is_active.is_(True))
        .order_by(Service.category, Service.name)
    )
    return list(result.scalars().all())


@router.get("/{business_id}/staff", response_model=list[StaffOut])
async def list_staff(
    business: Business = Depends(get_business_or_404),
    service_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[StaffOut]:
    stmt = select(Staff).where(Staff.business_id == business.id, Staff.is_active.is_(True))
    if service_id is not None:
        stmt = stmt.join(StaffService, StaffService.staff_id == Staff.id).where(
            StaffService.service_id == service_id
        )
    result = await db.execute(stmt.distinct().order_by(Staff.display_name))
    return list(result.scalars().all())
