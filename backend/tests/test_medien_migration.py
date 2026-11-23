"""Migration f4c8a1e6b9d2 (VIZU Medienwelt): upgrade -> downgrade -> upgrade on a throwaway database
(VIZU_MIGRATION_TEST_DB_URL, a database of its own at head): eleven tables, the owner's 7 + 8 starting categories, existing
tables untouched."""

import os
import unittest

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "f4c8a1e6b9d2", "e8b4d2f6a1c3"
TABLES = {"media_categories", "media_books", "songs", "playlists", "playlist_songs", "user_favorite_songs", "films", "film_subtitles",
          "media_purchases", "media_progress", "media_play_history"}


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestMedienMigration(unittest.TestCase):
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

    def test_upgrade_downgrade_upgrade(self):
        self._alembic("upgrade", "head")
        self.assertEqual(self._tables(), TABLES)
        counts = dict(self._q("SELECT kind, count(*) FROM media_categories WHERE name LIKE '%' GROUP BY kind"))
        self.assertGreaterEqual(counts["BOOK"], 7)
        self.assertGreaterEqual(counts["FILM"], 8)
        # by slug: at head migration c8d3f5a1e7b2 renames "Sonstige Bücher" -> "Sonstige" and sets three of them inactive (rows and ids stay)
        books = {r[0] for r in self._q("SELECT slug FROM media_categories WHERE kind='BOOK'")}
        self.assertTrue({"literatur", "grammatik", "zertifikatsbuecher", "wortschatz", "lektueren", "pruefungsvorbereitung", "sonstige-buecher"} <= books)
        films = {r[0] for r in self._q("SELECT name FROM media_categories WHERE kind='FILM'")}
        self.assertTrue({"Deutsche Filme", "Kurzfilme", "Dokumentationen", "Lernvideos", "Serien", "Prüfungsvorbereitung", "Kinderfilme", "VIZU Originals"} <= films)
        users, books_old = self._q("SELECT count(*) FROM users")[0][0], self._q("SELECT count(*) FROM books")[0][0]

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._tables(), set())
        self.assertEqual(self._q("SELECT count(*) FROM users")[0][0], users)  # existing tables untouched
        self.assertEqual(self._q("SELECT count(*) FROM books")[0][0], books_old)

        self._alembic("upgrade", REV)
        self.assertEqual(self._tables(), TABLES)
        self.assertEqual(len(self._q("SELECT 1 FROM media_categories WHERE kind='BOOK' AND slug='zertifikatsbuecher'")), 1)


if __name__ == "__main__":
    unittest.main()
