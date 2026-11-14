"""Migration e8b4d2f6a1c3 (audio_files + listening_contents.audio_file_id): upgrade -> downgrade -> upgrade on a throwaway
database (VIZU_MIGRATION_TEST_DB_URL, a database of its own at head), existing Hören content untouched; plus 401 / 403 of
the new endpoints."""

import os
import unittest
import uuid

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "e8b4d2f6a1c3", "c7e1f3a9b2d5"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestAudioFilesMigration(unittest.TestCase):
    def setUp(self):
        from pathlib import Path

        from alembic.config import Config
        from sqlalchemy import create_engine

        root = Path(__file__).resolve().parents[1]
        self.cfg = Config()
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

    def _q(self, sql):
        from sqlalchemy import text

        with self.engine.begin() as c:
            result = c.execute(text(sql))
            return result.fetchall() if result.returns_rows else []

    def test_upgrade_downgrade_upgrade(self):
        self._alembic("upgrade", "head")
        self.assertEqual(self._q("SELECT count(*) FROM information_schema.tables WHERE table_name='audio_files'")[0][0], 1)
        cols = {r[0] for r in self._q("SELECT column_name FROM information_schema.columns WHERE table_name='listening_contents'")}
        self.assertIn("audio_file_id", cols)
        before = self._q("SELECT count(*) FROM listening_contents")[0][0]

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._q("SELECT count(*) FROM information_schema.tables WHERE table_name='audio_files'")[0][0], 0)
        cols = {r[0] for r in self._q("SELECT column_name FROM information_schema.columns WHERE table_name='listening_contents'")}
        self.assertNotIn("audio_file_id", cols)
        self.assertEqual(self._q("SELECT count(*) FROM listening_contents")[0][0], before)  # Hören rows untouched

        self._alembic("upgrade", REV)
        self.assertEqual(self._q("SELECT count(*) FROM information_schema.tables WHERE table_name='audio_files'")[0][0], 1)


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
        i = uuid.uuid4()
        calls = [("get", "/api/v1/admin/multilevel-audio", None), ("get", f"/api/v1/admin/multilevel-audio/slots/{i}", None),
                 ("put", f"/api/v1/admin/multilevel-audio/slots/{i}", {"audio_file_id": str(i)}),
                 ("post", f"/api/v1/admin/multilevel-audio/slots/{i}/trim", {"start_ms": 0, "end_ms": 1000}),
                 ("delete", f"/api/v1/admin/multilevel-audio/slots/{i}", None), ("get", f"/api/v1/admin/multilevel-audio/slots/{i}/file", None),
                 ("post", "/api/v1/admin/audio-files", None), ("post", f"/api/v1/admin/audio-files/{i}/trim", {"start_ms": 0, "end_ms": 1000}),
                 ("get", f"/api/v1/admin/audio-files/{i}", None), ("get", f"/api/v1/admin/audio-files/{i}/file", None)]
        for method, url, body in calls:
            self.assertEqual(getattr(client, method)(url, **({"json": body} if body else {})).status_code, 401, url)
        # STUDENT: nothing; TEACHER (admin-panel read role): reads allowed as everywhere in the panel, every write refused
        for role in ("STUDENT", "TEACHER"):
            app.dependency_overrides[get_current_user] = lambda role=role: SimpleNamespace(id=uuid.uuid4(), role=role)
            try:
                for method, url, body in calls:
                    if role == "TEACHER" and method == "get":
                        continue
                    with self.subTest(role=role, url=url):
                        self.assertEqual(getattr(client, method)(url, **({"json": body} if body else {})).status_code, 403)
            finally:
                app.dependency_overrides.pop(get_current_user, None)
        # the student stream refuses a missing / forged token
        self.assertEqual(client.get(f"/api/v1/multilevel-exam/audio/{i}?token=garbage").status_code, 401)
        self.assertEqual(client.get(f"/api/v1/multilevel-exam/audio/{i}").status_code, 422)


if __name__ == "__main__":
    unittest.main()
