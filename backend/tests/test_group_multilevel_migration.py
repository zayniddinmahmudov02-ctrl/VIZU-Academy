"""Migration b6e3d9a2c5f8 (Multilevel groups): upgrade -> downgrade -> upgrade on a throwaway database (VIZU_MIGRATION_TEST_DB_URL, a database
of its own at head). `study_groups.mock_exam_level_id` (nullable uuid, FK SET NULL, index) exists after the upgrade and is gone after the
downgrade while the groups stay."""

import os
import unittest

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "b6e3d9a2c5f8", "a4c9e1f7b2d6"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestGroupMultilevelMigration(unittest.TestCase):
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

    def _state(self):
        col = self._q("SELECT is_nullable, data_type FROM information_schema.columns WHERE table_name = 'study_groups' AND column_name = 'mock_exam_level_id'")
        fk = self._q("SELECT confdeltype FROM pg_constraint WHERE conname = 'fk_study_groups_mock_exam_level_id'")
        ix = self._q("SELECT 1 FROM pg_indexes WHERE indexname = 'ix_study_groups_mock_exam_level_id'")
        return (tuple(col[0]) if col else None, fk[0][0] if fk else None, bool(ix))

    def test_upgrade_downgrade_upgrade(self):
        self._alembic("upgrade", "head")
        self.assertEqual(self._state(), (("YES", "uuid"), "n", True))  # n = ON DELETE SET NULL
        rows = self._q("SELECT count(*) FROM study_groups")[0][0]

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._state(), (None, None, False))
        self.assertEqual(self._q("SELECT count(*) FROM study_groups")[0][0], rows)

        self._alembic("upgrade", REV)
        self.assertEqual(self._state(), (("YES", "uuid"), "n", True))


if __name__ == "__main__":
    unittest.main()
