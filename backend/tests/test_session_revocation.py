"""Access-token revocation through login sessions (`sid` claim), and the
SUPER_ADMIN second-step password check. Mocked collaborators, no database."""

import asyncio
import inspect
import unittest
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from jose import jwt

from app.api.auth import router as auth_router
from app.api.dependencies import auth as deps
from app.core.config import settings
from app.core.security import create_access_token, create_user_token, decode_access_token
from app.core.security.roles import UserRole
from app.schemas.auth.password import VerifyAdminPasswordRequest
from app.services.auth import service as auth


def _now():
    return datetime.now(UTC).replace(tzinfo=None)


def _user(**kw):
    base = dict(id=uuid.uuid4(), email="a@b.de", role=UserRole.STUDENT, tokens_valid_after=None,
                is_banned=False, is_active=True, suspended_until=None)
    base.update(kw)
    return SimpleNamespace(**base)


def _call_current_user(token, session_active=True, user=None):
    user = user or _user()
    with patch.object(deps, "get_user_by_id", return_value=user), \
         patch.object(deps, "RefreshTokenRepository") as repo:
        repo.return_value.session_is_active.return_value = session_active
        result = asyncio.run(deps.get_current_user(token=token, db=MagicMock()))
        return result, repo


class TestSessionIssuing(unittest.TestCase):
    def test_login_pair_shares_one_session_id(self):
        user = _user()
        with patch.object(auth, "RefreshTokenRepository") as repo:
            pair = auth.issue_token_pair(MagicMock(), user)
        sid = decode_access_token(pair.access_token)["sid"]
        self.assertEqual(repo.return_value.issue.call_args.kwargs["session_id"], uuid.UUID(sid))

    def test_each_login_gets_a_new_session(self):
        user = _user()
        with patch.object(auth, "RefreshTokenRepository"):
            a = decode_access_token(auth.issue_token_pair(MagicMock(), user).access_token)["sid"]
            b = decode_access_token(auth.issue_token_pair(MagicMock(), user).access_token)["sid"]
        self.assertNotEqual(a, b)

    def _rotate(self, session_id):
        stored = SimpleNamespace(expires_at=_now() + timedelta(days=10), user_id="u1", session_id=session_id)
        with patch.object(auth, "RefreshTokenRepository") as repo, \
             patch.object(auth, "get_user_by_id", return_value=_user()), \
             patch.object(auth, "issue_token_pair") as pair:
            repo.return_value.get_by_token.return_value = stored
            auth.refresh_access_token(MagicMock(), "tok")
            return pair.call_args.kwargs["session_id"], repo

    def test_rotation_keeps_the_session(self):
        sid = uuid.uuid4()
        kept, repo = self._rotate(sid)
        self.assertEqual(kept, sid)
        repo.return_value.delete.assert_called_once()  # old refresh token still single-use

    def test_legacy_row_starts_a_session_on_rotation(self):
        kept, _ = self._rotate(None)
        self.assertIsInstance(kept, uuid.UUID)


class TestLogoutRevocation(unittest.TestCase):
    def test_logout_deletes_the_whole_session(self):
        sid = uuid.uuid4()
        with patch.object(auth, "RefreshTokenRepository") as repo:
            repo.return_value.get_by_token.return_value = SimpleNamespace(session_id=sid)
            auth.revoke_refresh_token(MagicMock(), "tok")
        repo.return_value.delete_session.assert_called_once_with(sid)

    def test_logout_of_a_legacy_row_deletes_that_row(self):
        row = SimpleNamespace(session_id=None)
        with patch.object(auth, "RefreshTokenRepository") as repo:
            repo.return_value.get_by_token.return_value = row
            auth.revoke_refresh_token(MagicMock(), "tok")
        repo.return_value.delete.assert_called_once_with(row)
        repo.return_value.delete_session.assert_not_called()

    def test_unknown_token_logout_is_a_noop(self):
        with patch.object(auth, "RefreshTokenRepository") as repo:
            repo.return_value.get_by_token.return_value = None
            auth.revoke_refresh_token(MagicMock(), "nope")
        repo.return_value.delete.assert_not_called()
        repo.return_value.delete_session.assert_not_called()


