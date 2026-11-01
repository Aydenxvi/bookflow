"""Shared enums used across models. Plain str Enums so they serialize cleanly through Pydantic too."""
from __future__ import annotations

import enum


class MembershipRole(str, enum.Enum):
    PLATFORM_ADMIN = "platform_admin"
    BUSINESS_OWNER = "business_owner"
    BUSINESS_MANAGER = "business_manager"
    STAFF = "staff"


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class BookingConfirmationMode(str, enum.Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"


class ScheduleExceptionType(str, enum.Enum):
    LEAVE = "leave"
    BREAK = "break"
    HOLIDAY = "holiday"
    CLOSURE = "closure"


class NotificationJobType(str, enum.Enum):
    BOOKING_RECEIVED = "booking_received"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_REJECTED = "booking_rejected"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_RESCHEDULED = "booking_rescheduled"
    REMINDER = "reminder"
    BUSINESS_NEW_BOOKING = "business_new_booking"
    BUSINESS_CANCELLATION = "business_cancellation"
    BUSINESS_RESCHEDULE = "business_reschedule"
    BUSINESS_DAILY_SUMMARY = "business_daily_summary"


class NotificationJobStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RecipientType(str, enum.Enum):
    CUSTOMER = "customer"
    STAFF = "staff"
    BUSINESS = "business"


class AuditAction(str, enum.Enum):
    BOOKING_STATUS_CHANGED = "booking_status_changed"
    BOOKING_CREATED_MANUALLY = "booking_created_manually"
    SERVICE_CREATED = "service_created"
    SERVICE_UPDATED = "service_updated"
    SERVICE_ARCHIVED = "service_archived"
    STAFF_CREATED = "staff_created"
    STAFF_UPDATED = "staff_updated"
    SCHEDULE_UPDATED = "schedule_updated"
    SETTINGS_UPDATED = "settings_updated"
    MEMBERSHIP_CHANGED = "membership_changed"
