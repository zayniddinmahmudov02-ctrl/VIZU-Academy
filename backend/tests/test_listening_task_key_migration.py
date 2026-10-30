"""Migration b8e3d1a7c5f2 (listenings.task_key): upgrade -> downgrade ->
upgrade on a throwaway database. Runs only with VIZU_MIGRATION_TEST_DB_URL (a
database of its own, at head): it changes the schema, so it must never share
the database of the other integration tests."""

import os
import unittest
import uuid

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "b8e3d1a7c5f2", "a6d2f9c4e8b1"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestListeningTaskKeyMigration(unittest.TestCase):
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

    def _columns(self):
        return {r[0] for r in self._q("SELECT column_name FROM information_schema.columns WHERE table_name = 'listenings'")}

    def _lesson(self):
        """A lesson row to hang test tasks on (course -> module -> lesson), created if the database has none."""
        row = self._q("SELECT id FROM lessons LIMIT 1")
        if row:
            return row[0][0], None
        language = self._q("SELECT id FROM languages LIMIT 1")
        language = language[0][0] if language else None
        if language is None:
            language = uuid.uuid4()
            self._q("INSERT INTO languages (id, code, locale, name, is_active, is_default, sort_order, created_at, updated_at) "
                    "VALUES (:id, 'de', 'de-DE', 'Deutsch', true, false, 1, now(), now())", id=language)
        course, module, lesson = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        self._q("INSERT INTO courses (id, title, language_id, level, is_active, order_index, created_at, updated_at) "
                "VALUES (:id, 'Mig', :lang, 'A2', true, 99, now(), now())", id=course, lang=language)
        self._q("INSERT INTO modules (id, course_id, title, number, is_active, order_index, created_at, updated_at) "
                "VALUES (:id, :c, 'Mig', 1, true, 1, now(), now())", id=module, c=course)
        self._q("INSERT INTO lessons (id, module_id, title, number, is_free, duration, created_at, updated_at) "
                "VALUES (:id, :m, 'Mig', 1, false, 0, now(), now())", id=lesson, m=module)
        return lesson, course

    def test_upgrade_downgrade_upgrade_keeps_tasks(self):
        from sqlalchemy.exc import IntegrityError

        self._alembic("upgrade", "head")
        self.assertIn("task_key", self._columns())
        lesson, made_course = self._lesson()
        plain, keyed = uuid.uuid4(), uuid.uuid4()
        insert = ("INSERT INTO listenings (id, lesson_id, title, order_index, is_published, task_key, created_at, updated_at) "
                  "VALUES (:id, :l, :t, 1, false, :k, now(), now())")
        self._q(insert, id=plain, l=lesson, t="ohne Schlüssel", k=None)
        self._q(insert, id=keyed, l=lesson, t="Hören: Text 1", k=f"mig-text-{keyed.hex[:6]}")
        self._q(insert, id=uuid.uuid4(), l=lesson, t="noch einer ohne", k=None)  # NULL is not unique-checked
        with self.assertRaises(IntegrityError):
            self._q(insert, id=uuid.uuid4(), l=lesson, t="Kopie", k=f"mig-text-{keyed.hex[:6]}")
        before = self._q("SELECT count(*) FROM listenings")[0][0]

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertNotIn("task_key", self._columns())
        self.assertEqual(self._q("SELECT count(*) FROM listenings")[0][0], before)  # the tasks stay
        self.assertEqual(self._q("SELECT title FROM listenings WHERE id = :id", id=keyed)[0][0], "Hören: Text 1")

        self._alembic("upgrade", REV)
        self.assertIn("task_key", self._columns())
        self.assertIsNone(self._q("SELECT task_key FROM listenings WHERE id = :id", id=keyed)[0][0])
        index = self._q("SELECT indexdef FROM pg_indexes WHERE indexname = 'uq_listenings_task_key'")
        self.assertIn("UNIQUE", index[0][0])
        self.assertIn("WHERE (task_key IS NOT NULL)", index[0][0])
        self._q("DELETE FROM listenings WHERE lesson_id = :l AND title IN ('ohne Schlüssel', 'Hören: Text 1', 'noch einer ohne')", l=lesson)
        if made_course:
            self._q("DELETE FROM courses WHERE id = :id", id=made_course)


if __name__ == "__main__":
    unittest.main()
