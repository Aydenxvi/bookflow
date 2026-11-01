"""Small helpers for building test fixtures without repeating boilerplate."""
from __future__ import annotations

from datetime import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import TokenPayload, create_access_token
from app.models.business import Business, BusinessMembership, BusinessSettings
from app.models.enums import BookingConfirmationMode, MembershipRole
from app.models.policy import BookingPolicy
from app.models.schedule import WorkingSchedule
from app.models.service import Service, StaffService
from app.models.staff import Staff
from app.models.user import TelegramIdentity, User


async def make_business(
    db: AsyncSession, *, timezone: str = "Europe/Istanbul", slug: str = "test-biz", **overrides
) -> Business:
    defaults = dict(name="Test Biz", currency="USD", is_active=True, is_demo=True)
    defaults.update(overrides)
    business = Business(slug=slug, timezone=timezone, **defaults)
    db.add(business)
    await db.flush()
    return business


async def make_policy(db: AsyncSession, business: Business, **overrides) -> BookingPolicy:
    defaults = dict(
        confirmation_mode=BookingConfirmationMode.AUTOMATIC,
        slot_interval_minutes=15,
        buffer_minutes=0,
        min_lead_time_minutes=0,
        max_advance_days=60,
        cancellation_window_minutes=60,
        reschedule_window_minutes=60,
    )
    defaults.update(overrides)
    policy = BookingPolicy(business_id=business.id, **defaults)
    db.add(policy)
    await db.flush()
    return policy


async def make_service(db: AsyncSession, business: Business, *, duration_minutes: int = 30, **overrides) -> Service:
    defaults = dict(name="Test Service", price_minor_units=1000, currency="USD", is_active=True)
    defaults.update(overrides)
    service = Service(business_id=business.id, duration_minutes=duration_minutes, **defaults)
    db.add(service)
    await db.flush()
    return service


async def make_staff(db: AsyncSession, business: Business, **overrides) -> Staff:
    defaults = dict(display_name="Test Staff", is_active=True)
    defaults.update(overrides)
    staff = Staff(business_id=business.id, **defaults)
    db.add(staff)
    await db.flush()
    return staff


async def link_staff_service(db: AsyncSession, staff: Staff, service: Service) -> None:
    db.add(StaffService(staff_id=staff.id, service_id=service.id))
    await db.flush()


async def make_all_week_schedule(
    db: AsyncSession, business: Business, staff: Staff | None, start: time = time(9, 0), end: time = time(18, 0)
) -> None:
    for weekday in range(7):
        db.add(
            WorkingSchedule(
                business_id=business.id, staff_id=staff.id if staff else None,
                weekday=weekday, start_time=start, end_time=end,
            )
        )
    await db.flush()


async def make_user(db: AsyncSession, **overrides) -> User:
    defaults = dict(first_name="Test", is_demo=True)
    defaults.update(overrides)
    user = User(**defaults)
    db.add(user)
    await db.flush()
    return user


async def make_membership(
    db: AsyncSession, business: Business, user: User, *, role: MembershipRole = MembershipRole.BUSINESS_OWNER
) -> BusinessMembership:
    membership = BusinessMembership(business_id=business.id, user_id=user.id, role=role)
    db.add(membership)
    await db.flush()
    return membership


async def make_telegram_identity(db: AsyncSession, user: User, *, telegram_user_id: int, **overrides) -> TelegramIdentity:
    defaults = dict(is_bot_blocked=False)
    defaults.update(overrides)
    identity = TelegramIdentity(user_id=user.id, telegram_user_id=telegram_user_id, **defaults)
    db.add(identity)
    await db.flush()
    return identity


async def make_settings(db: AsyncSession, business: Business, **overrides) -> BusinessSettings:
    defaults = dict(
        notify_business_on_new_booking=True,
        notify_business_on_cancellation=True,
        notify_business_daily_summary=False,
    )
    defaults.update(overrides)
    settings = BusinessSettings(business_id=business.id, **defaults)
    db.add(settings)
    await db.flush()
    return settings


def auth_header(user: User) -> dict[str, str]:
    """A real BookFlow JWT for `user`, as the `Authorization` header an
    authenticated request would send — exercises the actual token
    decode/lookup path (app/core/authz.py), not a bypassed test shortcut."""
    settings = get_settings()
    token = create_access_token(TokenPayload(user_id=user.id, is_demo=bool(user.is_demo)), settings)
    return {"Authorization": f"Bearer {token}"}
