"""Migration e6d2b9a4c8f3 (kompetenzen.audio_file_id = the one shared Hören audio of Modelltest 1): upgrade -> downgrade -> upgrade on a throwaway database
(VIZU_MIGRATION_TEST_DB_URL, a database of its own at head). The column, its foreign key and its index appear and disappear; Kompetenzen that already exist keep
every value; deleting the audio file clears the link (ON DELETE SET NULL) instead of deleting the section."""

import os
import unittest
import uuid

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "e6d2b9a4c8f3", "d4b9e2a7c3f1"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestSharedAudioMigration(unittest.TestCase):
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
        return bool(self._q("SELECT 1 FROM information_schema.columns WHERE table_name = 'kompetenzen' AND column_name = 'audio_file_id'"))

    def _index(self):
        return bool(self._q("SELECT 1 FROM pg_indexes WHERE tablename = 'kompetenzen' AND indexname = 'ix_kompetenzen_audio_file_id'"))

    def test_upgrade_downgrade_upgrade_keeps_existing_rows(self):
        from sqlalchemy.orm import Session

        import app.models  # noqa: F401
        from app.models.audio_file import AudioFile
        from app.models.certification_provider import CertificationProvider
        from app.models.kompetenz import Kompetenz
        from app.models.mock_exam_level import MockExamLevel
        from app.models.model_test import ModelTest

        tag = uuid.uuid4().hex[:6]
        with Session(self.engine) as db:
            provider = CertificationProvider(name=f"MSM {tag}", code=f"MSM{tag}", is_active=True)
            db.add(provider)
            db.flush()
            level = MockExamLevel(provider_id=provider.id, level="B1–C1", title=f"MSM level {tag}", is_active=True)
            db.add(level)
            db.flush()
            test = ModelTest(level_id=level.id, title="Modelltest M", status="DRAFT", sort_order=1)
            db.add(test)
            db.flush()
            komp = Kompetenz(model_test_id=test.id, type="HOEREN", title="Hören", total_points=35, duration_minutes=60, sort_order=2)
            audio = AudioFile(storage_path=f"msm-{tag}.wav", kind="ORIGINAL", content_type="audio/wav", size_bytes=10, duration_ms=1000, sha256="0" * 64)
            db.add_all([komp, audio])
            db.commit()
            ids = dict(provider=provider.id, komp=komp.id, audio=audio.id)
        try:
            self._alembic("downgrade", PREVIOUS_REV)
            self.assertEqual((self._column(), self._index()), (False, False))
            self.assertEqual(self._q("SELECT title, duration_minutes, total_points FROM kompetenzen WHERE id = :i", i=ids["komp"]), [("Hören", 60, 35)])
            self._alembic("upgrade", REV)
            self.assertEqual((self._column(), self._index()), (True, True))
            self.assertEqual(self._q("SELECT audio_file_id, duration_minutes FROM kompetenzen WHERE id = :i", i=ids["komp"]), [(None, 60)])
            # the link works, and deleting the audio file clears it instead of deleting the section
            self._q("UPDATE kompetenzen SET audio_file_id = :a WHERE id = :i", a=ids["audio"], i=ids["komp"])
            self.assertEqual(self._q("SELECT audio_file_id FROM kompetenzen WHERE id = :i", i=ids["komp"]), [(ids["audio"],)])
            self._q("DELETE FROM audio_files WHERE id = :a", a=ids["audio"])
            self.assertEqual(self._q("SELECT audio_file_id, title FROM kompetenzen WHERE id = :i", i=ids["komp"]), [(None, "Hören")])
        finally:
            self._alembic("upgrade", "head")
            self._q("DELETE FROM certification_providers WHERE id = :p", p=ids["provider"])
            self._q("DELETE FROM audio_files WHERE id = :a", a=ids["audio"])


if __name__ == "__main__":
    unittest.main()
