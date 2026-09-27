"""Tests for POST /auth/telegram (app/api/auth/router.py) and
get_or_create_telegram_user (app/services/auth/service.py) — the new
Telegram Mini App login method, added alongside (never instead of)
POST /auth/login. Same mocked-collaborators style as every other
service-level test here (see test_login_email_case_insensitive.py) —
no real DB in this suite.
"""

import unittest
from unittest.mock import MagicMock

from app.services.auth.service import get_or_create_telegram_user


class TestGetOrCreateTelegramUser(unittest.TestCase):
    def test_existing_telegram_user_is_found_not_duplicated(self):
        mock_db = MagicMock()
        existing_user = MagicMock(telegram_id=12345)
        mock_db.scalar.return_value = existing_user

        result = get_or_create_telegram_user(mock_db, {"id": 12345, "first_name": "Zayniddin"})

        self.assertIs(result, existing_user)
        mock_db.add.assert_not_called()

    def test_new_telegram_user_is_created_with_random_password(self):
        mock_db = MagicMock()
        # First scalar() call: lookup by telegram_id -> not found.
        # Second scalar() call: username-uniqueness check -> not found.
        mock_db.scalar.side_effect = [None, None]

        result = get_or_create_telegram_user(
            mock_db, {"id": 999, "first_name": "Anna", "last_name": "Muster", "username": "anna_m"}
        )

        mock_db.add.assert_called_once()
        created_user = mock_db.add.call_args[0][0]
        self.assertEqual(created_user.telegram_id, 999)
        self.assertEqual(created_user.username, "anna_m")
        self.assertEqual(created_user.first_name, "Anna")
        self.assertEqual(created_user.last_name, "Muster")
        self.assertTrue(created_user.email.startswith("telegram_999@"))
        # A real, unusable bcrypt hash — never empty/plaintext.
        self.assertTrue(created_user.password_hash)
        self.assertIs(result, created_user)

    def test_username_collision_gets_a_numeric_suffix(self):
        mock_db = MagicMock()
        # telegram_id lookup -> None; first username check -> collision;
        # second (suffixed) username check -> free.
        mock_db.scalar.side_effect = [None, MagicMock(), None]

        get_or_create_telegram_user(mock_db, {"id": 42, "username": "taken"})

        created_user = mock_db.add.call_args[0][0]
        self.assertEqual(created_user.username, "taken_1")

    def test_no_username_falls_back_to_tg_prefixed_id(self):
        mock_db = MagicMock()
        mock_db.scalar.side_effect = [None, None]

        get_or_create_telegram_user(mock_db, {"id": 777})

        created_user = mock_db.add.call_args[0][0]
        self.assertEqual(created_user.username, "tg_777")


if __name__ == "__main__":
    unittest.main()
