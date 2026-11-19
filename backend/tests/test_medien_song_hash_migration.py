"""Migration e8a3c5f1b7d2 (songs.sha256): upgrade -> downgrade -> upgrade on a throwaway database (VIZU_MIGRATION_TEST_DB_URL, at head): the column
and its index appear and disappear; an existing song row survives with an empty hash."""

import os
import unittest
import uuid

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "e8a3c5f1b7d2", "d5f1b8e3a9c7"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestSongHashMigration(unittest.TestCase):
    def setUp(self):
        from pathlib import Path

        from alembic.config import Config
        from sqlalchemy import create_engine

        root = Path(__file__).resolve().parents[1]
        self.cfg = Config()
        self.cfg.set_main_option("script_location", str(root / "alembic"))
        self.engine = create_engine(DB_URL)
        self.song = uuid.uuid4()

    def tearDown(self):
        self._alembic("upgrade", "head")
        self._q("DELETE FROM songs WHERE id = :id", id=self.song)
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
        column = self._q("SELECT 1 FROM information_schema.columns WHERE table_name = 'songs' AND column_name = 'sha256'")
        index = self._q("SELECT 1 FROM pg_indexes WHERE tablename = 'songs' AND indexname = 'ix_songs_sha256'")
        return bool(column), bool(index)

    def test_upgrade_downgrade_upgrade(self):
        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._state(), (False, False))
        self._q("INSERT INTO songs (id, title, language, access_type, is_special_offer, is_featured, status, play_count, metadata_status) "
                "VALUES (:id, 'mig-song', 'de', 'FREE', false, false, 'PUBLISHED', 0, 'OK')", id=self.song)
        self._alembic("upgrade", REV)
        self.assertEqual(self._state(), (True, True))
        self.assertEqual(self._q("SELECT sha256 FROM songs WHERE id = :id", id=self.song), [(None,)])
        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._state(), (False, False))
        self.assertEqual(len(self._q("SELECT 1 FROM songs WHERE id = :id", id=self.song)), 1)
        self._alembic("upgrade", REV)
        self.assertEqual(self._state(), (True, True))


if __name__ == "__main__":
    unittest.main()
