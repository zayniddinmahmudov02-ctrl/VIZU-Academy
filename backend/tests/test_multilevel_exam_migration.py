"""Migration a3c9e7b5d1f4 (Multilevel exam mode): upgrade -> downgrade -> upgrade on a throwaway database. Runs only with
VIZU_MIGRATION_TEST_DB_URL (a database of its own, at head): it changes the schema, so it must never share the
database of the other integration tests."""

import os
import unittest

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "a3c9e7b5d1f4", "f2b6d8a4c1e9"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestMultilevelExamMigration(unittest.TestCase):
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

    def _state(self):
        table = bool(self._q("SELECT 1 FROM information_schema.tables WHERE table_name = 'mock_attempt_sections'"))
        cols = {r[0] for r in self._q("SELECT column_name FROM information_schema.columns WHERE table_name = 'mock_test_attempts'")}
        uniques = {r[0] for r in self._q("SELECT conname FROM pg_constraint WHERE conname LIKE 'uq_mock_%'")}
        return table, {"result_level", "result_rule"} <= cols, uniques

    def test_upgrade_downgrade_upgrade(self):
        self._alembic("upgrade", "head")
        table, cols, uniques = self._state()
        self.assertTrue(table and cols)
        self.assertTrue({"uq_mock_question_answers_attempt_question", "uq_mock_writing_submissions_attempt_task",
                         "uq_mock_speaking_submissions_attempt_task", "uq_mock_attempt_sections_attempt_type"} <= uniques)
        attempts = self._q("SELECT count(*) FROM mock_test_attempts")[0][0]

        self._alembic("downgrade", PREVIOUS_REV)
        table, cols, uniques = self._state()
        self.assertFalse(table or cols)
        self.assertNotIn("uq_mock_question_answers_attempt_question", uniques)
        self.assertEqual(self._q("SELECT count(*) FROM mock_test_attempts")[0][0], attempts)

        self._alembic("upgrade", REV)
        self.assertTrue(self._state()[0])


if __name__ == "__main__":
    unittest.main()
