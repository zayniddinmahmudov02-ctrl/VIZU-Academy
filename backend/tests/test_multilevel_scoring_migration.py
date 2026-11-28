"""Migration c7f4a1e9d3b2 (Multilevel scoring trail): upgrade -> downgrade -> upgrade on a throwaway database (VIZU_MIGRATION_TEST_DB_URL, a
database of its own at head). The eight `mock_attempt_sections` columns, two checks and the ai_status index exist after the upgrade, are
gone after the downgrade, and the section rows stay."""

import os
import unittest

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "c7f4a1e9d3b2", "b6e3d9a2c5f8"
COLUMNS = {"auto_score", "override_score", "score_source", "ai_status", "ai_raw", "ai_raw_max", "ai_claimed_at", "ai_runs"}


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestMultilevelScoringMigration(unittest.TestCase):
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
        cols = {r[0] for r in self._q("SELECT column_name FROM information_schema.columns WHERE table_name = 'mock_attempt_sections'")} & COLUMNS
        checks = {r[0] for r in self._q("SELECT conname FROM pg_constraint WHERE conname IN ('ck_mock_attempt_sections_auto_score_0_75', "
                                        "'ck_mock_attempt_sections_override_0_75')")}
        ix = bool(self._q("SELECT 1 FROM pg_indexes WHERE indexname = 'ix_mock_attempt_sections_ai_status'"))
        return cols, len(checks), ix

    def test_upgrade_downgrade_upgrade(self):
        self._alembic("upgrade", "head")
        self.assertEqual(self._state(), (COLUMNS, 2, True))
        default = self._q("SELECT column_default, is_nullable FROM information_schema.columns WHERE table_name = 'mock_attempt_sections' AND column_name = 'ai_runs'")[0]
        self.assertEqual((default[0], default[1]), ("0", "NO"))
        rows = self._q("SELECT count(*) FROM mock_attempt_sections")[0][0]

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._state(), (set(), 0, False))
        self.assertEqual(self._q("SELECT count(*) FROM mock_attempt_sections")[0][0], rows)

        self._alembic("upgrade", REV)
        self.assertEqual(self._state(), (COLUMNS, 2, True))


if __name__ == "__main__":
    unittest.main()
