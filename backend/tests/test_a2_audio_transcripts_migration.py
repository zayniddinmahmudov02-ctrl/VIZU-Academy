"""Migration c4f7a9e2d6b3 (a2_audio_transcripts): upgrade -> downgrade ->
upgrade on a throwaway database. Runs only with VIZU_MIGRATION_TEST_DB_URL (a
database of its own, at head): it changes the schema, so it must never share
the database of the other integration tests."""

import os
import unittest
import uuid

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "c4f7a9e2d6b3", "b8e3d1a7c5f2"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestA2AudioTranscriptsMigration(unittest.TestCase):
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

    def _exists(self) -> bool:
        return bool(self._q("SELECT 1 FROM information_schema.tables WHERE table_name = 'a2_audio_transcripts'"))

    def test_upgrade_downgrade_upgrade(self):
        from sqlalchemy.exc import IntegrityError

        self._alembic("upgrade", "head")
        self.assertTrue(self._exists())
        insert = ("INSERT INTO a2_audio_transcripts (id, sha256, original_name, status) VALUES (:id, :sha, 'A2 1.mp3', :status)")
        sha = uuid.uuid4().hex * 2
        self._q(insert, id=uuid.uuid4(), sha=sha, status="TRANSCRIBED")
        row = self._q("SELECT storage_paths, matches FROM a2_audio_transcripts WHERE sha256 = :sha", sha=sha)[0]
        self.assertEqual((row[0], row[1]), ([], {}))  # server defaults
        with self.assertRaises(IntegrityError):
            self._q(insert, id=uuid.uuid4(), sha=sha, status="TRANSCRIBED")  # one row per content
        with self.assertRaises(IntegrityError):
            self._q(insert, id=uuid.uuid4(), sha=uuid.uuid4().hex * 2, status="DONE")
        self._alembic("downgrade", PREVIOUS_REV)
        self.assertFalse(self._exists())
        self._alembic("upgrade", REV)
        self.assertTrue(self._exists())
        self.assertEqual(self._q("SELECT count(*) FROM a2_audio_transcripts")[0][0], 0)


if __name__ == "__main__":
    unittest.main()
