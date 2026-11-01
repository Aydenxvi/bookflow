"""Telegram WebApp `initData` verification.

Implements the exact algorithm Telegram documents
(https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app):

1. Parse initData as a query string.
2. Remove the `hash` field; join the remaining `key=value` pairs sorted by
   key, separated by "\n", to form the data-check-string.
3. secret_key = HMAC_SHA256(key=b"WebAppData", msg=bot_token)
4. expected_hash = HMAC_SHA256(key=secret_key, msg=data_check_string).hexdigest()
5. Compare to the provided hash using a constant-time comparison.
6. Reject if `auth_date` is older than the configured freshness window.

`initDataUnsafe` (the client-side parsed object) is NEVER trusted — only this
server-side verification result is used to establish identity.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

from app.core.config import Settings


class InvalidInitDataError(Exception):
    """Raised when initData fails signature or freshness validation."""


@dataclass(frozen=True)
class TelegramUser:
    id: int
    first_name: str
    last_name: str | None
    username: str | None
    language_code: str | None
    photo_url: str | None


@dataclass(frozen=True)
class VerifiedInitData:
    user: TelegramUser
    auth_date: int
    start_param: str | None


def _build_data_check_string(pairs: list[tuple[str, str]]) -> str:
    filtered = [(k, v) for k, v in pairs if k != "hash"]
    filtered.sort(key=lambda kv: kv[0])
    return "\n".join(f"{k}={v}" for k, v in filtered)


def verify_init_data(init_data: str, settings: Settings) -> VerifiedInitData:
    if not settings.telegram_bot_token:
        raise InvalidInitDataError(
            "Telegram authentication is not configured on this server (no bot token set)."
        )
    if not init_data:
        raise InvalidInitDataError("initData is empty.")

    pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=False)
    pair_dict = dict(pairs)

    provided_hash = pair_dict.get("hash")
    if not provided_hash:
        raise InvalidInitDataError("initData is missing the hash field.")

    data_check_string = _build_data_check_string(pairs)

    secret_key = hmac.new(b"WebAppData", settings.telegram_bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, provided_hash):
        raise InvalidInitDataError("initData signature verification failed.")

    auth_date_raw = pair_dict.get("auth_date")
    if not auth_date_raw or not auth_date_raw.isdigit():
        raise InvalidInitDataError("initData is missing a valid auth_date.")
    auth_date = int(auth_date_raw)

    age = time.time() - auth_date
    if age > settings.telegram_init_data_max_age_seconds:
        raise InvalidInitDataError("initData has expired; please reopen the Mini App.")
    if age < -60:  # allow a little clock skew, but reject anything from "the future"
        raise InvalidInitDataError("initData auth_date is implausibly in the future.")

    user_raw = pair_dict.get("user")
    if not user_raw:
        raise InvalidInitDataError("initData is missing the user field.")
    try:
        user_json = json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise InvalidInitDataError("initData user field is not valid JSON.") from exc

    try:
        telegram_user = TelegramUser(
            id=int(user_json["id"]),
            first_name=str(user_json["first_name"]),
            last_name=user_json.get("last_name"),
            username=user_json.get("username"),
            language_code=user_json.get("language_code"),
            photo_url=user_json.get("photo_url"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidInitDataError("initData user field is missing required keys.") from exc

    return VerifiedInitData(
        user=telegram_user,
        auth_date=auth_date,
        start_param=pair_dict.get("start_param"),
    )
