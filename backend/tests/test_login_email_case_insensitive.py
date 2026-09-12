"""Regression test for the production login-401 root cause: email
lookup was a plain case-sensitive `User.email == email` comparison,
nowhere normalized on write either — any account whose stored email
differs in case from what's typed at login (mobile autocapitalize, a
copy-pasted address, etc.) could never authenticate, no matter how
correct the password was. Fixed in app/services/auth/service.py by
comparing against `func.lower(User.email)` with a stripped+lowercased
input, in authenticate_user / get_user_by_email / create_user's
duplicate check.

No real DB exists in this test suite (see conftest.py / every other
test file here) — SQLAlchemy Core statements can still be *compiled* to
SQL text without a real engine/connection, which is enough to prove the
comparison is genuinely case-insensitive (contains a `lower(...)` on the
email column) rather than mocking db.scalar and trivially getting a
green test regardless of what the real query does.
"""

import unittest
from unittest.mock import MagicMock

from app.models.user import User
from app.services.auth.service import authenticate_user, get_user_by_email


def _compiled_where_sql_and_params(mock_db: MagicMock) -> tuple[str, dict]:
    """authenticate_user/get_user_by_email call db.scalar(select(...))
    exactly once — pull that statement back out and compile it (generic,
    dialect-less compilation works fine for inspecting the WHERE clause
    and bound parameters without a real database)."""
    args, _kwargs = mock_db.scalar.call_args
    statement = args[0]
    compiled = statement.compile()
    return str(compiled), dict(compiled.params)


class TestLoginEmailCaseInsensitive(unittest.TestCase):
    def test_authenticate_user_query_is_case_insensitive(self):
        mock_db = MagicMock()
        mock_db.scalar.return_value = None  # user not found is fine — only the query shape is under test

        authenticate_user(mock_db, "Zayniddin.Mahmudov.02@GMAIL.com", "irrelevant-password")

        sql, params = _compiled_where_sql_and_params(mock_db)
        self.assertIn("lower(users.email)", sql.lower())
        # The bound parameter must be the normalized (trimmed+lowercased)
        # form — a stray "Zayniddin..." leaking through here would mean
        # the fix only wraps the COLUMN in lower(), not the input, which
        # still wouldn't match a differently-cased stored value depending
        # on collation.
        self.assertIn("zayniddin.mahmudov.02@gmail.com", params.values())

    def test_authenticate_user_strips_whitespace(self):
        mock_db = MagicMock()
        mock_db.scalar.return_value = None

        authenticate_user(mock_db, "  someone@example.com  ", "irrelevant-password")

        _sql, params = _compiled_where_sql_and_params(mock_db)
        self.assertIn("someone@example.com", params.values())
        self.assertNotIn("  someone@example.com  ", params.values())

    def test_get_user_by_email_is_case_insensitive(self):
        mock_db = MagicMock()
        mock_db.scalar.return_value = None

        get_user_by_email(mock_db, "Someone@Example.COM")

        sql, params = _compiled_where_sql_and_params(mock_db)
        self.assertIn("lower(users.email)", sql.lower())
        self.assertIn("someone@example.com", params.values())

    def test_authenticate_user_returns_none_for_unknown_email_without_raising(self):
        mock_db = MagicMock()
        mock_db.scalar.return_value = None

        result = authenticate_user(mock_db, "nobody@example.com", "x")

        self.assertIsNone(result)

    def test_authenticate_user_rejects_wrong_password_for_a_real_user(self):
        mock_db = MagicMock()
        user = User(email="real@example.com", username="real")
        from app.core.security import hash_password

        user.password_hash = hash_password("correct-horse-battery-staple")
        mock_db.scalar.return_value = user

        result = authenticate_user(mock_db, "real@example.com", "wrong-password")

        self.assertIsNone(result)

    def test_authenticate_user_accepts_correct_password_case_insensitive_email(self):
        mock_db = MagicMock()
        user = User(email="Real@Example.com", username="real")
        from app.core.security import hash_password

        user.password_hash = hash_password("correct-horse-battery-staple")
        mock_db.scalar.return_value = user

        result = authenticate_user(mock_db, "real@example.com", "correct-horse-battery-staple")

        self.assertIs(result, user)


if __name__ == "__main__":
    unittest.main()
