"""Migration f3a8c1d5e7b2 (Global Chat replies): upgrade -> downgrade ->
upgrade on a throwaway database with existing messages. Runs only with
VIZU_MIGRATION_TEST_DB_URL (a database of its own, at head): it changes the
schema, so it must never share the database of the other integration tests."""

import os
import unittest
import uuid

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REPLY_REV, PREVIOUS_REV = "f3a8c1d5e7b2", "e9b4c2f7a3d1"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestGlobalChatReplyMigration(unittest.TestCase):
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
        return {r[0] for r in self._q("SELECT column_name FROM information_schema.columns WHERE table_name = 'global_chat_messages'")}

    def test_upgrade_downgrade_upgrade_keeps_messages(self):
        self._alembic("upgrade", "head")
        self.assertIn("reply_to_id", self._columns())
        user = uuid.uuid4()
        self._q("INSERT INTO users (id, email, username, password_hash, is_active, is_verified, is_superuser, role, is_banned, "
                "preferred_language, created_at, updated_at) VALUES (:id, :e, :u, 'x', true, true, false, 'STUDENT', false, 'uz', now(), now())",
                id=user, e=f"mig-{user.hex[:8]}@test.local", u=f"mig_{user.hex[:8]}")
        old, reply = uuid.uuid4(), uuid.uuid4()
        self._q("INSERT INTO global_chat_messages (id, sender_id, body, status, created_at, updated_at) VALUES (:id, :s, 'alt', 'visible', now(), now())",
                id=old, s=user)
        self._q("INSERT INTO global_chat_messages (id, sender_id, body, status, reply_to_id, created_at, updated_at) "
                "VALUES (:id, :s, 'antwort', 'visible', :r, now(), now())", id=reply, s=user, r=old)
        # existing rows: NULL, a reply points at its original
        self.assertEqual(self._q("SELECT reply_to_id FROM global_chat_messages WHERE id = :id", id=old)[0][0], None)

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertNotIn("reply_to_id", self._columns())
        self.assertEqual({r[0] for r in self._q("SELECT body FROM global_chat_messages WHERE id IN (:a, :b)", a=old, b=reply)},
                         {"alt", "antwort"})  # both messages survive as plain messages

        self._alembic("upgrade", REPLY_REV)
        self.assertIn("reply_to_id", self._columns())
        self.assertEqual(self._q("SELECT reply_to_id FROM global_chat_messages WHERE id = :id", id=reply)[0][0], None)
        index = self._q("SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_global_chat_messages_reply_to'")
        self.assertIn("WHERE (reply_to_id IS NOT NULL)", index[0][0])
        # the FK only accepts Global Chat ids
        from sqlalchemy.exc import IntegrityError

        with self.assertRaises(IntegrityError):
            self._q("UPDATE global_chat_messages SET reply_to_id = :r WHERE id = :id", r=uuid.uuid4(), id=reply)
        self._q("DELETE FROM global_chat_messages WHERE id IN (:a, :b)", a=reply, b=old)
        self._q("DELETE FROM users WHERE id = :id", id=user)


if __name__ == "__main__":
    unittest.main()
