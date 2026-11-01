"""JWT issuance/verification for BookFlow's own session tokens.

Telegram initData (or demo-mode) authentication happens once, at /auth/*;
the result is exchanged for a short-lived BookFlow JWT that every other
endpoint actually checks. This keeps the rest of the API from having to
re-verify Telegram signatures on every request.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.core.config import Settings


class InvalidTokenError(Exception):
    pass


@dataclass(frozen=True)
class TokenPayload:
    user_id: uuid.UUID
    is_demo: bool
    demo_business_id: uuid.UUID | None = None


def create_access_token(payload: TokenPayload, settings: Settings) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": str(payload.user_id),
        "is_demo": payload.is_demo,
        "demo_business_id": str(payload.demo_business_id) if payload.demo_business_id else None,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_ttl_minutes),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> TokenPayload:
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise InvalidTokenError("Invalid or expired token.") from exc

    try:
        user_id = uuid.UUID(claims["sub"])
    except (KeyError, ValueError) as exc:
        raise InvalidTokenError("Token is missing a valid subject.") from exc

    demo_business_id_raw = claims.get("demo_business_id")
    demo_business_id = uuid.UUID(demo_business_id_raw) if demo_business_id_raw else None

    return TokenPayload(
        user_id=user_id,
        is_demo=bool(claims.get("is_demo", False)),
        demo_business_id=demo_business_id,
    )
