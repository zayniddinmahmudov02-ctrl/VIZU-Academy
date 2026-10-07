"""Email verification / password reset — pure logic: code generation and
hashing, templates, email providers, schemas, verification rule."""

import logging
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from pydantic import ValidationError

from app.core.config import settings
from app.models.email_verification_code import PURPOSE_PASSWORD_RESET, PURPOSE_REGISTRATION
from app.schemas.auth.password import ResetPasswordRequest
from app.schemas.auth.user import UserRegister
from app.services.auth import email_code_service as codes
from app.services.auth.service import can_receive_email, display_name, needs_email_verification
from app.services.email import email_service
from app.services.email.templates import password_reset_email, verification_email


class TestCodes(unittest.TestCase):
    def test_codes_are_six_digits_from_secrets(self):
        for _ in range(200):
            self.assertRegex(codes.generate_code(), r"^\d{6}$")
        with patch.object(codes.secrets, "randbelow", return_value=42) as rb:
            self.assertEqual(codes.generate_code(), "000042")
            rb.assert_called_with(1_000_000)

    def test_hash_is_bound_to_user_and_purpose(self):
        user = uuid4()
        h = codes.hash_code(user, PURPOSE_REGISTRATION, "123456")
        self.assertEqual(len(h), 64)
        self.assertNotIn("123456", h)
        self.assertEqual(h, codes.hash_code(user, PURPOSE_REGISTRATION, "123456"))
        self.assertNotEqual(h, codes.hash_code(user, PURPOSE_PASSWORD_RESET, "123456"))
        self.assertNotEqual(h, codes.hash_code(uuid4(), PURPOSE_REGISTRATION, "123456"))
        self.assertNotEqual(h, codes.hash_code(user, PURPOSE_REGISTRATION, "123457"))

    def test_email_and_ip_keys_are_hashed_and_normalized(self):
        self.assertEqual(codes.email_key(" Anna@Example.com "), codes.email_key("anna@example.com"))
        self.assertNotIn("anna", codes.email_key("anna@example.com"))
        self.assertIsNone(codes.ip_key(None))
        self.assertEqual(len(codes.ip_key("1.2.3.4")), 64)

    def test_limits_match_the_policy(self):
        self.assertEqual(codes.CODE_TTL.total_seconds(), 600)
        self.assertEqual(codes.MAX_ATTEMPTS, 5)
        self.assertEqual(codes.SEND_COOLDOWN.total_seconds(), 60)
        self.assertEqual(codes.MAX_SENDS_PER_HOUR, 5)
        self.assertTrue(codes.CODE_RE.fullmatch("012345"))
        for bad in ("12345", "1234567", "12a456", " 123456 x"):
            self.assertFalse(codes.CODE_RE.fullmatch(bad))


class TestTemplates(unittest.TestCase):
    def test_verification_email(self):
        msg = verification_email("Anna", "482731")
        self.assertEqual(msg.subject, "Ihr Bestätigungscode für VIZU-Academy")
        for part in (
            "Hallo Anna,",
            "vielen Dank für Ihre Registrierung bei VIZU-Academy.",
            "Bitte verwenden Sie den folgenden Bestätigungscode:",
            "Der Code ist 10 Minuten gültig.",
            "Wenn Sie diese Registrierung nicht vorgenommen haben, können Sie diese E-Mail ignorieren.",
            "https://vizu-deutsch.com",
        ):
            self.assertIn(part, msg.text)
        self.assertIn("482731", msg.text)
        self.assertIn("4 8 2 7 3 1", msg.html)
        self.assertIn('name="viewport"', msg.html)

    def test_reset_email_is_german(self):
        msg = password_reset_email("Anna", "123456")
        self.assertEqual(msg.subject, "Passwort zurücksetzen – VIZU-Academy")
        self.assertIn("Sie haben eine Anfrage zum Zurücksetzen Ihres Passworts gestellt.", msg.text)
        self.assertIn("Ihr Bestätigungscode lautet:", msg.text)
        self.assertNotIn("If you did not", msg.text)

    def test_html_escapes_names(self):
        self.assertNotIn("<script>", verification_email("<script>x</script>", "111111").html)


