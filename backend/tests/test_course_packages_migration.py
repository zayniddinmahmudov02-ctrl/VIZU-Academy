"""Migration c7e1f3a9b2d5 (course packages, order snapshots, promo approval): upgrade -> downgrade -> upgrade on a
throwaway database (VIZU_MIGRATION_TEST_DB_URL, a database of its own at head), plus 401 / 403 of the new endpoints."""

import os
import unittest
import uuid

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "c7e1f3a9b2d5", "a3c9e7b5d1f4"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestCoursePackagesMigration(unittest.TestCase):
    def setUp(self):
        from pathlib import Path

        from alembic.config import Config
        from sqlalchemy import create_engine

        root = Path(__file__).resolve().parents[1]
        self.cfg = Config()  # no ini file: env.py's fileConfig() would silence the app's loggers
        self.cfg.set_main_option("script_location", str(root / "alembic"))
        self.engine = create_engine(DB_URL)

    def tearDown(self):
        self._alembic("upgrade", "head")
        self.engine.dispose()

    def _alembic(self, action: str, revision: str) -> None:
        from unittest.mock import patch

        from alembic import command
        from sqlalchemy.engine import make_url

        from app.core.config import settings

        url = make_url(DB_URL)
        with patch.multiple(settings, DATABASE_HOST=url.host, DATABASE_PORT=url.port or 5432, DATABASE_NAME=url.database,
                            DATABASE_USER=url.username, DATABASE_PASSWORD=url.password or ""):
            getattr(command, action)(self.cfg, revision)

    def _q(self, sql, **params):
        from sqlalchemy import text

        with self.engine.begin() as c:
            result = c.execute(text(sql), params)
            return result.fetchall() if result.returns_rows else []

    def _tables(self):
        return {r[0] for r in self._q("SELECT table_name FROM information_schema.tables WHERE table_name IN ('course_packages','promo_code_requests')")}

    def test_upgrade_downgrade_upgrade(self):
        self._alembic("upgrade", "head")
        self.assertEqual(self._tables(), {"course_packages", "promo_code_requests"})
        rows = dict(self._q("SELECT code, status FROM course_packages"))
        self.assertEqual(rows["B2_C1"], "COMING_SOON")
        self.assertEqual(rows["A1_C1"], "ACTIVE")
        self.assertEqual(self._q("SELECT price, duration_days FROM course_packages WHERE code='B1'")[0], (100_000, 60))
        orders = self._q("SELECT count(*) FROM subscription_orders")[0][0]

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._tables(), set())
        self.assertEqual(self._q("SELECT count(*) FROM subscription_orders")[0][0], orders)
        cols = {r[0] for r in self._q("SELECT column_name FROM information_schema.columns WHERE table_name='promo_codes'")}
        self.assertNotIn("requires_approval", cols)

        self._alembic("upgrade", REV)
        self.assertEqual(len(self._q("SELECT code FROM course_packages")), 8)


class TestNewEndpointsAuth(unittest.TestCase):
    def test_401_403(self):
        try:
            from fastapi.testclient import TestClient
        except Exception:  # httpx missing (server)
            self.skipTest("httpx not installed")
        from types import SimpleNamespace

        from app.api.dependencies.auth import get_current_user
        from app.main import app

        client = TestClient(app)
        rid = uuid.uuid4()
        admin_calls = [("get", "/api/v1/admin/vizu-pay/packages", None), ("post", "/api/v1/admin/vizu-pay/packages", {"code": "X"}),
                       ("put", "/api/v1/admin/vizu-pay/packages/A1", {"price": 1}),
                       ("get", "/api/v1/admin/vizu-pay/promo-requests", None),
                       ("post", f"/api/v1/admin/vizu-pay/promo-requests/{rid}/review", {"approve": True}),
                       ("get", "/api/v1/admin/vizu-pay/discount-statistics", None)]
        student_calls = [("get", "/api/v1/vizu-pay/promo/requests", None), ("post", "/api/v1/vizu-pay/promo/requests", {"code": "A", "plan": "A1"})]
        for method, url, body in admin_calls + student_calls:
            self.assertEqual(getattr(client, method)(url, **({"json": body} if body else {})).status_code, 401, url)
        for role in ("ADMIN", "CONTENT_MANAGER", "PAYMENT_MANAGER", "STUDENT"):
            app.dependency_overrides[get_current_user] = lambda role=role: SimpleNamespace(id=uuid.uuid4(), role=role)
            try:
                for method, url, body in admin_calls:
                    with self.subTest(role=role, url=url):
                        self.assertEqual(getattr(client, method)(url, **({"json": body} if body else {})).status_code, 403)
            finally:
                app.dependency_overrides.pop(get_current_user, None)


if __name__ == "__main__":
    unittest.main()
