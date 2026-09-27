"""Validates Telegram Mini App `initData` — the official algorithm
(https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app):

    secret_key = HMAC_SHA256(key="WebAppData", msg=bot_token)
    data_check_string = "\n".join(sorted(f"{k}={v}" for k, v in fields if k != "hash"))
    expected_hash = HMAC_SHA256(key=secret_key, msg=data_check_string).hexdigest()

`initDataUnsafe` (the parsed-but-unverified object the frontend already
has via window.Telegram.WebApp) must never be trusted for identity —
this is the actual verification step a future bot-auth endpoint needs
before treating any field in it (user id, username, ...) as real. Not
wired into any router yet — this is the utility that endpoint will call,
prepared ahead of the Telegram BOT project's own work.

TELEGRAM_BOT_TOKEN is read from settings/environment, never hardcoded,
never sent to the frontend. Raises RuntimeError if it isn't configured,
since silently treating unverifiable data as valid would be worse than
failing loudly.
"""

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from app.core.config import settings


def validate_telegram_init_data(
    init_data: str,
    max_age_seconds: int | None = 86400,
) -> dict | None:
    """Returns the parsed initData fields (with `user`/`receiver`/`chat`
    JSON-decoded) if the hash is valid and not stale, else None. Never
    raises for malformed/tampered input — only for a missing bot token,
    which is a configuration error, not an attacker-controlled input."""

    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured — cannot validate Telegram initData."
        )

    try:
        pairs = parse_qsl(init_data, strict_parsing=True)
    except ValueError:
        return None

    fields = dict(pairs)
    received_hash = fields.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))

    secret_key = hmac.new(b"WebAppData", settings.TELEGRAM_BOT_TOKEN.encode("utf-8"), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        return None

    if max_age_seconds is not None:
        auth_date = fields.get("auth_date")
        if auth_date is None or not auth_date.isdigit():
            return None
        if time.time() - int(auth_date) > max_age_seconds:
            return None

    for json_field in ("user", "receiver", "chat"):
        if json_field in fields:
            try:
                fields[json_field] = json.loads(fields[json_field])
            except (json.JSONDecodeError, TypeError):
                return None

    return fields
