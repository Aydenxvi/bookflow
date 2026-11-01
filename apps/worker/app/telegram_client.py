"""Sending a message over Telegram's raw Bot API.

Only one call type is needed (sendMessage), so this talks to
https://api.telegram.org directly via httpx rather than pulling in aiogram
(which apps/bot already uses for its own, different job: launching the Mini
App from a chat). Never run against a real token in this environment — see
README.md.
"""
from __future__ import annotations

import httpx

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramSendError(Exception):
    """Telegram's API rejected the send (bad token, blocked chat, bad request, ...)."""


async def send_message(
    *, bot_token: str, chat_id: int, text: str, client: httpx.AsyncClient | None = None
) -> None:
    """POST sendMessage. Raises TelegramSendError on anything but a 2xx response
    with ok: true, including network failures — callers decide retry/backoff."""
    url = f"{TELEGRAM_API_BASE}/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}

    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=10.0)
    try:
        try:
            response = await client.post(url, json=payload)
        except httpx.HTTPError as exc:
            raise TelegramSendError(f"network error calling Telegram: {exc}") from exc

        try:
            body = response.json()
        except ValueError:
            body = {}

        if response.status_code >= 400 or not body.get("ok", False):
            description = body.get("description", response.text[:200])
            raise TelegramSendError(f"Telegram API error ({response.status_code}): {description}")
    finally:
        if owns_client:
            await client.aclose()
