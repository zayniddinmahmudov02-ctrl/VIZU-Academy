"""Production hardening: DEBUG off by default, no built-in admin password,
no implicit email fallback."""

import logging
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.api.auth import router as auth_router
from app.core.config import Settings, settings
from app.schemas.auth.password import VerifyAdminPasswordRequest
from app.services.email import email_service


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


class TestEmailProviderSafety(unittest.TestCase):
    KEYS = ("EMAIL_PROVIDER", "APP_ENV", "EMAIL_FROM", "SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD")

    def setUp(self):
        self._saved = {k: getattr(settings, k) for k in self.KEYS}

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(settings, k, v)

    def _smtp(self, **overrides):
        values = dict(EMAIL_PROVIDER="smtp", APP_ENV="production", EMAIL_FROM="noreply@vizu-deutsch.com",
                      SMTP_HOST="smtp.example.com", SMTP_PORT=587, SMTP_USERNAME="user", SMTP_PASSWORD="pw")
        values.update(overrides)
        for k, v in values.items():
            setattr(settings, k, v)

    def test_empty_provider_never_falls_back_to_outbox(self):
        for env in ("development", "test", "production"):
            with self.subTest(env=env):
                settings.EMAIL_PROVIDER, settings.APP_ENV = "", env
                self.assertEqual(email_service.missing_email_settings(), ["EMAIL_PROVIDER"])
                with patch.object(email_service.EmailService, "_write_outbox") as outbox:
                    with self.assertRaises(email_service.EmailNotConfigured):
                        email_service.EmailService().send_verification_code("a@example.com", "Anna", "000000")
                outbox.assert_not_called()

    def test_outbox_only_in_development_and_test(self):
        for env, ok in (("development", True), ("test", True), ("production", False), ("staging", False)):
            with self.subTest(env=env):
                settings.EMAIL_PROVIDER, settings.APP_ENV = "outbox", env
                self.assertEqual(email_service.missing_email_settings() == [], ok)

    def test_unknown_provider_refused(self):
        settings.EMAIL_PROVIDER = "sendmail"
        with self.assertRaises(email_service.EmailNotConfigured):
            email_service.EmailService().send_verification_code("a@example.com", "Anna", "000000")

    def test_complete_smtp_configuration(self):
        self._smtp()
        self.assertEqual(email_service.missing_email_settings(), [])

    def test_incomplete_smtp_configuration_is_reported_by_name_and_refused(self):
        cases = [
            (dict(EMAIL_FROM=""), ["EMAIL_FROM"]),
            (dict(SMTP_HOST=""), ["SMTP_HOST"]),
            (dict(SMTP_PORT=0), ["SMTP_PORT"]),
            (dict(SMTP_PASSWORD=""), ["SMTP_PASSWORD"]),
            (dict(SMTP_USERNAME=""), ["SMTP_USERNAME"]),
        ]
        for overrides, expected in cases:
            with self.subTest(overrides=list(overrides)):
                self._smtp(**overrides)
                self.assertEqual(email_service.missing_email_settings(), expected)
                with patch.object(email_service.smtplib, "SMTP") as smtp:
                    with self.assertRaises(email_service.EmailNotConfigured):
                        email_service.EmailService().send_password_reset_code("a@example.com", "Anna", "000000")
                smtp.assert_not_called()

    def test_startup_log_names_missing_settings_without_values(self):
        self._smtp(SMTP_HOST="", SMTP_PASSWORD="")
        with self.assertLogs(email_service.logger.name, level=logging.ERROR) as logs:
            email_service.log_email_configuration()
        text = "\n".join(logs.output)
        self.assertIn("SMTP_HOST", text)
        self.assertIn("SMTP_PASSWORD", text)
        self.assertNotIn("noreply@vizu-deutsch.com", text)
        self.assertNotIn("user", text.replace("SMTP_USERNAME", ""))


if __name__ == "__main__":
    unittest.main()
