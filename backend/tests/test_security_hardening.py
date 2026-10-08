"""Production hardening: DEBUG off by default, no built-in admin password."""

import logging
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.api.auth import router as auth_router
from app.core.config import Settings, settings
from app.schemas.auth.password import VerifyAdminPasswordRequest


class TestConfigDefaults(unittest.TestCase):
    def test_debug_defaults_to_false(self):
        self.assertIs(Settings.model_fields["DEBUG"].default, False)

    def test_admin_verification_password_has_no_default(self):
        self.assertEqual(Settings.model_fields["SUPER_ADMIN_VERIFICATION_PASSWORD"].default, "")

    def test_sql_echo_only_with_explicit_debug_outside_production(self):
        cases = [
            (False, "development", False),
            (True, "development", True),
            (True, "test", True),
            (True, "production", False),
            (True, "staging", False),
            (False, "production", False),
        ]
        for debug, env, expected in cases:
            with self.subTest(debug=debug, env=env):
                with patch.object(settings, "DEBUG", debug), patch.object(settings, "APP_ENV", env):
                    self.assertIs(settings.SQL_ECHO, expected)


class TestAdminVerification(unittest.TestCase):
    admin = SimpleNamespace(id="admin-id", role="SUPER_ADMIN")

    def test_refuses_when_not_configured(self):
        with patch.object(settings, "SUPER_ADMIN_VERIFICATION_PASSWORD", ""):
            for attempt in ("", "anything"):
                with self.subTest(attempt=attempt):
                    with self.assertRaises(HTTPException) as ctx, self.assertLogs(auth_router.logger.name, level=logging.ERROR):
                        auth_router.verify_admin_password(VerifyAdminPasswordRequest(password=attempt), current_user=self.admin)
                    self.assertEqual(ctx.exception.status_code, 503)
                    self.assertEqual(ctx.exception.detail, "ADMIN_VERIFICATION_NOT_CONFIGURED")

    def test_configured_value_is_enforced(self):
        configured = "unit-test-only-value"
        with patch.object(settings, "SUPER_ADMIN_VERIFICATION_PASSWORD", configured):
            self.assertEqual(
                auth_router.verify_admin_password(VerifyAdminPasswordRequest(password=configured), current_user=self.admin),
                {"message": "Admin verification successful."},
            )
            with self.assertRaises(HTTPException) as ctx:
                auth_router.verify_admin_password(VerifyAdminPasswordRequest(password="wrong"), current_user=self.admin)
            self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
