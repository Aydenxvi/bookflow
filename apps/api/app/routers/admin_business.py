"""Business profile, operating hours, and booking policy — owner/manager only.

Operating hours reuse the same WorkingSchedule machinery as staff schedules
(staff_id=None means "the business itself" — see app/models/schedule.py),
so the replace-whole-week helpers live in admin_staff.py and are imported
here rather than duplicated.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import RequireBusinessRole
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.business import Business, BusinessMembership
from app.models.enums import AuditAction, MembershipRole
from app.routers.admin_staff import load_schedule_out, replace_schedule
from app.routers.deps import get_business_or_404, get_or_create_policy
from app.schemas.admin import (
    BookingPolicyOut,
    BookingPolicyUpdate,
    BusinessProfileUpdate,
    DayScheduleOut,
    WeeklyScheduleUpdate,
)
from app.schemas.business import BusinessOut

router = APIRouter(prefix="/api/v1/admin/businesses/{business_id}", tags=["admin:business"])

_CAN_WRITE = RequireBusinessRole(MembershipRole.BUSINESS_OWNER, MembershipRole.BUSINESS_MANAGER)
_OWNER_ONLY = RequireBusinessRole(MembershipRole.BUSINESS_OWNER)


@router.get("/profile", response_model=BusinessOut)
async def get_admin_profile(
    business: Business = Depends(get_business_or_404),
    membership: BusinessMembership = Depends(_CAN_WRITE),
) -> Business:
    return business


@router.patch("/profile", response_model=BusinessOut)
async def update_profile(
    business_id: uuid.UUID,
    body: BusinessProfileUpdate,
    business: Business = Depends(get_business_or_404),
    membership: BusinessMembership = Depends(_OWNER_ONLY),
    db: AsyncSession = Depends(get_db),
) -> Business:
    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(business, field, value)
    await db.flush()
    db.add(
        AuditLog(
            business_id=business_id,
            actor_user_id=membership.user_id,
            action=AuditAction.SETTINGS_UPDATED,
            target_type="business",
            target_id=str(business_id),
            details=changes,
        )
    )
    await db.commit()
    await db.refresh(business)
    return business


@router.get("/hours", response_model=list[DayScheduleOut])
async def get_business_hours(
    business_id: uuid.UUID,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> list[DayScheduleOut]:
    return await load_schedule_out(db, business_id=business_id, staff_id=None)


@router.put("/hours", response_model=list[DayScheduleOut])
async def set_business_hours(
    business_id: uuid.UUID,
    body: WeeklyScheduleUpdate,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> list[DayScheduleOut]:
    await replace_schedule(db, business_id=business_id, staff_id=None, days=body.days)
    db.add(
        AuditLog(
            business_id=business_id,
            actor_user_id=membership.user_id,
            action=AuditAction.SCHEDULE_UPDATED,
            target_type="business",
            target_id=str(business_id),
            details={"days": len(body.days)},
        )
    )
    await db.commit()
    return await load_schedule_out(db, business_id=business_id, staff_id=None)


@router.get("/policy", response_model=BookingPolicyOut)
async def get_policy(
    business: Business = Depends(get_business_or_404),
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> BookingPolicyOut:
    policy = await get_or_create_policy(db, business)
    return BookingPolicyOut.model_validate(policy)


@router.patch("/policy", response_model=BookingPolicyOut)
async def update_policy(
    business_id: uuid.UUID,
    body: BookingPolicyUpdate,
    business: Business = Depends(get_business_or_404),
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> BookingPolicyOut:
    policy = await get_or_create_policy(db, business)
    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(policy, field, value)
    await db.flush()
    db.add(
        AuditLog(
            business_id=business_id,
            actor_user_id=membership.user_id,
            action=AuditAction.SETTINGS_UPDATED,
            target_type="booking_policy",
            target_id=str(policy.id),
            details=changes,
        )
    )
    await db.commit()
    await db.refresh(policy)
    return BookingPolicyOut.model_validate(policy)
