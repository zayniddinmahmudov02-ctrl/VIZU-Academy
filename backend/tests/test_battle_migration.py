"""Migration e5a9c3f1b7d2 (VIZU DEUTSCH BATTLE tables): upgrade -> downgrade -> upgrade on a throwaway
database. Runs only with VIZU_MIGRATION_TEST_DB_URL (a database of its own, at head): it changes the schema,
so it must never share the database of the other integration tests."""

import os
import unittest

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "e5a9c3f1b7d2", "d7e2b4f8a1c6"
TABLES = {"battle_profiles", "battle_images", "battle_words", "battle_matches", "battle_answers", "battle_points_ledger", "battle_themes"}


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestBattleMigration(unittest.TestCase):
    def setUp(self):
        from pathlib import Path

        from alembic.config import Config
        from sqlalchemy import create_engine

        root = Path(__file__).resolve().parents[1]
        # no ini file: env.py would run logging.fileConfig() and silence the app's loggers for later tests
        self.cfg = Config()
        self.cfg.set_main_option("script_location", str(root / "alembic"))
        self.engine = create_engine(DB_URL)

    def tearDown(self):
        self._alembic("upgrade", "head")
        self.engine.dispose()

    def _alembic(self, action: str, revision: str) -> None:
        """env.py builds its URL from settings — point it at THIS database, never the shared test DB."""
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
        return {r[0] for r in self._q("SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'battle_%'")}

    def test_upgrade_downgrade_upgrade(self):
        self._alembic("upgrade", "head")
        self.assertEqual(self._tables(), TABLES)
        before = self._q("SELECT count(*) FROM dictionary_entries")[0][0]
        rule = self._q("SELECT confdeltype FROM pg_constraint WHERE conname = 'battle_words_entry_id_fkey'")
        self.assertEqual(rule[0][0], "n")  # ON DELETE SET NULL: a Wörterbuch re-import is never blocked
        self._q("INSERT INTO battle_themes (id, level, city, title) VALUES (gen_random_uuid(), 'A1', 'Berlin', 'Tor')")

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._tables(), set())
        self.assertEqual(self._q("SELECT count(*) FROM dictionary_entries")[0][0], before)

        self._alembic("upgrade", REV)
        self.assertEqual(self._tables(), TABLES)
        self.assertEqual(self._q("SELECT count(*) FROM battle_themes")[0][0], 0)
        uniques = {r[0] for r in self._q("SELECT conname FROM pg_constraint WHERE conname LIKE 'uq_battle_%'")}
        self.assertTrue({"uq_battle_profiles_user_id", "uq_battle_words_entry_id", "uq_battle_answer_round_slot", "uq_battle_points_ledger_event"} <= uniques)


if __name__ == "__main__":
    unittest.main()
