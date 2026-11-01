"""Staff management (spec section 10) — owner/manager only.

Covers staff CRUD, which services each staff member can perform, their
weekly working hours + recurring breaks, and one-off schedule exceptions
(leave, extra holiday, closure) — both business-wide and per-staff.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.authz import RequireBusinessRole
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.business import BusinessMembership
from app.models.enums import AuditAction, MembershipRole
from app.models.schedule import ScheduleException, WorkingSchedule, WorkingScheduleBreak
from app.models.service import StaffService
from app.models.staff import Staff
from app.schemas.admin import (
    AdminStaffOut,
    DayScheduleOut,
    ScheduleExceptionCreate,
    ScheduleExceptionOut,
    StaffCreate,
    StaffServicesUpdate,
    StaffUpdate,
    WeeklyScheduleUpdate,
)

router = APIRouter(prefix="/api/v1/admin/businesses/{business_id}/staff", tags=["admin:staff"])

_CAN_WRITE = RequireBusinessRole(MembershipRole.BUSINESS_OWNER, MembershipRole.BUSINESS_MANAGER)


def _to_admin_staff_out(staff: Staff) -> AdminStaffOut:
    return AdminStaffOut(
        id=staff.id,
        display_name=staff.display_name,
        photo_url=staff.photo_url,
        specialization=staff.specialization,
        bio=staff.bio,
        is_active=staff.is_active,
        service_ids=[ss.service_id for ss in staff.staff_services],
    )


async def _get_staff_or_404(business_id: uuid.UUID, staff_id: uuid.UUID, db: AsyncSession) -> Staff:
    result = await db.execute(
        select(Staff)
        .where(Staff.id == staff_id, Staff.business_id == business_id)
        .options(selectinload(Staff.staff_services))
    )
    staff = result.scalar_one_or_none()
    if staff is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Staff member not found for this business.")
    return staff


@router.get("", response_model=list[AdminStaffOut])
async def list_staff(
    business_id: uuid.UUID,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> list[AdminStaffOut]:
    result = await db.execute(
        select(Staff)
        .where(Staff.business_id == business_id)
        .options(selectinload(Staff.staff_services))
        .order_by(Staff.display_name)
    )
    return [_to_admin_staff_out(s) for s in result.scalars().all()]


@router.post("", response_model=AdminStaffOut, status_code=status.HTTP_201_CREATED)
async def create_staff(
    business_id: uuid.UUID,
    body: StaffCreate,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> AdminStaffOut:
    staff = Staff(
        business_id=business_id,
        display_name=body.display_name,
        photo_url=body.photo_url,
        specialization=body.specialization,
        bio=body.bio,
        is_active=True,
    )
    db.add(staff)
    await db.flush()
    for service_id in body.service_ids:
        db.add(StaffService(staff_id=staff.id, service_id=service_id))
    db.add(
        AuditLog(
            business_id=business_id,
            actor_user_id=membership.user_id,
            action=AuditAction.STAFF_CREATED,
            target_type="staff",
            target_id=str(staff.id),
            details={"display_name": staff.display_name},
        )
    )
    await db.commit()
    return _to_admin_staff_out(await _get_staff_or_404(business_id, staff.id, db))


@router.patch("/{staff_id}", response_model=AdminStaffOut)
async def update_staff(
    business_id: uuid.UUID,
    staff_id: uuid.UUID,
    body: StaffUpdate,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> AdminStaffOut:
    staff = await _get_staff_or_404(business_id, staff_id, db)
    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(staff, field, value)
    await db.flush()
    db.add(
        AuditLog(
            business_id=business_id,
            actor_user_id=membership.user_id,
            action=AuditAction.STAFF_UPDATED,
            target_type="staff",
            target_id=str(staff.id),
            details=changes,
        )
    )
    await db.commit()
    return _to_admin_staff_out(await _get_staff_or_404(business_id, staff_id, db))


@router.put("/{staff_id}/services", response_model=AdminStaffOut)
async def set_staff_services(
    business_id: uuid.UUID,
    staff_id: uuid.UUID,
    body: StaffServicesUpdate,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> AdminStaffOut:
    staff = await _get_staff_or_404(business_id, staff_id, db)
    await db.execute(delete(StaffService).where(StaffService.staff_id == staff_id))
    for service_id in body.service_ids:
        db.add(StaffService(staff_id=staff_id, service_id=service_id))
    await db.commit()
    # `staff` is already in the session's identity map with `staff_services`
    # loaded (from the _get_staff_or_404 call above) — without an explicit
    # refresh, SQLAlchemy would keep serving that now-stale cached collection
    # instead of the rows we just replaced, even though the DB is correct.
    await db.refresh(staff, attribute_names=["staff_services"])
    return _to_admin_staff_out(staff)


# --- Weekly schedule -------------------------------------------------------
# `staff_id=None` in the URL would be ambiguous with a real id, so business
# hours are managed through a dedicated endpoint instead (below), separate
# from a specific staff member's hours.


@router.get("/{staff_id}/schedule", response_model=list[DayScheduleOut])
async def get_staff_schedule(
    business_id: uuid.UUID,
    staff_id: uuid.UUID,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> list[DayScheduleOut]:
    await _get_staff_or_404(business_id, staff_id, db)
    return await load_schedule_out(db, business_id=business_id, staff_id=staff_id)


@router.put("/{staff_id}/schedule", response_model=list[DayScheduleOut])
async def set_staff_schedule(
    business_id: uuid.UUID,
    staff_id: uuid.UUID,
    body: WeeklyScheduleUpdate,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> list[DayScheduleOut]:
    await _get_staff_or_404(business_id, staff_id, db)
    await replace_schedule(db, business_id=business_id, staff_id=staff_id, days=body.days)
    db.add(
        AuditLog(
            business_id=business_id,
            actor_user_id=membership.user_id,
            action=AuditAction.SCHEDULE_UPDATED,
            target_type="staff",
            target_id=str(staff_id),
            details={"days": len(body.days)},
        )
    )
    await db.commit()
    return await load_schedule_out(db, business_id=business_id, staff_id=staff_id)


# --- Schedule exceptions (leave / holiday / closure) ------------------------


@router.get("/exceptions", response_model=list[ScheduleExceptionOut])
async def list_exceptions(
    business_id: uuid.UUID,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> list[ScheduleException]:
    result = await db.execute(
        select(ScheduleException)
        .where(ScheduleException.business_id == business_id)
        .order_by(ScheduleException.date)
    )
    return list(result.scalars().all())


@router.post("/exceptions", response_model=ScheduleExceptionOut, status_code=status.HTTP_201_CREATED)
async def create_exception(
    business_id: uuid.UUID,
    body: ScheduleExceptionCreate,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> ScheduleException:
    if body.staff_id is not None:
        await _get_staff_or_404(business_id, body.staff_id, db)
    exc = ScheduleException(business_id=business_id, **body.model_dump())
    db.add(exc)
    await db.commit()
    await db.refresh(exc)
    return exc


@router.delete("/exceptions/{exception_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exception(
    business_id: uuid.UUID,
    exception_id: uuid.UUID,
    membership: BusinessMembership = Depends(_CAN_WRITE),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(ScheduleException).where(
            ScheduleException.id == exception_id, ScheduleException.business_id == business_id
        )
    )
    exc = result.scalar_one_or_none()
    if exc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Schedule exception not found.")
    await db.delete(exc)
    await db.commit()


# --- shared helpers ----------------------------------------------------


async def load_schedule_out(
    db: AsyncSession, *, business_id: uuid.UUID, staff_id: uuid.UUID | None
) -> list[DayScheduleOut]:
    result = await db.execute(
        select(WorkingSchedule)
        .where(WorkingSchedule.business_id == business_id, WorkingSchedule.staff_id == staff_id)
        .options(selectinload(WorkingSchedule.breaks))
        .order_by(WorkingSchedule.weekday)
    )
    out = []
    for ws in result.scalars().all():
        out.append(
            DayScheduleOut(
                weekday=ws.weekday,
                start_time=ws.start_time.strftime("%H:%M"),
                end_time=ws.end_time.strftime("%H:%M"),
                breaks=[
                    {"start_time": b.start_time.strftime("%H:%M"), "end_time": b.end_time.strftime("%H:%M")}
                    for b in ws.breaks
                ],
            )
        )
    return out


async def replace_schedule(
    db: AsyncSession, *, business_id: uuid.UUID, staff_id: uuid.UUID | None, days: list
) -> None:
    # Deleting the WorkingSchedule rows cascades to their breaks (ORM-level
    # cascade="all, delete-orphan" on WorkingSchedule.breaks).
    existing = await db.execute(
        select(WorkingSchedule).where(
            WorkingSchedule.business_id == business_id, WorkingSchedule.staff_id == staff_id
        )
    )
    for ws in existing.scalars().all():
        await db.delete(ws)
    await db.flush()

    for day in days:
        ws = WorkingSchedule(
            business_id=business_id,
            staff_id=staff_id,
            weekday=day.weekday,
            start_time=day.start_time,
            end_time=day.end_time,
        )
        db.add(ws)
        await db.flush()
        for brk in day.breaks:
            db.add(WorkingScheduleBreak(working_schedule_id=ws.id, start_time=brk.start_time, end_time=brk.end_time))
