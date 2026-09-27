"""Regression test for the production bug: password reset links were
generated as http://localhost:3000/reset-password?token=... because
FRONTEND_URL was never set in that environment (settings.FRONTEND_URL's
own default, meant only for local dev — see app/core/config.py).

request_password_reset() (app/services/auth/service.py) is unchanged in
behavior — it still builds the link from settings.FRONTEND_URL exactly
as before — this only adds a log.warning() the next time this exact
misconfiguration recurs (APP_ENV says "not local dev" but FRONTEND_URL
is still the local-dev default), so it's caught immediately instead of
silently shipping wrong links.
"""

import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.core.config import settings
from app.services.auth.service import request_password_reset

LOCALHOST_DEFAULT = "http://localhost:3000"


class TestPasswordResetFrontendUrlWarning(unittest.TestCase):
    def setUp(self):
        self._original_app_env = settings.APP_ENV
        self._original_frontend_url = settings.FRONTEND_URL

    def tearDown(self):
        settings.APP_ENV = self._original_app_env
        settings.FRONTEND_URL = self._original_frontend_url

    def _fake_user(self):
        return MagicMock(id=uuid4(), email="student@example.com", password_hash="$2b$12$fakehashfakehashfakehashfa")

    @patch("app.services.auth.service.logger")
    def test_warns_when_production_still_has_the_localhost_default(self, mock_logger):
        settings.APP_ENV = "production"
        settings.FRONTEND_URL = LOCALHOST_DEFAULT
        mock_db = MagicMock()
        mock_db.scalar.return_value = self._fake_user()

        request_password_reset(mock_db, "student@example.com")

        mock_logger.warning.assert_called_once()
        # The link itself is still built from FRONTEND_URL exactly as
        # before — this test only adds a warning, it doesn't change what
        # link gets generated/logged.
        info_call = mock_logger.info.call_args
        self.assertIn(LOCALHOST_DEFAULT, info_call[0][3])

    @patch("app.services.auth.service.logger")
    def test_no_warning_in_development_even_with_the_localhost_default(self, mock_logger):
        # This is the correct, unmodified local-dev behavior — must never
        # start warning just because a developer hasn't set FRONTEND_URL,
        # since localhost:3000 is genuinely correct there.
        settings.APP_ENV = "development"
        settings.FRONTEND_URL = LOCALHOST_DEFAULT
        mock_db = MagicMock()
        mock_db.scalar.return_value = self._fake_user()

        request_password_reset(mock_db, "student@example.com")

        mock_logger.warning.assert_not_called()

    @patch("app.services.auth.service.logger")
    def test_no_warning_once_frontend_url_is_configured_correctly(self, mock_logger):
        settings.APP_ENV = "production"
        settings.FRONTEND_URL = "https://vizu-deutsch.com"
        mock_db = MagicMock()
        mock_db.scalar.return_value = self._fake_user()

        request_password_reset(mock_db, "student@example.com")

        mock_logger.warning.assert_not_called()
        info_call = mock_logger.info.call_args
        self.assertIn("https://vizu-deutsch.com/reset-password?token=", info_call[0][3])

    @patch("app.services.auth.service.logger")
    def test_unknown_email_still_does_nothing_no_warning_no_link(self, mock_logger):
        # Unchanged existing behavior: never reveals whether the email
        # exists, regardless of FRONTEND_URL/APP_ENV.
        settings.APP_ENV = "production"
        settings.FRONTEND_URL = LOCALHOST_DEFAULT
        mock_db = MagicMock()
        mock_db.scalar.return_value = None

        request_password_reset(mock_db, "nobody@example.com")

        mock_logger.warning.assert_not_called()
        mock_logger.info.assert_not_called()


if __name__ == "__main__":
    unittest.main()
