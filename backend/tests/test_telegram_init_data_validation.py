"""Tests for validate_telegram_init_data (backend/app/core/security/
telegram.py) — the HMAC verification a future BOT<->WEB auth endpoint
will call. Builds a real initData string the same way Telegram's own
client does (per https://core.telegram.org/bots/webapps#validating-data-
received-via-the-mini-app) so this proves the algorithm itself is
correct, not just that some mock returns True.
"""

import hashlib
import hmac
import json
import time
import unittest
from urllib.parse import urlencode

from app.core.config import settings
from app.core.security.telegram import validate_telegram_init_data

FAKE_BOT_TOKEN = "123456:FAKE-BOT-TOKEN-FOR-TESTS-ONLY"


def _build_init_data(fields: dict, bot_token: str = FAKE_BOT_TOKEN) -> str:
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    real_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return urlencode({**fields, "hash": real_hash})


class TestValidateTelegramInitData(unittest.TestCase):
    def setUp(self):
        self._original_token = settings.TELEGRAM_BOT_TOKEN
        settings.TELEGRAM_BOT_TOKEN = FAKE_BOT_TOKEN

    def tearDown(self):
        settings.TELEGRAM_BOT_TOKEN = self._original_token

    def test_valid_init_data_is_accepted_and_user_is_json_decoded(self):
        user = {"id": 12345, "first_name": "Zayniddin", "username": "zayniddin"}
        init_data = _build_init_data(
            {"auth_date": str(int(time.time())), "query_id": "abc", "user": json.dumps(user)}
        )

        result = validate_telegram_init_data(init_data)

        self.assertIsNotNone(result)
        self.assertEqual(result["user"], user)

    def test_tampered_field_is_rejected(self):
        init_data = _build_init_data({"auth_date": str(int(time.time())), "user": json.dumps({"id": 1})})
        # Flip the user id after signing — the hash no longer matches.
        tampered = init_data.replace("%22id%22%3A+1", "%22id%22%3A+999")

        result = validate_telegram_init_data(tampered)

        self.assertIsNone(result)

    def test_wrong_bot_token_is_rejected(self):
        init_data = _build_init_data({"auth_date": str(int(time.time()))}, bot_token="different-token")

        result = validate_telegram_init_data(init_data)

        self.assertIsNone(result)

    def test_stale_auth_date_is_rejected(self):
        two_days_ago = int(time.time()) - 2 * 86400
        init_data = _build_init_data({"auth_date": str(two_days_ago)})

        result = validate_telegram_init_data(init_data, max_age_seconds=86400)

        self.assertIsNone(result)

    def test_max_age_none_skips_the_freshness_check(self):
        two_days_ago = int(time.time()) - 2 * 86400
        init_data = _build_init_data({"auth_date": str(two_days_ago)})

        result = validate_telegram_init_data(init_data, max_age_seconds=None)

        self.assertIsNotNone(result)

    def test_missing_hash_is_rejected(self):
        result = validate_telegram_init_data("auth_date=123&query_id=abc")

        self.assertIsNone(result)

    def test_malformed_init_data_does_not_raise(self):
        result = validate_telegram_init_data("not a valid query string=&&=")

        self.assertIsNone(result)

    def test_missing_bot_token_raises_runtime_error(self):
        settings.TELEGRAM_BOT_TOKEN = ""

        with self.assertRaises(RuntimeError):
            validate_telegram_init_data("hash=x")


if __name__ == "__main__":
    unittest.main()
