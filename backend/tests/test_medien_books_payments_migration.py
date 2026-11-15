"""Migration c2f7a9d1e4b6 (book preview + reading position, book payments, song audio metadata): upgrade -> downgrade -> upgrade on a throwaway
database (VIZU_MIGRATION_TEST_DB_URL, a database of its own at head). New columns / table appear and disappear; rows that existed before the
migration keep their values and get the documented defaults (preview 10, metadata status OK)."""

import os
import unittest
import uuid

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "c2f7a9d1e4b6", "b6e2d9f4a1c8"
COLUMNS = {("media_books", "preview_pages_count"), ("media_books", "page_count"), ("media_progress", "scroll_position"), ("media_progress", "last_opened_at"),
           ("songs", "audio_format"), ("songs", "bitrate_kbps"), ("songs", "metadata_status"), ("songs", "metadata_note"), ("media_purchases", "payment_request_id")}


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestBooksPaymentsMigration(unittest.TestCase):
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
        return {(r[0], r[1]) for r in self._q("SELECT table_name, column_name FROM information_schema.columns WHERE table_name IN ('media_books','media_progress','songs','media_purchases')")} & COLUMNS

    def _table(self):
        return bool(self._q("SELECT 1 FROM information_schema.tables WHERE table_name = 'book_payment_requests'"))

    def test_upgrade_downgrade_upgrade_keeps_existing_rows(self):
        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual((self._columns(), self._table()), (set(), False))
        book, song, user = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        # rows of the previous schema
        self._q("INSERT INTO users (id, email, username, password_hash, is_active, is_verified, is_superuser, role, is_banned, preferred_language) "
                "VALUES (:u, :e, :n, 'x', true, true, false, 'STUDENT', false, 'uz')", u=user, e=f"mig-{user.hex[:8]}@test.local", n=f"mig_{user.hex[:8]}")
        self._q("INSERT INTO media_books (id, title, language, access_type, price, status) VALUES (:b, 'Altes Buch', 'de', 'PAID', 25000, 'PUBLISHED')", b=book)
        self._q("INSERT INTO songs (id, title, language, access_type, status, duration_ms) VALUES (:s, 'Altes Lied', 'de', 'FREE', 'PUBLISHED', 4000)", s=song)
        self._q("INSERT INTO media_progress (id, user_id, content_type, content_id, position, total, completed) VALUES (gen_random_uuid(), :u, 'BOOK', :b, 5, 20, false)", u=user, b=book)
        self._q("INSERT INTO media_purchases (id, user_id, content_type, content_id, price, status) VALUES (gen_random_uuid(), :u, 'BOOK', :b, 25000, 'GRANTED')", u=user, b=book)
        try:
            self._alembic("upgrade", REV)
            self.assertEqual((self._columns(), self._table()), (COLUMNS, True))
            self.assertEqual(self._q("SELECT preview_pages_count, page_count, price FROM media_books WHERE id = :b", b=book), [(10, None, 25000)])
            self.assertEqual(self._q("SELECT metadata_status, audio_format, bitrate_kbps, duration_ms FROM songs WHERE id = :s", s=song), [("OK", None, None, 4000)])
            self.assertEqual(self._q("SELECT position, total, scroll_position, last_opened_at FROM media_progress WHERE user_id = :u", u=user), [(5, 20, None, None)])
            self.assertEqual(self._q("SELECT status, payment_request_id FROM media_purchases WHERE user_id = :u", u=user), [("GRANTED", None)])
            # the new table: one PENDING request per student and book, amount must be positive, status is a fixed set
            ok = "INSERT INTO book_payment_requests (id, user_id, book_id, amount, payment_status) VALUES (gen_random_uuid(), :u, :b, 25000, :s)"
            self._q(ok, u=user, b=book, s="PENDING")
            from sqlalchemy.exc import IntegrityError

            for params in (dict(u=user, b=book, s="PENDING"), dict(u=user, b=book, s="BOGUS")):
                with self.assertRaises(IntegrityError):
                    self._q(ok, **params)
            with self.assertRaises(IntegrityError):
                self._q("INSERT INTO book_payment_requests (id, user_id, book_id, amount, payment_status) VALUES (gen_random_uuid(), :u, :b, 0, 'REJECTED')", u=user, b=book)
            self._q(ok, u=user, b=book, s="REJECTED")  # history rows are not limited
            # deleting the book keeps the request (book_id becomes NULL)
            self._q("DELETE FROM media_purchases WHERE user_id = :u", u=user)
            self._q("DELETE FROM media_books WHERE id = :b", b=book)
            self.assertEqual(self._q("SELECT count(*), count(book_id) FROM book_payment_requests WHERE user_id = :u", u=user), [(2, 0)])
            # downgrade drops exactly the new things and keeps the old rows
            self._alembic("downgrade", PREVIOUS_REV)
            self.assertEqual((self._columns(), self._table()), (set(), False))
            self.assertEqual(self._q("SELECT title, duration_ms FROM songs WHERE id = :s", s=song), [("Altes Lied", 4000)])
            self.assertEqual(self._q("SELECT position FROM media_progress WHERE user_id = :u", u=user), [(5,)])
            self._alembic("upgrade", REV)
            self.assertEqual((self._columns(), self._table()), (COLUMNS, True))
        finally:
            self._alembic("upgrade", "head")
            self._q("DELETE FROM media_progress WHERE user_id = :u", u=user)
            self._q("DELETE FROM book_payment_requests WHERE user_id = :u", u=user)
            self._q("DELETE FROM media_purchases WHERE user_id = :u", u=user)
            self._q("DELETE FROM songs WHERE id = :s", s=song)
            self._q("DELETE FROM media_books WHERE id = :b", b=book)
            self._q("DELETE FROM users WHERE id = :u", u=user)


if __name__ == "__main__":
    unittest.main()
