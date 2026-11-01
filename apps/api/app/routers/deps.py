"""Shared lookups used by several routers: fetch-or-404 helpers that also
enforce basic data integrity (e.g. a service/staff must belong to the
business referenced in the URL — never trust a mismatched id combination)."""
from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.business import Business
from app.models.policy import BookingPolicy
from app.models.service import Service
from app.models.staff import Staff


async def get_business_by_slug_or_404(slug: str, db: AsyncSession = Depends(get_db)) -> Business:
    result = await db.execute(select(Business).where(Business.slug == slug, Business.is_active.is_(True)))
    business = result.scalar_one_or_none()
    if business is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Business not found.")
    return business


async def get_business_or_404(business_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Business:
    business = await db.get(Business, business_id)
    if business is None or not business.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Business not found.")
    return business


async def get_service_in_business_or_404(
    business_id: uuid.UUID, service_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> Service:
    result = await db.execute(
        select(Service).where(
            Service.id == service_id, Service.business_id == business_id, Service.is_active.is_(True)
        )
    )
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Service not found for this business.")
    return service


async def get_staff_in_business_or_404(
    business_id: uuid.UUID, staff_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> Staff:
    result = await db.execute(
        select(Staff).where(Staff.id == staff_id, Staff.business_id == business_id, Staff.is_active.is_(True))
    )
    staff = result.scalar_one_or_none()
    if staff is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Staff member not found for this business.")
    return staff


async def get_or_create_policy(db: AsyncSession, business: Business) -> BookingPolicy:
    result = await db.execute(select(BookingPolicy).where(BookingPolicy.business_id == business.id))
    policy = result.scalar_one_or_none()
    if policy is None:
        policy = BookingPolicy(business_id=business.id)
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
    return policy
