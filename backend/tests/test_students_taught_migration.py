"""Migration f3b8d2a6c9e1 (teacher's own career figure): upgrade -> downgrade -> upgrade on a throwaway database
(VIZU_MIGRATION_TEST_DB_URL, a database of its own at head). `teacher_profiles.students_taught_total` exists (nullable) with the
check 0 … 1 000 000 after the upgrade and is gone after the downgrade while the rows stay."""

import os
import unittest

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "f3b8d2a6c9e1", "e2a7c4f9b1d3"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestStudentsTaughtMigration(unittest.TestCase):
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

    def _q(self, sql, **params):
        from sqlalchemy import text

        with self.engine.begin() as c:
            result = c.execute(text(sql), params)
            return result.fetchall() if result.returns_rows else []

    def _column(self):
        rows = self._q("SELECT is_nullable FROM information_schema.columns WHERE table_name = 'teacher_profiles' AND column_name = 'students_taught_total'")
        return rows[0][0] if rows else None

    def test_upgrade_downgrade_upgrade(self):
        self._alembic("upgrade", "head")
        self.assertEqual(self._column(), "YES")
        check = self._q("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'ck_teacher_profiles_students_taught'")[0][0]
        self.assertIn("1000000", check)
        rows = self._q("SELECT count(*) FROM teacher_profiles")[0][0]

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertIsNone(self._column())
        self.assertEqual(self._q("SELECT count(*) FROM pg_constraint WHERE conname = 'ck_teacher_profiles_students_taught'")[0][0], 0)
        self.assertEqual(self._q("SELECT count(*) FROM teacher_profiles")[0][0], rows)

        self._alembic("upgrade", REV)
        self.assertEqual(self._column(), "YES")


if __name__ == "__main__":
    unittest.main()
