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


if __name__ == "__main__":
    unittest.main()
