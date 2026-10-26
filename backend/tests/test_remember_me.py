"""Login "remember me": long sliding refresh lifetime vs short pinned one."""

import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.schemas.auth.user import UserLogin
from app.services.auth import service as auth


def _now():
    return datetime.now(UTC).replace(tzinfo=None)


class TestRememberMe(unittest.TestCase):
    def test_login_schema_defaults_to_remember(self):
        self.assertTrue(UserLogin(identifier="a@b.de", password="x").remember_me)
        self.assertFalse(UserLogin(identifier="a@b.de", password="x", remember_me=False).remember_me)

    def _issue(self, **kwargs):
        with patch.object(auth, "RefreshTokenRepository") as repo:
            auth.issue_refresh_token(MagicMock(), SimpleNamespace(id="u1"), **kwargs)
            return repo.return_value.issue.call_args.kwargs["expires_at"]

    def test_remembered_session_is_long(self):
        left = self._issue(remember=True) - _now()
        self.assertGreater(left, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS) - timedelta(minutes=1))

    def test_plain_session_is_short(self):
        left = self._issue(remember=False) - _now()
        self.assertLessEqual(left, timedelta(hours=settings.REFRESH_TOKEN_SESSION_EXPIRE_HOURS))

    def _rotate(self, expires_in):
        stored = SimpleNamespace(expires_at=_now() + expires_in, user_id="u1")
        with patch.object(auth, "RefreshTokenRepository") as repo, \
             patch.object(auth, "get_user_by_id", return_value=SimpleNamespace(id="u1")), \
             patch.object(auth, "issue_token_pair") as pair:
            repo.return_value.get_by_token.return_value = stored
            auth.refresh_access_token(MagicMock(), "tok")
            return stored, pair.call_args.kwargs["expires_at"]

    def test_rotation_keeps_short_session_expiry(self):
        stored, pinned = self._rotate(timedelta(hours=3))
        self.assertEqual(pinned, stored.expires_at)

    def test_rotation_renews_remembered_session(self):
        _, pinned = self._rotate(timedelta(days=20))
        self.assertIsNone(pinned)


if __name__ == "__main__":
    unittest.main()
