"""Migration c8d3f5a1e7b2 (Team / Kontroll / activity / Bibliothek categories): upgrade -> downgrade -> upgrade on a throwaway
database (VIZU_MIGRATION_TEST_DB_URL, at head). The tables and the column appear and go; one open session per user; the six
book categories (old ids kept, old ones inactive, their books moved, nothing deleted) and back."""

import os
import unittest
import uuid

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "c8d3f5a1e7b2", "b7e4c2a9d6f1"
TABLES = {"teacher_profiles", "student_sessions", "student_activity_events"}
SIX = ["Literatur", "Historisch", "Beruflich", "Sonstige", "Prüfungsvorbereitung", "Wortschatz"]


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestTeamKontrollMigration(unittest.TestCase):
    def setUp(self):
        from pathlib import Path

        from alembic.config import Config
        from sqlalchemy import create_engine

        root = Path(__file__).resolve().parents[1]
        self.cfg = Config()
        self.cfg.set_main_option("script_location", str(root / "alembic"))
        self.engine = create_engine(DB_URL)
        self.tag = uuid.uuid4().hex[:8]

    def tearDown(self):
        self._alembic("upgrade", "head")
        self._q("DELETE FROM media_books WHERE title LIKE :t", t=f"mig-lib-{self.tag}%")
        self._q("DELETE FROM users WHERE username = :u", u=f"mig_team_{self.tag}")
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
        return {r[0] for r in self._q("SELECT table_name FROM information_schema.tables WHERE table_name IN "
                                      "('teacher_profiles', 'student_sessions', 'student_activity_events')")}

    def _active_books(self) -> list:
        return [r[0] for r in self._q("SELECT name FROM media_categories WHERE kind = 'BOOK' AND is_active ORDER BY sort_order")]

    def _cat(self, slug):
        return self._q("SELECT id FROM media_categories WHERE kind = 'BOOK' AND slug = :s", s=slug)[0][0]

    def test_upgrade_downgrade_upgrade(self):
        from sqlalchemy.exc import IntegrityError

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._tables(), set())
        self.assertFalse(self._q("SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'must_change_password'"))
        self.assertIn("Sonstige Bücher", self._active_books())
        ids_before = {slug: self._cat(slug) for slug in ("literatur", "wortschatz", "pruefungsvorbereitung", "sonstige-buecher")}
        lekt, zert, gram = self._cat("lektueren"), self._cat("zertifikatsbuecher"), self._cat("grammatik")
        for title, cat in (("a", lekt), ("b", zert), ("c", gram)):
            self._q("INSERT INTO media_books (id, title, status, access_type, language, category_id, view_count, preview_pages_count, is_special_offer, "
                    "is_featured) VALUES (:id, :t, 'DRAFT', 'FREE', 'de', :c, 0, 10, false, false)", id=uuid.uuid4(), t=f"mig-lib-{self.tag}-{title}", c=cat)

        self._alembic("upgrade", REV)
        self.assertEqual(self._tables(), TABLES)
        self.assertEqual([n for n in self._active_books() if n in SIX], SIX)
        self.assertFalse({"Grammatik", "Zertifikatsbücher", "Lektüren", "Sonstige Bücher"} & set(self._active_books()))
        self.assertEqual({slug: self._cat(slug) for slug in ids_before}, ids_before, "existing category ids are kept")
        moved = dict(self._q("SELECT title, category_id FROM media_books WHERE title LIKE :t", t=f"mig-lib-{self.tag}%"))
        self.assertEqual(moved[f"mig-lib-{self.tag}-a"], ids_before["literatur"])
        self.assertEqual(moved[f"mig-lib-{self.tag}-b"], ids_before["pruefungsvorbereitung"])
        self.assertEqual(moved[f"mig-lib-{self.tag}-c"], ids_before["sonstige-buecher"])
        self.assertEqual(len(self._q("SELECT 1 FROM media_categories WHERE kind = 'BOOK' AND slug IN ('lektueren', 'zertifikatsbuecher', 'grammatik')")), 3,
                         "old categories are kept (inactive)")

        uid = uuid.uuid4()
        self._q("INSERT INTO users (id, email, username, password_hash, is_active, is_verified, is_superuser, role, is_banned, preferred_language) "
                "VALUES (:id, :e, :u, 'x', true, true, false, 'STUDENT', false, 'uz')", id=uid, e=f"mig-team-{self.tag}@test.local", u=f"mig_team_{self.tag}")
        self.assertEqual(self._q("SELECT must_change_password FROM users WHERE id = :id", id=uid), [(False,)])
        session = "INSERT INTO student_sessions (id, user_id, day, started_at, last_seen_at) VALUES (:id, :u, current_date, now(), now())"
        self._q(session, id=uuid.uuid4(), u=uid)
        with self.assertRaises(IntegrityError):  # a second open session for the same user
            self._q(session, id=uuid.uuid4(), u=uid)
        with self.assertRaises(IntegrityError):
            self._q("INSERT INTO student_activity_events (id, user_id, day, area, started_at, last_seen_at) VALUES (:id, :u, current_date, 'SPAM', now(), now())",
                    id=uuid.uuid4(), u=uid)
        self._q("INSERT INTO teacher_profiles (id, user_id) VALUES (:id, :u)", id=uuid.uuid4(), u=uid)
        self.assertEqual(self._q("SELECT can_access_student_control FROM teacher_profiles WHERE user_id = :u", u=uid), [(False,)])

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._tables(), set())
        self.assertIn("Sonstige Bücher", self._active_books())
        self.assertIn("Lektüren", self._active_books())
        self.assertEqual(self._q("SELECT is_active FROM media_categories WHERE kind = 'BOOK' AND slug IN ('historisch', 'beruflich')"),
                         [(False,), (False,)], "the downgrade deletes no category, it only hides the two new ones")
        self.assertEqual(len(self._q("SELECT 1 FROM media_books WHERE title LIKE :t", t=f"mig-lib-{self.tag}%")), 3, "no book is deleted")
        self._alembic("upgrade", REV)
        self.assertEqual(self._tables(), TABLES)


if __name__ == "__main__":
    unittest.main()
