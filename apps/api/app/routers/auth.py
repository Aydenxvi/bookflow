"""Authentication: real Telegram initData verification, and a separate
clearly-scoped browser demo-mode path (spec sections 5 & 19)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.authz import get_current_user
from app.core.config import Settings, get_settings
from app.core.security import TokenPayload, create_access_token
from app.core.telegram_auth import InvalidInitDataError, verify_init_data
from app.db.session import get_db
from app.models.business import Business, BusinessMembership
from app.models.enums import MembershipRole
from app.models.user import TelegramIdentity, User
from app.schemas.admin import MembershipOut, MeOut
from app.schemas.auth import DemoAuthRequest, TelegramAuthRequest, TokenOut

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/telegram", response_model=TokenOut)
async def auth_telegram(
    body: TelegramAuthRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenOut:
    try:
        verified = verify_init_data(body.init_data, settings)
    except InvalidInitDataError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    result = await db.execute(
        select(TelegramIdentity).where(TelegramIdentity.telegram_user_id == verified.user.id)
    )
    identity = result.scalar_one_or_none()

    if identity is None:
        user = User(first_name=verified.user.first_name, last_name=verified.user.last_name, is_demo=False)
        db.add(user)
        await db.flush()
        identity = TelegramIdentity(
            user_id=user.id,
            telegram_user_id=verified.user.id,
            username=verified.user.username,
            language_code=verified.user.language_code,
            photo_url=verified.user.photo_url,
        )
        db.add(identity)
    else:
        user = await db.get(User, identity.user_id)
        # Keep basic profile fields fresh in case the person changed their
        # Telegram name/username since we last saw them.
        user.first_name = verified.user.first_name
        user.last_name = verified.user.last_name
        identity.username = verified.user.username
        identity.language_code = verified.user.language_code
        identity.photo_url = verified.user.photo_url
        identity.is_bot_blocked = False

    await db.commit()

    token = create_access_token(TokenPayload(user_id=user.id, is_demo=False), settings)
    return TokenOut(access_token=token, is_demo=False)


@router.post("/demo", response_model=TokenOut)
async def auth_demo(
    body: DemoAuthRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenOut:
    if not settings.demo_mode_enabled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Demo mode is not enabled on this server.")

    slug = body.business_slug or settings.demo_business_slug
    result = await db.execute(select(Business).where(Business.slug == slug, Business.is_demo.is_(True)))
    business = result.scalar_one_or_none()
    if business is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Demo business not found.")

    # Every demo-mode call gets a fresh synthetic demo user. This keeps demo
    # sessions fully isolated from each other and from real customers; it's
    # deliberately cheap (no persistent "demo login") since the whole point
    # is frictionless, account-free exploration.
    user = User(first_name="Demo Visitor", is_demo=True)
    db.add(user)
    await db.commit()

    token = create_access_token(
        TokenPayload(user_id=user.id, is_demo=True, demo_business_id=business.id), settings
    )
    return TokenOut(access_token=token, is_demo=True)


@router.post("/demo-admin", response_model=TokenOut)
async def auth_demo_admin(
    body: DemoAuthRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenOut:
    """Browser demo mode for the *admin* dashboard (spec section 19: "a sample
    admin dashboard", explorable without a real Telegram account or a real
    business-owner relationship). Issues a fresh synthetic user with a
    BUSINESS_OWNER membership on the demo business — isolated per call, same
    as /demo, so concurrent demo visitors never collide."""
    if not settings.demo_mode_enabled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Demo mode is not enabled on this server.")

    slug = body.business_slug or settings.demo_business_slug
    result = await db.execute(select(Business).where(Business.slug == slug, Business.is_demo.is_(True)))
    business = result.scalar_one_or_none()
    if business is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Demo business not found.")

    user = User(first_name="Demo Owner", is_demo=True)
    db.add(user)
    await db.flush()
    db.add(BusinessMembership(business_id=business.id, user_id=user.id, role=MembershipRole.BUSINESS_OWNER))
    await db.commit()

    token = create_access_token(
        TokenPayload(user_id=user.id, is_demo=True, demo_business_id=business.id), settings
    )
    return TokenOut(access_token=token, is_demo=True)


@router.get("/me", response_model=MeOut)
async def get_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> MeOut:
    """Who am I, and which businesses can I administer? The admin frontend
    uses this right after login to decide what to show — never trusts the
    client to say which business/role it's acting as."""
    result = await db.execute(
        select(BusinessMembership)
        .where(BusinessMembership.user_id == user.id)
        .options(selectinload(BusinessMembership.business))
    )
    memberships = result.scalars().all()
    return MeOut(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        is_demo=user.is_demo,
        is_platform_admin=user.is_platform_admin,
        memberships=[
            MembershipOut(
                business_id=m.business_id,
                business_slug=m.business.slug,
                business_name=m.business.name,
                role=m.role,
            )
            for m in memberships
        ],
    )
