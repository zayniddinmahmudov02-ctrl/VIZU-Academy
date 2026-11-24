"""Migration e2a7c4f9b1d3 (admin who also teaches): upgrade -> downgrade -> upgrade on a throwaway database (VIZU_MIGRATION_TEST_DB_URL,
a database of its own at head). `teacher_profiles.teaches` exists after the upgrade, is NOT NULL with default false (existing
rows = false), and is gone after the downgrade while the rows stay."""

import os
import unittest

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "e2a7c4f9b1d3", "d9e4a1c7b3f5"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestAdminTeachesMigration(unittest.TestCase):
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
        rows = self._q("SELECT is_nullable, column_default FROM information_schema.columns WHERE table_name = 'teacher_profiles' "
                       "AND column_name = 'teaches'")
        return rows[0] if rows else None

    def test_upgrade_downgrade_upgrade(self):
        self._alembic("upgrade", "head")
        nullable, default = self._column()
        self.assertEqual(nullable, "NO")
        self.assertIn("false", default)
        rows = self._q("SELECT count(*) FROM teacher_profiles")[0][0]
        self.assertEqual(self._q("SELECT count(*) FROM teacher_profiles WHERE teaches")[0][0], 0)

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertIsNone(self._column())
        self.assertEqual(self._q("SELECT count(*) FROM teacher_profiles")[0][0], rows)

        self._alembic("upgrade", REV)
        self.assertIsNotNone(self._column())


if __name__ == "__main__":
    unittest.main()
