"""Schemas for the business admin dashboard (spec sections 8-10).

Kept in a separate module from the customer-facing schemas in business.py /
service.py / staff.py because the shapes genuinely differ: admin endpoints
need to see inactive/archived rows, write access, and fields customers never
see (e.g. a service's currency being editable, not just displayable).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator

from app.models.enums import (
    BookingConfirmationMode,
    BookingStatus,
    MembershipRole,
    ScheduleExceptionType,
)
from app.schemas.common import ORMModel
from app.schemas.service import ServiceOut
from app.schemas.staff import StaffOut


class MembershipOut(BaseModel):
    business_id: uuid.UUID
    business_slug: str
    business_name: str
    role: MembershipRole


class BusinessProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    logo_url: str | None = Field(default=None, max_length=512)
    cover_image_url: str | None = Field(default=None, max_length=512)
    address: str | None = Field(default=None, max_length=300)
    contact_phone: str | None = Field(default=None, max_length=32)
    contact_email: str | None = Field(default=None, max_length=160)
    timezone: str | None = Field(default=None, max_length=64)
    currency: str | None = Field(default=None, min_length=3, max_length=8)

    @field_validator("timezone")
    @classmethod
    def _valid_iana_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"'{value}' is not a known IANA timezone (e.g. 'Europe/Istanbul').") from exc
        return value


class MeOut(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str | None
    is_demo: bool
    is_platform_admin: bool
    memberships: list[MembershipOut]


# --- Services --------------------------------------------------------------


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    category: str | None = Field(default=None, max_length=80)
    image_url: str | None = Field(default=None, max_length=512)
    duration_minutes: int = Field(gt=0, le=600)
    price_minor_units: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=8)


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    category: str | None = Field(default=None, max_length=80)
    image_url: str | None = Field(default=None, max_length=512)
    duration_minutes: int | None = Field(default=None, gt=0, le=600)
    price_minor_units: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=8)
    is_active: bool | None = None


class AdminServiceOut(ORMModel):
    id: uuid.UUID
    name: str
    description: str | None
    category: str | None
    image_url: str | None
    duration_minutes: int
    price_minor_units: int
    currency: str
    is_active: bool


# --- Staff -------------------------------------------------------------


class StaffCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=160)
    photo_url: str | None = Field(default=None, max_length=512)
    specialization: str | None = Field(default=None, max_length=160)
    bio: str | None = Field(default=None, max_length=1000)
    service_ids: list[uuid.UUID] = Field(default_factory=list)


class StaffUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=160)
    photo_url: str | None = Field(default=None, max_length=512)
    specialization: str | None = Field(default=None, max_length=160)
    bio: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None


class StaffServicesUpdate(BaseModel):
    service_ids: list[uuid.UUID]


class AdminStaffOut(ORMModel):
    id: uuid.UUID
    display_name: str
    photo_url: str | None
    specialization: str | None
    bio: str | None
    is_active: bool
    service_ids: list[uuid.UUID]


# --- Schedules ---------------------------------------------------------


class BreakIn(BaseModel):
    start_time: time
    end_time: time


class DayScheduleIn(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    breaks: list[BreakIn] = Field(default_factory=list)


class WeeklyScheduleUpdate(BaseModel):
    """Replaces the *entire* weekly schedule for the target (business or one
    staff member) with exactly these days — any weekday left out is treated
    as closed/off that day."""

    days: list[DayScheduleIn]


class BreakOut(BaseModel):
    start_time: str
    end_time: str


class DayScheduleOut(BaseModel):
    weekday: int
    start_time: str
    end_time: str
    breaks: list[BreakOut]


class ScheduleExceptionCreate(BaseModel):
    staff_id: uuid.UUID | None = None  # None => business-wide (holiday/closure)
    date: date
    start_time: time | None = None  # None+None => all day
    end_time: time | None = None
    type: ScheduleExceptionType
    note: str | None = Field(default=None, max_length=300)


class ScheduleExceptionOut(ORMModel):
    id: uuid.UUID
    staff_id: uuid.UUID | None
    date: date
    start_time: time | None
    end_time: time | None
    type: ScheduleExceptionType
    note: str | None


# --- Booking policy ------------------------------------------------------


class BookingPolicyOut(ORMModel):
    confirmation_mode: BookingConfirmationMode
    slot_interval_minutes: int
    buffer_minutes: int
    min_lead_time_minutes: int
    max_advance_days: int
    cancellation_window_minutes: int
    reschedule_window_minutes: int
    reminder_offsets_minutes: list[int]


class BookingPolicyUpdate(BaseModel):
    confirmation_mode: BookingConfirmationMode | None = None
    slot_interval_minutes: int | None = Field(default=None, gt=0, le=120)
    buffer_minutes: int | None = Field(default=None, ge=0, le=240)
    min_lead_time_minutes: int | None = Field(default=None, ge=0)
    max_advance_days: int | None = Field(default=None, gt=0, le=365)
    cancellation_window_minutes: int | None = Field(default=None, ge=0)
    reschedule_window_minutes: int | None = Field(default=None, ge=0)
    reminder_offsets_minutes: list[int] | None = None


# --- Admin bookings / calendar ------------------------------------------


class ManualBookingCreate(BaseModel):
    """A booking entered by staff on a customer's behalf (walk-in, phone call).

    There's no customer account system yet, so a lightweight guest User is
    created from the supplied name — see app/routers/admin_bookings.py.
    """

    service_id: uuid.UUID
    staff_id: uuid.UUID | None = None  # None => "any available", same as customer flow
    starts_at: datetime
    customer_name: str = Field(min_length=1, max_length=160)
    customer_phone: str | None = Field(default=None, max_length=32)
    customer_notes: str | None = Field(default=None, max_length=1000)


class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    note: str | None = Field(default=None, max_length=300)


class AdminCustomerOut(BaseModel):
    id: uuid.UUID
    display_name: str
    phone: str | None
    is_demo: bool


class AdminBookingOut(ORMModel):
    id: uuid.UUID
    status: BookingStatus
    starts_at: datetime
    ends_at: datetime
    price_minor_units_snapshot: int
    currency_snapshot: str
    duration_minutes_snapshot: int
    customer_notes: str | None
    cancel_reason: str | None
    is_demo: bool
    service: ServiceOut
    staff: StaffOut
    customer: AdminCustomerOut


# --- Dashboard -----------------------------------------------------------


class ServiceCountOut(BaseModel):
    service_id: uuid.UUID
    name: str
    count: int


class StaffCountOut(BaseModel):
    staff_id: uuid.UUID
    display_name: str
    count: int


class DashboardSummaryOut(BaseModel):
    today_count: int
    upcoming_count: int
    completed_count: int
    cancelled_count: int
    revenue_minor_units: int
    revenue_currency: str
    popular_services: list[ServiceCountOut]
    staff_workload: list[StaffCountOut]
