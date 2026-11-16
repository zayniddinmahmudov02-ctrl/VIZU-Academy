"""Migration d4b9e2a7c3f1 (Multilevel: mock_questions.answer_key, mock_attempt_sections.duration_seconds): upgrade -> downgrade -> upgrade on a throwaway database
(VIZU_MIGRATION_TEST_DB_URL, a database of its own at head). The two columns appear and disappear; questions and attempt sections that already exist keep every
other value, and the sections get duration_seconds = deadline_at - started_at on upgrade."""

import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "d4b9e2a7c3f1", "c2f7a9d1e4b6"
COLUMNS = {("mock_questions", "answer_key"), ("mock_attempt_sections", "duration_seconds")}


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestMultilevelKeysMigration(unittest.TestCase):
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

    def _columns(self):
        return {(r[0], r[1]) for r in self._q("SELECT table_name, column_name FROM information_schema.columns WHERE table_name IN ('mock_questions','mock_attempt_sections')")} & COLUMNS

    def test_upgrade_downgrade_upgrade_keeps_existing_rows(self):
        from sqlalchemy import select
        from sqlalchemy.orm import Session

        import app.models  # noqa: F401
        from app.models.certification_provider import CertificationProvider
        from app.models.kompetenz import Kompetenz
        from app.models.mock_attempt_section import MockAttemptSection
        from app.models.mock_exam_level import MockExamLevel
        from app.models.mock_question import MockQuestion
        from app.models.mock_test_attempt import MockTestAttempt
        from app.models.model_test import ModelTest
        from app.models.reading_content import ReadingContent
        from app.models.teil import Teil
        from app.models.user import User

        tag = uuid.uuid4().hex[:6]
        started = datetime(2026, 11, 16, 10, 0, 0, tzinfo=timezone.utc)
        with Session(self.engine) as db:
            user = User(email=f"mkm-{tag}@test.local", username=f"mkm_{tag}", password_hash="x", is_active=True, is_verified=True, is_superuser=False,
                        role="STUDENT", is_banned=False, preferred_language="uz")
            provider = CertificationProvider(name=f"MKM {tag}", code=f"MKM{tag}", is_active=True)
            db.add_all([user, provider])
            db.flush()
            level = MockExamLevel(provider_id=provider.id, level="B1–C1", title=f"MKM level {tag}", is_active=True)
            db.add(level)
            db.flush()
            test = ModelTest(level_id=level.id, title="Modelltest M", status="DRAFT", sort_order=1)
            db.add(test)
            db.flush()
            komp = Kompetenz(model_test_id=test.id, type="LESEN", title="Lesen", total_points=0, duration_minutes=60, sort_order=1)
            db.add(komp)
            db.flush()
            teil = Teil(kompetenz_id=komp.id, title="Teil 1", points=0, sort_order=1)
            db.add(teil)
            db.flush()
            content = ReadingContent(teil_id=teil.id, content_type="TEXT", text="Text")
            db.add(content)
            db.flush()
            question = MockQuestion(reading_content_id=content.id, question_type="SINGLE_CHOICE", question_text="A1", points=1, sort_order=1, answer_key="b")
            attempt = MockTestAttempt(model_test_id=test.id, user_id=user.id, status="IN_PROGRESS", max_score=300)
            db.add_all([question, attempt])
            db.flush()
            section = MockAttemptSection(attempt_id=attempt.id, kompetenz_id=komp.id, section_type="LESEN", status="OPEN", started_at=started,
                                         deadline_at=started + timedelta(minutes=60), duration_seconds=3600)
            db.add(section)
            db.commit()
            ids = dict(user=user.id, provider=provider.id, question=question.id, section=section.id)
        try:
            self._alembic("downgrade", PREVIOUS_REV)
            self.assertEqual(self._columns(), set())
            self.assertEqual(self._q("SELECT question_text, points FROM mock_questions WHERE id = :i", i=ids["question"]), [("A1", 1)])
            self.assertEqual(self._q("SELECT status, score FROM mock_attempt_sections WHERE id = :i", i=ids["section"]), [("OPEN", None)])
            self._alembic("upgrade", REV)
            self.assertEqual(self._columns(), COLUMNS)
            # rows from before the migration: no key typed (NULL), the granted length is the difference of the two timestamps
            self.assertEqual(self._q("SELECT answer_key, question_text FROM mock_questions WHERE id = :i", i=ids["question"]), [(None, "A1")])
            self.assertEqual(self._q("SELECT duration_seconds, status FROM mock_attempt_sections WHERE id = :i", i=ids["section"]), [(3600, "OPEN")])
            # the model still works against the migrated schema
            with Session(self.engine) as db:
                self.assertEqual(db.scalar(select(MockAttemptSection.duration_seconds).where(MockAttemptSection.id == ids["section"])), 3600)
        finally:
            self._alembic("upgrade", "head")
            with Session(self.engine) as db:
                db.execute(CertificationProvider.__table__.delete().where(CertificationProvider.id == ids["provider"]))
                db.execute(User.__table__.delete().where(User.id == ids["user"]))
                db.commit()


if __name__ == "__main__":
    unittest.main()
