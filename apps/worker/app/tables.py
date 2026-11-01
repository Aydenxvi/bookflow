"""Thin SQLAlchemy Core views onto tables apps/api's Alembic migrations own.

This worker is a separate deployable service (its own pyproject.toml/
Dockerfile, built from its own directory per docker-compose.yml, same
pattern as apps/bot) — it does not import apps/api's ORM package. Rather
than reach across the service boundary, it declares plain Core `Table`
objects for exactly the columns it reads or writes, mapped onto the same
tables apps/api's models already define and Alembic already created. This
file owns no schema and runs no migrations; it must stay in sync with
apps/api/app/models/{notification,booking,service,staff,business,user}.py
by hand if those ever change shape — there is no reflection or shared import
to do that automatically, which is a deliberate simplicity trade-off for a
service this small, not an oversight.

Enum columns (job_type, recipient_type, status, booking status, membership
role) are declared as SQLAlchemy's Enum(..., native_enum=False) stores them:
as the Python Enum member's NAME (e.g. "BOOKING_CONFIRMED", "PENDING"), not
its lower-case `.value` — confirmed against the real columns apps/api's
hooks (app/services/notifications.py) actually insert. The *Values classes
below mirror apps/api/app/models/enums.py's member names, not its values.
"""
from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID

metadata = MetaData()


class JobStatus:
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RecipientType:
    CUSTOMER = "CUSTOMER"
    STAFF = "STAFF"
    BUSINESS = "BUSINESS"


class JobType:
    BOOKING_RECEIVED = "BOOKING_RECEIVED"
    BOOKING_CONFIRMED = "BOOKING_CONFIRMED"
    BOOKING_REJECTED = "BOOKING_REJECTED"
    BOOKING_CANCELLED = "BOOKING_CANCELLED"
    BOOKING_RESCHEDULED = "BOOKING_RESCHEDULED"
    REMINDER = "REMINDER"
    BUSINESS_NEW_BOOKING = "BUSINESS_NEW_BOOKING"
    BUSINESS_CANCELLATION = "BUSINESS_CANCELLATION"
    BUSINESS_RESCHEDULE = "BUSINESS_RESCHEDULE"
    BUSINESS_DAILY_SUMMARY = "BUSINESS_DAILY_SUMMARY"


class MembershipRole:
    BUSINESS_OWNER = "BUSINESS_OWNER"
    BUSINESS_MANAGER = "BUSINESS_MANAGER"


notification_jobs = Table(
    "notification_jobs",
    metadata,
    Column("id", UUID, primary_key=True),
    # No ForeignKey() here deliberately: apps/api's Alembic migration owns
    # referential integrity for these tables (including the ON DELETE CASCADE
    # that makes a notification_job outliving its booking impossible in
    # production); this worker only reads/writes rows, it doesn't enforce
    # the schema's relationships.
    Column("business_id", UUID, nullable=False),
    Column("booking_id", UUID, nullable=True),
    Column("job_type", String(32), nullable=False),
    Column("recipient_type", String(16), nullable=False),
    Column("recipient_telegram_user_id", BigInteger, nullable=True),
    Column("payload", JSON, nullable=False),
    Column("status", String(16), nullable=False),
    Column("attempts", Integer, nullable=False),
    Column("last_error", String(1000), nullable=True),
    Column("scheduled_for", DateTime(timezone=True), nullable=False),
    Column("sent_at", DateTime(timezone=True), nullable=True),
    Column("dedupe_key", String(200), nullable=False, unique=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

bookings = Table(
    "bookings",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("business_id", UUID, nullable=False),
    Column("staff_id", UUID, nullable=False),
    Column("service_id", UUID, nullable=False),
    Column("customer_user_id", UUID, nullable=False),
    Column("starts_at", DateTime(timezone=True), nullable=False),
    Column("ends_at", DateTime(timezone=True), nullable=False),
    Column("status", String(16), nullable=False),
    Column("price_minor_units_snapshot", Integer, nullable=False),
    Column("currency_snapshot", String(8), nullable=False),
    Column("is_demo", Boolean, nullable=False),
)

services = Table(
    "services",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("name", String(160), nullable=False),
)

staff = Table(
    "staff",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("display_name", String(160), nullable=False),
)

businesses = Table(
    "businesses",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("name", String(160), nullable=False),
    Column("timezone", String(64), nullable=False),
    Column("currency", String(8), nullable=False),
    Column("is_demo", Boolean, nullable=False),
)

users = Table(
    "users",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("first_name", String(120), nullable=False),
    Column("last_name", String(120), nullable=True),
)

telegram_identities = Table(
    "telegram_identities",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("user_id", UUID, nullable=False),
    Column("telegram_user_id", BigInteger, nullable=False),
    Column("is_bot_blocked", Boolean, nullable=False),
)

business_memberships = Table(
    "business_memberships",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("business_id", UUID, nullable=False),
    Column("user_id", UUID, nullable=False),
    Column("role", String(32), nullable=False),
)

business_settings = Table(
    "business_settings",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("business_id", UUID, nullable=False, unique=True),
    Column("notify_business_on_new_booking", Boolean, nullable=False),
    Column("notify_business_on_cancellation", Boolean, nullable=False),
    Column("notify_business_daily_summary", Boolean, nullable=False),
)
