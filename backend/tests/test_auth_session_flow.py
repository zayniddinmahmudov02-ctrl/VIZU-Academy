"""End-to-end auth session flow over real HTTP + a real PostgreSQL database:
register -> login (remember / not) -> refresh rotation -> logout ->
refresh refused. Needs a running backend on a migrated, throwaway database,
so it only runs when VIZU_AUTH_FLOW_URL is set (and DATABASE_* env vars point
at the same database the server uses), e.g.

    DATABASE_PORT=54329 DATABASE_NAME=vizu_auth_e2e \
        uvicorn app.main:app --port 8000 &
    DATABASE_PORT=54329 DATABASE_NAME=vizu_auth_e2e VIZU_AUTH_FLOW_URL=http://127.0.0.1:8000 \
        python -m unittest tests.test_auth_session_flow
"""

import json
import os
import unittest
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime, timedelta

BASE_URL = os.environ.get("VIZU_AUTH_FLOW_URL", "").rstrip("/")


class _Response:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text

    def json(self):
        return json.loads(self.text)


class _Client:
    """Tiny stdlib HTTP client (the TestClient needs httpx2, not installed)."""

    def _send(self, method, path, body=None, headers=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(BASE_URL + path, data=data, method=method, headers={
            "Content-Type": "application/json", **(headers or {}),
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                return _Response(res.status, res.read().decode())
        except urllib.error.HTTPError as err:
            return _Response(err.code, err.read().decode())

    def get(self, path, headers=None):
        return self._send("GET", path, headers=headers)

    def post(self, path, json=None, headers=None):
        return self._send("POST", path, json, headers)


@unittest.skipUnless(BASE_URL, "integration test: set VIZU_AUTH_FLOW_URL to a backend on a migrated test database")
class TestAuthSessionFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.core.config import settings
        from app.db.session import SessionLocal
        from app.models.refresh_token import RefreshToken

        assert settings.DATABASE_NAME != "vizu_academy", "refusing to run against the main database"
        cls.client = _Client()
        cls.Session = SessionLocal
        cls.RefreshToken = RefreshToken
        cls.settings = settings
        cls.email = f"flow_{uuid.uuid4().hex[:10]}@example.com"
        cls.password = "Geheim123!"
        r = cls.client.post("/auth/register", json={
            "full_name": "Flow Test", "identifier": cls.email,
            "password": cls.password, "password_confirm": cls.password,
        })
        assert r.status_code == 200, r.text

    def _login(self, remember):
        r = self.client.post("/auth/login", json={"identifier": self.email, "password": self.password, "remember_me": remember})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def _expiry(self, refresh_token):
        with self.Session() as db:
            row = db.query(self.RefreshToken).filter_by(token=refresh_token).one_or_none()
            return row.expires_at if row else None

    def _left(self, refresh_token):
        return self._expiry(refresh_token) - datetime.now(UTC).replace(tzinfo=None)

    def test_wrong_password_is_rejected(self):
        r = self.client.post("/auth/login", json={"identifier": self.email, "password": "falsch"})
        self.assertEqual(r.status_code, 401)
        self.assertNotIn("Traceback", r.text)

    def test_duplicate_registration_is_409(self):
        r = self.client.post("/auth/register", json={
            "full_name": "Flow Test", "identifier": self.email,
            "password": self.password, "password_confirm": self.password,
        })
        self.assertEqual(r.status_code, 409, r.text)

    def test_remember_me_session_is_long_and_sliding(self):
        tokens = self._login(True)
        self.assertGreater(self._left(tokens["refresh_token"]), timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS - 1))
        r = self.client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        self.assertEqual(r.status_code, 200)
        self.assertGreater(self._left(r.json()["refresh_token"]), timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS - 1))

    def test_plain_session_is_short_and_not_extended_by_refresh(self):
        tokens = self._login(False)
        first = self._expiry(tokens["refresh_token"])
        self.assertLessEqual(self._left(tokens["refresh_token"]), timedelta(hours=self.settings.REFRESH_TOKEN_SESSION_EXPIRE_HOURS))
        r = self.client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self._expiry(r.json()["refresh_token"]), first)

    def test_rotation_makes_old_refresh_token_single_use(self):
        tokens = self._login(True)
        self.assertEqual(self.client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code, 200)
        self.assertEqual(self.client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code, 401)

    def test_logout_revokes_refresh_token(self):
        tokens = self._login(True)
        me = self.client.get("/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
        self.assertEqual(me.status_code, 200)
        self.assertEqual(self.client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code, 200)
        self.assertIsNone(self._expiry(tokens["refresh_token"]))
        self.assertEqual(self.client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code, 401)

    def test_expired_refresh_token_requires_new_login(self):
        tokens = self._login(False)
        with self.Session() as db:
            row = db.query(self.RefreshToken).filter_by(token=tokens["refresh_token"]).one()
            row.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)
            db.commit()
        self.assertEqual(self.client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code, 401)

    def test_protected_endpoints_without_or_with_bad_token(self):
        self.assertEqual(self.client.get("/users/me").status_code, 401)
        self.assertEqual(self.client.get("/users/me", headers={"Authorization": "Bearer x.y.z"}).status_code, 401)

    def test_student_cannot_reach_admin_endpoints(self):
        tokens = self._login(True)
        r = self.client.get("/admin/dashboard", headers={"Authorization": f"Bearer {tokens['access_token']}"})
        self.assertEqual(r.status_code, 403)

    # --- access-token revocation (sid claim) ---

    def _me(self, access):
        return self.client.get("/users/me", headers={"Authorization": f"Bearer {access}"}).status_code

    def test_logout_revokes_the_access_token_immediately(self):
        tokens = self._login(True)
        self.assertEqual(self._me(tokens["access_token"]), 200)
        self.client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
        r = self.client.get("/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
        self.assertEqual((r.status_code, r.json()["message"]), (401, "Session ended"))
        # same on the /api/v1 mount
        self.assertEqual(self.client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}).status_code, 401)

    def test_refresh_keeps_earlier_access_valid_and_logout_ends_both(self):
        tokens = self._login(True)
        new = self.client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).json()
        # parallel requests still holding the pre-rotation access token keep working
        self.assertEqual(self._me(tokens["access_token"]), 200)
        self.assertEqual(self._me(new["access_token"]), 200)
        self.client.post("/auth/logout", json={"refresh_token": new["refresh_token"]})
        self.assertEqual(self._me(tokens["access_token"]), 401)
        self.assertEqual(self._me(new["access_token"]), 401)

    def test_logout_ends_only_that_session(self):
        phone, laptop = self._login(True), self._login(False)
        self.client.post("/auth/logout", json={"refresh_token": phone["refresh_token"]})
        self.assertEqual(self._me(phone["access_token"]), 401)
        self.assertEqual(self._me(laptop["access_token"]), 200)

    def test_expired_session_refuses_its_access_token(self):
        tokens = self._login(False)
        with self.Session() as db:
            row = db.query(self.RefreshToken).filter_by(token=tokens["refresh_token"]).one()
            row.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)
            db.commit()
        self.assertEqual(self._me(tokens["access_token"]), 401)

    def test_revoked_access_is_refused_by_every_gate(self):
        admin = self._admin_login()
        hdr = {"Authorization": f"Bearer {admin['access_token']}"}
        for path in ("/users/me", "/admin/dashboard", "/teacher/students"):
            self.assertIn(self.client.get(path, headers=hdr).status_code, (200, 404), path)
        self.client.post("/auth/logout", json={"refresh_token": admin["refresh_token"]})
        for path in ("/users/me", "/admin/dashboard", "/teacher/students"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path, headers=hdr).status_code, 401)

    def test_password_change_ends_all_sessions(self):
        email = f"pw_{uuid.uuid4().hex[:10]}@example.com"
        self.client.post("/auth/register", json={"full_name": "Pw Test", "identifier": email,
                                                 "password": self.password, "password_confirm": self.password},
                         headers={"X-Forwarded-For": f"10.99.{uuid.uuid4().int % 250}.1"})
        a = self.client.post("/auth/login", json={"identifier": email, "password": self.password}).json()
        b = self.client.post("/auth/login", json={"identifier": email, "password": self.password}).json()
        r = self.client._send("PUT", "/users/me/password", {"current_password": self.password, "new_password": "Neu12345!"},
                              {"Authorization": f"Bearer {a['access_token']}"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self._me(a["access_token"]), 401)
        self.assertEqual(self._me(b["access_token"]), 401)

    # --- Telegram WebApp login (needs the server's TELEGRAM_BOT_TOKEN) ---

    @unittest.skipUnless(os.environ.get("VIZU_AUTH_FLOW_TG_TOKEN"), "set VIZU_AUTH_FLOW_TG_TOKEN = the server's TELEGRAM_BOT_TOKEN")
    def test_telegram_login_session_is_revocable(self):
        import hashlib
        import hmac
        import time
        from urllib.parse import urlencode

        fields = {"auth_date": str(int(time.time())), "query_id": "q1",
                  "user": json.dumps({"id": 777000000 + uuid.uuid4().int % 100000, "first_name": "Tg", "username": "tg_flow"})}
        check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
        secret = hmac.new(b"WebAppData", os.environ["VIZU_AUTH_FLOW_TG_TOKEN"].encode(), hashlib.sha256).digest()
        fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        r = self.client.post("/auth/telegram", json={"init_data": urlencode(fields)})
        self.assertEqual(r.status_code, 200, r.text)
        tokens = r.json()
        self.assertEqual(self._me(tokens["access_token"]), 200)
        new = self.client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).json()
        self.client.post("/auth/logout", json={"refresh_token": new["refresh_token"]})
        self.assertEqual(self._me(tokens["access_token"]), 401)
        tampered = urlencode({**fields, "hash": "0" * 64})
        self.assertEqual(self.client.post("/auth/telegram", json={"init_data": tampered}).status_code, 401)

    # --- SUPER_ADMIN second step (needs a SUPER_ADMIN + the server's secret) ---

    def _admin_login(self):
        email, password = os.environ.get("VIZU_AUTH_FLOW_ADMIN_EMAIL"), os.environ.get("VIZU_AUTH_FLOW_ADMIN_PASSWORD")
        if not (email and password):
            self.skipTest("set VIZU_AUTH_FLOW_ADMIN_EMAIL / _PASSWORD for a SUPER_ADMIN in the test database")
        r = self.client.post("/auth/login", json={"identifier": email, "password": password})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_super_admin_second_step(self):
        secret = os.environ.get("VIZU_AUTH_FLOW_ADMIN_VERIFY")
        if not secret:
            self.skipTest("set VIZU_AUTH_FLOW_ADMIN_VERIFY = the server's SUPER_ADMIN_VERIFICATION_PASSWORD")
        admin = self._admin_login()
        hdr = {"Authorization": f"Bearer {admin['access_token']}"}
        self.assertEqual(self.client.post("/auth/verify-admin-password", json={"password": "wrong"}, headers=hdr).status_code, 403)
        self.assertEqual(self.client.post("/auth/verify-admin-password", json={"password": secret}, headers=hdr).status_code, 200)
        student = self._login(True)
        r = self.client.post("/auth/verify-admin-password", json={"password": secret},
                             headers={"Authorization": f"Bearer {student['access_token']}"})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.client.post("/auth/verify-admin-password", json={"password": secret}).status_code, 401)


if __name__ == "__main__":
    unittest.main()
