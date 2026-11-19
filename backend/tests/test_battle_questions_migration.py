"""Migration a6c2e8f4b9d1 (battle_questions): upgrade -> downgrade -> upgrade on a throwaway database (VIZU_MIGRATION_TEST_DB_URL, at
head): the table appears with its unique keys (level + norm_key, seed_id) and disappears again; the picture words are untouched."""

import os
import unittest
import uuid

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "a6c2e8f4b9d1", "f3b9d1a6c4e8"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestBattleQuestionsMigration(unittest.TestCase):
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
        self._q("DELETE FROM battle_questions WHERE norm_key LIKE 'mig-test|%'")
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

    def _has_table(self):
        return bool(self._q("SELECT 1 FROM information_schema.tables WHERE table_name = 'battle_questions'"))

    def test_upgrade_downgrade_upgrade(self):
        from sqlalchemy.exc import IntegrityError

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertFalse(self._has_table())
        self.assertTrue(self._q("SELECT 1 FROM information_schema.tables WHERE table_name = 'battle_words'"))
        self._alembic("upgrade", REV)
        self.assertTrue(self._has_table())
        insert = ("INSERT INTO battle_questions (id, level, kind, format, topic, prompt, answer, wrong, norm_key) "
                  "VALUES (:id, 'A1', 'vocab', 'de_uz', 'essen', 'der Apfel', 'olma', '[\"non\", \"suv\", \"tuz\"]', 'mig-test|der apfel')")
        self._q(insert, id=uuid.uuid4())
        self.assertEqual(self._q("SELECT status, source FROM battle_questions WHERE norm_key = 'mig-test|der apfel'"), [("draft", "admin")])
        with self.assertRaises(IntegrityError):  # the same question twice in one level
            self._q(insert, id=uuid.uuid4())
        self._alembic("downgrade", PREVIOUS_REV)
        self.assertFalse(self._has_table())
        self._alembic("upgrade", REV)
        self.assertTrue(self._has_table())


if __name__ == "__main__":
    unittest.main()
