"""Registration / login with an e-mail address OR a phone number, without
any confirmation step, plus login / registration brute-force limits."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from pydantic import ValidationError

from app.core.security import hash_password
from app.schemas.auth.user import UserLogin, UserRegister
from app.services.auth import identifier as ident
from app.services.auth import rate_limit
from app.services.auth import service as auth


class TestIdentifierParsing(unittest.TestCase):
    def test_email(self):
        self.assertEqual(ident.parse_identifier("  Anna.Schmidt@Example.COM "), ident.LoginIdentifier("email", "anna.schmidt@example.com"))

    def test_phone_formats_normalise_to_the_same_value(self):
        for raw in ("+998 90 123 45 67", "998901234567", "90 123 45 67", "(90) 123-45-67", "00998901234567", "+998-90-123-45-67"):
            with self.subTest(raw=raw):
                self.assertEqual(ident.parse_identifier(raw), ident.LoginIdentifier("phone", "+998901234567"))

    def test_foreign_phone(self):
        self.assertEqual(ident.parse_identifier("+49 151 2345 6789").value, "+4915123456789")

    def test_invalid_identifiers(self):
        for raw in ("", "   ", "abc", "12345", "+12 34", "123456789012345678", "anna@", "@x.de"):
            with self.subTest(raw=raw), self.assertRaises(ident.InvalidIdentifier):
                ident.parse_identifier(raw, strict=True)

    def test_strict_email_validation_only_for_registration(self):
        with self.assertRaises(ident.InvalidIdentifier):
            ident.parse_identifier("admin@vizu.local", strict=True)
        # login stays lenient so existing accounts keep working
        self.assertEqual(ident.parse_identifier("admin@vizu.local").value, "admin@vizu.local")

    def test_placeholder_email_passes_emailstr_and_is_reserved(self):
        from app.schemas.auth.user import UserResponse

        email = ident.phone_placeholder_email("+998901234567")
        self.assertEqual(email, "998901234567@phone.vizu-deutsch.com")
        self.assertTrue(ident.is_reserved_email(email))
        self.assertTrue(ident.is_reserved_email("telegram_1@telegram.local"))
        self.assertFalse(ident.is_reserved_email("anna@example.com"))
        UserResponse.model_validate(  # must not fail validation for /users/me
            {"id": "00000000-0000-0000-0000-000000000001", "email": email, "username": "u998", "preferred_language": "de",
             "is_active": True, "is_verified": True, "is_banned": False, "role": "STUDENT", "created_at": "2026-10-08T00:00:00"}
        )


class TestSchemas(unittest.TestCase):
    def test_register_requires_identifier_name_and_matching_passwords(self):
        ok = UserRegister(identifier="+998901234567", full_name="Anna Schmidt", password="secret1", password_confirm="secret1")
        self.assertEqual(ok.login_identifier, "+998901234567")
        self.assertEqual(UserRegister(email="a@example.com", full_name="Anna S", password="secret1").login_identifier, "a@example.com")
        for bad in (
            dict(full_name="Anna Schmidt", password="secret1"),  # no identifier
            dict(identifier="a@example.com", password="secret1"),  # no name
            dict(identifier="a@example.com", full_name="Anna S", password="12345"),  # too short
            dict(identifier="a@example.com", full_name="Anna S", password="secret1", password_confirm="secret2"),
        ):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                UserRegister(**bad)

    def test_login_accepts_identifier_or_legacy_email(self):
        self.assertEqual(UserLogin(identifier="90 123 45 67", password="x").login_identifier, "90 123 45 67")
        self.assertEqual(UserLogin(email="admin@example.com", password="x").login_identifier, "admin@example.com")
        with self.assertRaises(ValidationError):
            UserLogin(password="x")


class TestCreateUser(unittest.TestCase):
    def _db(self, existing=None):
        db = MagicMock()
        db.scalar.side_effect = lambda *a, **k: existing
        return db

    def test_email_registration_is_active_and_verified_immediately(self):
        db = self._db()
        user = auth.create_user(db, UserRegister(identifier="Anna@Example.com", full_name="Anna Schmidt", password="secret1"))
        self.assertEqual((user.email, user.login_phone), ("anna@example.com", None))
        self.assertTrue(user.is_active and user.is_verified)
        self.assertEqual((user.first_name, user.last_name), ("Anna", "Schmidt"))
        self.assertNotEqual(user.password_hash, "secret1")
        db.add.assert_called_once_with(user)

    def test_phone_registration(self):
        db = self._db()
        user = auth.create_user(db, UserRegister(identifier="90 123 45 67", full_name="Ali Valiyev", password="secret1"))
        self.assertEqual(user.login_phone, "+998901234567")
        self.assertEqual(user.phone_number, "+998901234567")
        self.assertEqual(user.email, "998901234567@phone.vizu-deutsch.com")
        self.assertTrue(user.is_verified)

    def test_duplicate_email_or_phone_is_409(self):
        for identifier in ("anna@example.com", "+998901234567"):
            with self.subTest(identifier=identifier):
                db = self._db(existing=SimpleNamespace(id="taken"))
                with self.assertRaises(HTTPException) as ctx:
                    auth.create_user(db, UserRegister(identifier=identifier, full_name="Anna S", password="secret1"))
                self.assertEqual((ctx.exception.status_code, ctx.exception.detail), (409, "ACCOUNT_EXISTS"))
                db.add.assert_not_called()

    def test_invalid_or_reserved_identifier_is_422(self):
        for identifier in ("not-a-login", "998901234567@phone.vizu-deutsch.com", "x@telegram.local"):
            with self.subTest(identifier=identifier):
                with self.assertRaises(HTTPException) as ctx:
                    auth.create_user(self._db(), UserRegister(identifier=identifier, full_name="Anna S", password="secret1"))
                self.assertEqual((ctx.exception.status_code, ctx.exception.detail), (422, "INVALID_IDENTIFIER"))

    def test_concurrent_duplicate_maps_to_409(self):
        from sqlalchemy.exc import IntegrityError

        db = self._db()
        db.commit.side_effect = IntegrityError("x", {}, Exception("dup"))
        with self.assertRaises(HTTPException) as ctx:
            auth.create_user(db, UserRegister(identifier="anna@example.com", full_name="Anna S", password="secret1"))
        self.assertEqual(ctx.exception.status_code, 409)
        db.rollback.assert_called_once()


class TestAuthenticate(unittest.TestCase):
    def _user(self):
        return SimpleNamespace(password_hash=hash_password("secret1"))

    def test_login_by_email_or_phone(self):
        for identifier in ("anna@example.com", "+998 90 123 45 67", "901234567"):
            with self.subTest(identifier=identifier):
                db = MagicMock()
                db.scalar.return_value = self._user()
                self.assertIsNotNone(auth.authenticate_user(db, identifier, "secret1"))

    def test_phone_lookup_uses_login_phone_column(self):
        db = MagicMock()
        db.scalar.return_value = None
        auth.authenticate_user(db, "90 123 45 67", "x")
        query = str(db.scalar.call_args[0][0].compile(compile_kwargs={"literal_binds": True}))
        self.assertIn("login_phone", query)
        self.assertIn("+998901234567", query)

    def test_wrong_password_and_garbage_identifier(self):
        db = MagicMock()
        db.scalar.return_value = self._user()
        self.assertIsNone(auth.authenticate_user(db, "anna@example.com", "wrong"))
        self.assertIsNone(auth.authenticate_user(MagicMock(), "%%%", "secret1"))


class TestRateLimit(unittest.TestCase):
    def test_login_blocked_after_too_many_failures(self):
        db = MagicMock()
        db.execute.return_value.one.return_value = (rate_limit.MAX_FAILED_LOGINS_PER_IDENTIFIER, None)
        with self.assertRaises(rate_limit.RateLimited) as ctx:
            rate_limit.check_login_allowed(db, "+998901234567", "1.2.3.4")
        self.assertGreater(ctx.exception.retry_after, 0)

    def test_login_allowed_below_limit(self):
        db = MagicMock()
        db.execute.return_value.one.return_value = (3, None)
        rate_limit.check_login_allowed(db, "anna@example.com", "1.2.3.4")  # no exception

    def test_keys_are_hashed_never_raw(self):
        key = rate_limit.identifier_key("anna@example.com")
        self.assertEqual(len(key), 64)
        self.assertNotIn("anna", key)
        self.assertEqual(key, rate_limit.identifier_key("  ANNA@example.com "))


class TestNoEmailVerificationLeft(unittest.TestCase):
    def test_removed_endpoints_are_gone(self):
        from app.api.auth.router import router

        paths = {r.path for r in router.routes}
        for gone in ("/auth/verify-email", "/auth/resend-verification", "/auth/forgot-password", "/auth/verify-reset-code", "/auth/reset-password"):
            self.assertNotIn(gone, paths)
        for kept in ("/auth/register", "/auth/login", "/auth/telegram", "/auth/refresh", "/auth/logout", "/auth/verify-admin-password"):
            self.assertIn(kept, paths)

    def test_no_email_modules(self):
        import importlib.util

        for mod in ("app.services.auth.email_code_service", "app.services.email", "app.models.email_verification_code"):
            self.assertIsNone(importlib.util.find_spec(mod), mod)


if __name__ == "__main__":
    unittest.main()
