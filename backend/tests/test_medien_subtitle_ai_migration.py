"""Migration d5f1b8e3a9c7 (AI subtitles): upgrade -> downgrade -> upgrade on a throwaway database (VIZU_MIGRATION_TEST_DB_URL, a database of
its own at head): the job table and the new subtitle columns appear and disappear; an existing track is APPROVED / UPLOAD after the upgrade
(students keep seeing it) and survives the downgrade."""

import os
import unittest
import uuid

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "d5f1b8e3a9c7", "a7c4e2f9b1d8"
COLUMNS = {"status", "source", "source_language", "ai_model", "approved_at", "approved_by_id", "edited_at"}


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestSubtitleAIMigration(unittest.TestCase):
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
        self._q(f"DELETE FROM films WHERE title = 'mig-{self.id()[-8:]}'")
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
        tables = {r[0] for r in self._q("SELECT table_name FROM information_schema.tables WHERE table_name = 'film_subtitle_jobs'")}
        columns = {r[0] for r in self._q("SELECT column_name FROM information_schema.columns WHERE table_name = 'film_subtitles'")} & COLUMNS
        return tables, columns

    def test_upgrade_downgrade_upgrade(self):
        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._state(), (set(), set()))
        film, track = uuid.uuid4(), uuid.uuid4()
        self._q("INSERT INTO films (id, title, language, access_type, is_special_offer, is_featured, status, processing_status, view_count) "
                "VALUES (:id, :t, 'de', 'FREE', false, false, 'PUBLISHED', 'NONE', 0)", id=film, t=f"mig-{self.id()[-8:]}")
        self._q("INSERT INTO film_subtitles (id, film_id, language, label, file_key) VALUES (:id, :f, 'de', 'Deutsch', 'subtitles/x.vtt')", id=track, f=film)

        self._alembic("upgrade", REV)
        self.assertEqual(self._state(), ({"film_subtitle_jobs"}, COLUMNS))
        self.assertEqual(self._q("SELECT status, source FROM film_subtitles WHERE id = :id", id=track), [("APPROVED", "UPLOAD")])
        indexes = {r[0] for r in self._q("SELECT indexname FROM pg_indexes WHERE tablename = 'film_subtitle_jobs'")}
        self.assertIn("uq_film_subtitle_jobs_active", indexes)

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._state(), (set(), set()))
        self.assertEqual(len(self._q("SELECT 1 FROM film_subtitles WHERE id = :id", id=track)), 1)

        self._alembic("upgrade", REV)
        self.assertEqual(self._state(), ({"film_subtitle_jobs"}, COLUMNS))


if __name__ == "__main__":
    unittest.main()
