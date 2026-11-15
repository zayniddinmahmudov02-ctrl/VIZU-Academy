"""Migration b6e2d9f4a1c8 (Medienwelt film player): upgrade -> downgrade -> upgrade on a throwaway database
(VIZU_MIGRATION_TEST_DB_URL, a database of its own at head): the new columns and the two new tables appear and disappear, existing
Medienwelt rows and tables stay untouched."""

import os
import unittest

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "b6e2d9f4a1c8", "f4c8a1e6b9d2"
TABLES = {"film_renditions", "media_player_prefs"}
COLUMNS = {("films", "video_duration_ms"), ("media_progress", "player_state"), ("film_subtitles", "cue_count"), ("film_subtitles", "last_ms"),
           ("film_subtitles", "source_format"), ("film_subtitles", "original_name"), ("film_subtitles", "file_size"), ("film_subtitles", "warnings")}


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestMedienPlayerMigration(unittest.TestCase):
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

    def _tables(self):
        names = ", ".join(f"'{t}'" for t in TABLES)
        return {r[0] for r in self._q(f"SELECT table_name FROM information_schema.tables WHERE table_name IN ({names})")}

    def _columns(self):
        return {(r[0], r[1]) for r in self._q("SELECT table_name, column_name FROM information_schema.columns "
                                              "WHERE table_name IN ('films','media_progress','film_subtitles')")} & COLUMNS

    def test_upgrade_downgrade_upgrade(self):
        self._alembic("upgrade", "head")
        self.assertEqual(self._tables(), TABLES)
        self.assertEqual(self._columns(), COLUMNS)
        # defaults of the new subtitle columns, nullable state column
        defaults = dict(self._q("SELECT column_name, column_default FROM information_schema.columns WHERE table_name='film_subtitles' "
                                "AND column_name IN ('cue_count','warnings')"))
        self.assertIn("0", defaults["cue_count"])
        self.assertIn("[]", defaults["warnings"])
        users = self._q("SELECT count(*) FROM users")[0][0]
        categories = self._q("SELECT count(*) FROM media_categories")[0][0]

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._tables(), set())
        self.assertEqual(self._columns(), set())
        self.assertEqual(self._q("SELECT count(*) FROM users")[0][0], users)  # the earlier Medienwelt tables and their rows stay
        self.assertEqual(self._q("SELECT count(*) FROM media_categories")[0][0], categories)
        self.assertEqual(len(self._q("SELECT 1 FROM information_schema.tables WHERE table_name IN ('films','film_subtitles','media_progress')")), 3)

        self._alembic("upgrade", REV)
        self.assertEqual(self._tables(), TABLES)
        self.assertEqual(self._columns(), COLUMNS)


if __name__ == "__main__":
    unittest.main()
