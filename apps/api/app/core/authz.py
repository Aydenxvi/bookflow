"""Authentication/authorization FastAPI dependencies.

`get_current_user` is the only place a request's identity is established —
from the BookFlow JWT (see security.py), never from any client-supplied
body field. Role/business-scope dependencies build on top of it so routers
never have to re-derive "is this person allowed to touch this row".
"""
from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import InvalidTokenError, TokenPayload, decode_access_token
from app.db.session import get_db
from app.models.business import BusinessMembership
from app.models.enums import MembershipRole
from app.models.user import User

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/demo", auto_error=False)


async def get_current_token(
    token: str | None = Depends(_oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> TokenPayload:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing authentication token.")
    try:
        return decode_access_token(token, settings)
    except InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc


async def get_current_user(
    token_payload: TokenPayload = Depends(get_current_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await db.get(User, token_payload.user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User for this token no longer exists.")
    return user


class RequireBusinessRole:
    """Dependency factory: require the current user to hold one of `roles`
    within the business identified by the `business_id` path parameter.

    Usage: `Depends(RequireBusinessRole(MembershipRole.BUSINESS_OWNER, MembershipRole.BUSINESS_MANAGER))`
    """

    def __init__(self, *roles: MembershipRole):
        self.roles = set(roles)

    async def __call__(
        self,
        business_id: uuid.UUID,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> BusinessMembership:
        if user.is_platform_admin:
            # Platform admins bypass per-business membership checks entirely,
            # but we still need a membership-shaped object for callers that
            # read `.role` off the result — synthesize one, unsaved.
            return BusinessMembership(business_id=business_id, user_id=user.id, role=MembershipRole.PLATFORM_ADMIN)

        result = await db.execute(
            select(BusinessMembership).where(
                BusinessMembership.business_id == business_id,
                BusinessMembership.user_id == user.id,
            )
        )
        membership = result.scalar_one_or_none()
        if membership is None or membership.role not in self.roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "You do not have the required role for this business."
            )
        return membership


async def require_demo_or_real_customer(user: User = Depends(get_current_user)) -> User:
    """Any authenticated user (real Telegram or demo) may use the customer-facing
    booking endpoints. This dependency exists mainly as a readable name at the
    router level and a single place to add future customer-specific checks."""
    return user
