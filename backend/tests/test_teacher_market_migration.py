"""Migration d9e4a1c7b3f5 (My Teacher marketplace): upgrade -> downgrade -> upgrade on a throwaway database. Runs only with
VIZU_MIGRATION_TEST_DB_URL (a database of its own, at head): it changes the schema, so it must never share the database of
the other integration tests. Checks the new tables and constraints, that a group video room still needs its group (owner
check) and that the downgrade keeps users and group rooms."""

import os
import unittest

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "d9e4a1c7b3f5", "c8d3f5a1e7b2"
TABLES = ("teacher_certificates", "teacher_courses", "teacher_course_enrollments", "teacher_course_interests", "teacher_reviews",
          "teacher_review_reports", "special_lessons", "special_lesson_signups")


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestTeacherMarketMigration(unittest.TestCase):
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

    def _tables(self) -> set:
        return {r[0] for r in self._q("SELECT table_name FROM information_schema.tables WHERE table_name = ANY(:t)", t=list(TABLES))}

    def _columns(self, table: str) -> set:
        return {r[0] for r in self._q("SELECT column_name FROM information_schema.columns WHERE table_name = :t", t=table)}

    def test_upgrade_downgrade_upgrade(self):
        from sqlalchemy.exc import IntegrityError

        self._alembic("upgrade", "head")
        self.assertEqual(self._tables(), set(TABLES))
        self.assertTrue({"photo_path", "verified", "catalog_hidden", "rating_avg"} <= self._columns("teacher_profiles"))
        self.assertTrue({"special_lesson_id", "hard_end_at", "students_camera_allowed"} <= self._columns("video_rooms"))
        self.assertIn("can_video", self._columns("video_room_participants"))
        self.assertIn("teacher_course_id", self._columns("subscription_orders"))
        users = self._q("SELECT count(*) FROM users")[0][0]
        with self.assertRaises(IntegrityError):  # a room must belong to a group or a lesson
            self._q("INSERT INTO video_rooms (id, room_name, title) VALUES (gen_random_uuid(), 'vizu-x', 'x')")
        checks = dict(self._q("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conname IN "
                              "('ck_special_lessons_duration', 'ck_teacher_reviews_rating', 'ck_teacher_courses_price')"))
        self.assertIn("90", checks["ck_special_lessons_duration"])  # 15–90 minutes only
        self.assertIn("5", checks["ck_teacher_reviews_rating"])
        self.assertIn("FREE", checks["ck_teacher_courses_price"])
        live = self._q("SELECT indexdef FROM pg_indexes WHERE indexname = 'uq_teacher_course_enrollments_live'")[0][0]
        self.assertIn("UNIQUE", live)  # one live enrollment per student and course

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._tables(), set())
        self.assertNotIn("special_lesson_id", self._columns("video_rooms"))
        self.assertNotIn("teacher_course_id", self._columns("subscription_orders"))
        self.assertNotIn("verified", self._columns("teacher_profiles"))
        self.assertEqual(self._q("SELECT count(*) FROM users")[0][0], users)
        self.assertEqual(self._q("SELECT is_nullable FROM information_schema.columns WHERE table_name='video_rooms' AND column_name='group_id'")[0][0], "NO")

        self._alembic("upgrade", REV)
        self.assertEqual(self._tables(), set(TABLES))


if __name__ == "__main__":
    unittest.main()
