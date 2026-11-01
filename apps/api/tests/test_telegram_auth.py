"""Validates Telegram initData verification: correct signatures accepted,
tampered/missing/stale data rejected. This directly covers spec section 20's
"Telegram authentication validation" and "Invalid authentication rejection"
requirements.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from app.core.config import Settings
from app.core.telegram_auth import InvalidInitDataError, verify_init_data

BOT_TOKEN = "test-bot-token-for-signing"


def _settings(**overrides) -> Settings:
    return Settings(telegram_bot_token=BOT_TOKEN, **overrides)


def _build_init_data(user: dict, auth_date: int, bot_token: str = BOT_TOKEN, tamper: bool = False) -> str:
    params = {
        "user": json.dumps(user, separators=(",", ":")),
        "auth_date": str(auth_date),
        "query_id": "AAFake",
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if tamper:
        params["user"] = json.dumps({**user, "id": user["id"] + 1}, separators=(",", ":"))
    params["hash"] = computed_hash
    return urlencode(params)


def test_valid_init_data_is_accepted():
    user = {"id": 123456789, "first_name": "Ada", "username": "ada_lovelace", "language_code": "en"}
    init_data = _build_init_data(user, auth_date=int(time.time()))

    result = verify_init_data(init_data, _settings())

    assert result.user.id == 123456789
    assert result.user.first_name == "Ada"
    assert result.user.username == "ada_lovelace"


def test_tampered_payload_is_rejected():
    user = {"id": 123456789, "first_name": "Ada"}
    init_data = _build_init_data(user, auth_date=int(time.time()), tamper=True)

    with pytest.raises(InvalidInitDataError):
        verify_init_data(init_data, _settings())


def test_wrong_bot_token_is_rejected():
    user = {"id": 1, "first_name": "Ada"}
    init_data = _build_init_data(user, auth_date=int(time.time()), bot_token="a-different-bot-token")

    with pytest.raises(InvalidInitDataError):
        verify_init_data(init_data, _settings())


def test_stale_auth_date_is_rejected():
    user = {"id": 1, "first_name": "Ada"}
    stale_auth_date = int(time.time()) - 999_999  # way older than the freshness window
    init_data = _build_init_data(user, auth_date=stale_auth_date)

    with pytest.raises(InvalidInitDataError, match="expired"):
        verify_init_data(init_data, _settings(telegram_init_data_max_age_seconds=86400))


def test_missing_hash_is_rejected():
    init_data = "user=%7B%22id%22%3A1%2C%22first_name%22%3A%22Ada%22%7D&auth_date=123"
    with pytest.raises(InvalidInitDataError, match="hash"):
        verify_init_data(init_data, _settings())


def test_no_bot_token_configured_rejects_everything():
    user = {"id": 1, "first_name": "Ada"}
    init_data = _build_init_data(user, auth_date=int(time.time()))
    with pytest.raises(InvalidInitDataError):
        verify_init_data(init_data, Settings(telegram_bot_token=None))