class TestGetCurrentUser(unittest.TestCase):
    def _token(self, user, **claims):
        return create_user_token(user, extra_claims=claims or None)

    def test_active_session_is_accepted(self):
        user = _user()
        result, repo = _call_current_user(self._token(user, sid=str(uuid.uuid4())), True, user)
        self.assertIs(result, user)
        repo.return_value.session_is_active.assert_called_once()

    def test_ended_session_is_refused(self):
        user = _user()
        with self.assertRaises(HTTPException) as ctx:
            _call_current_user(self._token(user, sid=str(uuid.uuid4())), False, user)
        self.assertEqual((ctx.exception.status_code, ctx.exception.detail), (401, "Session ended"))

    def test_malformed_sid_is_refused(self):
        with self.assertRaises(HTTPException) as ctx:
            _call_current_user(self._token(_user(), sid="not-a-uuid"))
        self.assertEqual(ctx.exception.status_code, 401)

    def test_token_without_sid_keeps_plain_expiry(self):
        # issued before session ids existed, or admin impersonation
        user = _user()
        result, repo = _call_current_user(self._token(user, impersonated_by=str(uuid.uuid4())), True, user)
        self.assertIs(result, user)
        repo.return_value.session_is_active.assert_not_called()

    def test_expired_token_is_refused(self):
        user = _user()
        expired = jwt.encode({"sub": str(user.id), "sid": str(uuid.uuid4()),
                              "iat": datetime.now(UTC) - timedelta(hours=2), "exp": datetime.now(UTC) - timedelta(minutes=1)},
                             settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        with self.assertRaises(HTTPException) as ctx:
            _call_current_user(expired, True, user)
        self.assertEqual((ctx.exception.status_code, ctx.exception.detail), (401, "Token expired"))

    def test_purpose_tokens_are_not_login_credentials(self):
        user = _user()
        for purpose in ("video_stream", "lms_resource", "admin_video_preview"):
            token = create_access_token({"sub": str(user.id), "purpose": purpose, "user_id": str(user.id)})
            with self.subTest(purpose=purpose), self.assertRaises(HTTPException) as ctx:
                _call_current_user(token, True, user)
            self.assertEqual(ctx.exception.status_code, 401)

    def test_optional_variant_treats_ended_session_as_anonymous(self):
        user = _user()
        token = self._token(user, sid=str(uuid.uuid4()))
        with patch.object(deps, "get_user_by_id", return_value=user), \
             patch.object(deps, "RefreshTokenRepository") as repo:
            repo.return_value.session_is_active.return_value = False
            self.assertIsNone(asyncio.run(deps.get_current_user_optional(token=token, db=MagicMock())))


class TestEveryGateUsesTheSessionCheck(unittest.TestCase):
    """The revocation lives in get_current_user; every role gate must resolve
    the user through it, so no protected endpoint skips the check
    (test_route_protection makes sure every endpoint has such a gate)."""

    def test_all_gates_depend_on_get_current_user(self):
        gates = [getattr(deps, n) for n in dir(deps) if n.startswith("require_") and callable(getattr(deps, n))]
        self.assertGreaterEqual(len(gates), 4)
        for gate in gates:
            with self.subTest(gate=gate.__name__):
                calls = [p.default.dependency for p in inspect.signature(gate).parameters.values()
                         if hasattr(p.default, "dependency")]
                self.assertIn(deps.get_current_user, calls)

    def test_optional_variant_delegates(self):
        self.assertIn("get_current_user(", inspect.getsource(deps.get_current_user_optional))


class TestSuperAdminSecondStep(unittest.TestCase):
    def _verify(self, configured, password):
        admin = _user(role=UserRole.SUPER_ADMIN)
        with patch.object(auth_router.settings, "SUPER_ADMIN_VERIFICATION_PASSWORD", configured):
            return auth_router.verify_admin_password(VerifyAdminPasswordRequest(password=password), current_user=admin)

    def test_unset_secret_refuses_with_503_never_a_default(self):
        for unset in (None, ""):
            with self.subTest(unset=unset), self.assertRaises(HTTPException) as ctx:
                self._verify(unset, "anything")
            self.assertEqual((ctx.exception.status_code, ctx.exception.detail), (503, "ADMIN_VERIFICATION_NOT_CONFIGURED"))

    def test_wrong_password_is_403(self):
        with self.assertRaises(HTTPException) as ctx:
            self._verify("correct-horse", "wrong")
        self.assertEqual(ctx.exception.status_code, 403)

    def test_correct_password_passes(self):
        self.assertEqual(self._verify("correct-horse", "correct-horse"), {"message": "Admin verification successful."})

    def test_comparison_is_constant_time(self):
        self.assertIn("compare_digest", inspect.getsource(auth_router.verify_admin_password))

    def test_only_super_admin_reaches_the_check(self):
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(deps.require_super_admin(current_user=_user(role=UserRole.ADMIN)))
        self.assertEqual(ctx.exception.status_code, 403)

    def test_endpoint_is_gated_by_require_super_admin(self):
        params = inspect.signature(auth_router.verify_admin_password).parameters
        self.assertIs(params["current_user"].default.dependency, deps.require_super_admin)


if __name__ == "__main__":
    unittest.main()
