"""Service management (spec section 9) — owner/manager only.

Services are never hard-deleted: "archiving" just flips is_active, since
historical bookings snapshot their own price/duration and must stay
readable regardless of what happens to the service record afterwards.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import RequireBusinessRole
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.business import BusinessMembership
from app.models.enums import AuditAction, MembershipRole
from app.models.service import Service
from app.schemas.admin import AdminServiceOut, ServiceCreate, ServiceUpdate

router = APIRouter(prefix="/api/v1/admin/businesses/{business_id}/services", tags=["admin:services"])

_CAN_WRITE = RequireBusinessRole(MembershipRole.BUSINESS_OWNER, MembershipRole.BUSINESS_MANAGER)


async def _get_service_or_404(business_id: uuid.UUID, service_id: uuid.UUID, db: AsyncSession) -> Service:
    result = await db.execute(
        select(Service).where(Service.id == service_id, Service.business_id == business_id)
    )
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Service not found for this business.")
    return service


@router.get("", response_model=list[AdminServiceOut])
async def list_services(
    business_id: uuid.UUID,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> list[Service]:
    # Unlike the public endpoint, this includes inactive/archived services —
    # the owner needs to see (and potentially reactivate) them.
    result = await db.execute(
        select(Service).where(Service.business_id == business_id).order_by(Service.category, Service.name)
    )
    return list(result.scalars().all())


@router.post("", response_model=AdminServiceOut, status_code=status.HTTP_201_CREATED)
async def create_service(
    business_id: uuid.UUID,
    body: ServiceCreate,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> Service:
    service = Service(business_id=business_id, is_active=True, **body.model_dump())
    db.add(service)
    await db.flush()
    db.add(
        AuditLog(
            business_id=business_id,
            actor_user_id=membership.user_id,
            action=AuditAction.SERVICE_CREATED,
            target_type="service",
            target_id=str(service.id),
            details={"name": service.name},
        )
    )
    await db.commit()
    await db.refresh(service)
    return service


@router.patch("/{service_id}", response_model=AdminServiceOut)
async def update_service(
    business_id: uuid.UUID,
    service_id: uuid.UUID,
    body: ServiceUpdate,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> Service:
    service = await _get_service_or_404(business_id, service_id, db)
    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(service, field, value)
    await db.flush()
    db.add(
        AuditLog(
            business_id=business_id,
            actor_user_id=membership.user_id,
            action=AuditAction.SERVICE_UPDATED,
            target_type="service",
            target_id=str(service.id),
            details=changes,
        )
    )
    await db.commit()
    await db.refresh(service)
    return service


@router.post("/{service_id}/archive", response_model=AdminServiceOut)
async def archive_service(
    business_id: uuid.UUID,
    service_id: uuid.UUID,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> Service:
    service = await _get_service_or_404(business_id, service_id, db)
    service.is_active = False
    await db.flush()
    db.add(
        AuditLog(
            business_id=business_id,
            actor_user_id=membership.user_id,
            action=AuditAction.SERVICE_ARCHIVED,
            target_type="service",
            target_id=str(service.id),
            details={},
        )
    )
    await db.commit()
    await db.refresh(service)
    return service


@router.post("/{service_id}/unarchive", response_model=AdminServiceOut)
async def unarchive_service(
    business_id: uuid.UUID,
    service_id: uuid.UUID,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> Service:
    service = await _get_service_or_404(business_id, service_id, db)
    service.is_active = True
    await db.commit()
    await db.refresh(service)
    return service