class TestEmailService(unittest.TestCase):
    def setUp(self):
        self._saved = {k: getattr(settings, k) for k in ("EMAIL_PROVIDER", "APP_ENV", "EMAIL_OUTBOX_DIR", "SMTP_HOST", "EMAIL_FROM")}

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(settings, k, v)

    def test_outbox_in_development_writes_eml_and_never_logs_the_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings.EMAIL_PROVIDER, settings.APP_ENV, settings.EMAIL_OUTBOX_DIR = "", "development", tmp
            with self.assertLogs(email_service.logger.name, level=logging.INFO) as logs:
                email_service.EmailService().send_verification_code("a@example.com", "Anna", "654321")
            files = list(Path(tmp).glob("*.eml"))
            self.assertEqual(len(files), 1)
            self.assertIn(b"654321", files[0].read_bytes())
            self.assertFalse(any("654321" in line for line in logs.output))
            self.assertFalse(any("a@example.com" in line for line in logs.output))

    def test_not_configured_outside_development_refuses(self):
        settings.EMAIL_PROVIDER, settings.APP_ENV = "", "production"
        with self.assertRaises(email_service.EmailNotConfigured):
            email_service.EmailService().send_password_reset_code("a@example.com", "Anna", "654321")

    def test_outbox_refused_in_production(self):
        settings.EMAIL_PROVIDER, settings.APP_ENV = "outbox", "production"
        with self.assertRaises(email_service.EmailNotConfigured):
            email_service.EmailService().send_verification_code("a@example.com", "Anna", "654321")

    def test_smtp_requires_host_and_sender(self):
        settings.EMAIL_PROVIDER, settings.SMTP_HOST, settings.EMAIL_FROM = "smtp", "", ""
        with self.assertRaises(email_service.EmailNotConfigured):
            email_service.EmailService().send_verification_code("a@example.com", "Anna", "654321")

    def test_smtp_delivery_uses_starttls_and_login(self):
        settings.EMAIL_PROVIDER, settings.SMTP_HOST, settings.EMAIL_FROM = "smtp", "smtp.example.com", "noreply@vizu-deutsch.com"
        with patch.object(email_service.smtplib, "SMTP") as smtp:
            server = smtp.return_value
            with patch.object(settings, "SMTP_USERNAME", "user"), patch.object(settings, "SMTP_PASSWORD", "pw"), patch.object(settings, "SMTP_USE_SSL", False):
                email_service.EmailService().send_verification_code("a@example.com", "Anna", "654321")
        server.starttls.assert_called_once()
        server.login.assert_called_once_with("user", "pw")
        sent = server.send_message.call_args[0][0]
        self.assertEqual(sent["To"], "a@example.com")
        self.assertIn("VIZU-Academy", sent["From"])


class TestSchemasAndRules(unittest.TestCase):
    def test_register_requires_name_and_valid_password(self):
        ok = UserRegister(email="a@example.com", password="secret1", full_name="Anna Schmidt")
        self.assertEqual(ok.full_name, "Anna Schmidt")
        self.assertIsNotNone(UserRegister(email="a@example.com", password="secret1", username="anna_s"))
        for bad in (
            dict(email="a@example.com", password="secret1"),  # no name
            dict(email="a@example.com", password="12345", full_name="Anna"),  # too short
            dict(email="a@example.com", password="x" * 129, full_name="Anna"),  # too long
            dict(email="a@example.com", password="      ", full_name="Anna"),  # blank
            dict(email="not-an-email", password="secret1", full_name="Anna"),
        ):
            with self.assertRaises(ValidationError):
                UserRegister(**bad)

    def test_reset_request_has_no_token_field(self):
        self.assertEqual(set(ResetPasswordRequest.model_fields), {"email", "code", "new_password"})

    def test_only_new_registrations_need_verification(self):
        self.assertTrue(needs_email_verification(SimpleNamespace(email_verification_required=True, email_verified_at=None)))
        self.assertFalse(needs_email_verification(SimpleNamespace(email_verification_required=True, email_verified_at=object())))
        # existing accounts (flag false) are never blocked, verified or not
        self.assertFalse(needs_email_verification(SimpleNamespace(email_verification_required=False, email_verified_at=None)))

    def test_telegram_accounts_get_no_mail(self):
        self.assertFalse(can_receive_email(SimpleNamespace(email="telegram_1@telegram.local")))
        self.assertTrue(can_receive_email(SimpleNamespace(email="a@example.com")))

    def test_display_name(self):
        self.assertEqual(display_name(SimpleNamespace(first_name="Anna", username="a")), "Anna")
        self.assertEqual(display_name(SimpleNamespace(first_name=None, username="anna_s")), "anna_s")

    def test_no_code_in_any_auth_log_call(self):
        import inspect

        from app.api.auth import router

        source = inspect.getsource(router) + inspect.getsource(codes)
        for call in re.findall(r"logger\.\w+\((.*?)\)\n", source, re.S):
            # the logged VALUES (everything after the format string)
            values = call.split('",', 1)[1] if '",' in call else ""
            self.assertNotRegex(values, r"\bcode\b|password|smtp", call)


if __name__ == "__main__":
    unittest.main()
