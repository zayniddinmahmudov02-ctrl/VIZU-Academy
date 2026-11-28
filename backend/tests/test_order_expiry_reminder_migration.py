"""Migration a4c9e1f7b2d6 (course access reminder): upgrade -> downgrade -> upgrade on a throwaway database
(VIZU_MIGRATION_TEST_DB_URL, a database of its own at head). `subscription_orders.expiry_reminder_sent_at` exists (nullable,
timestamptz) after the upgrade and is gone after the downgrade while the orders stay."""

import os
import unittest

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "a4c9e1f7b2d6", "f3b8d2a6c9e1"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestOrderExpiryReminderMigration(unittest.TestCase):
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
        rows = self._q("SELECT is_nullable, data_type FROM information_schema.columns "
                       "WHERE table_name = 'subscription_orders' AND column_name = 'expiry_reminder_sent_at'")
        return tuple(rows[0]) if rows else None

    def test_upgrade_downgrade_upgrade(self):
        self._alembic("upgrade", "head")
        self.assertEqual(self._column(), ("YES", "timestamp with time zone"))
        rows = self._q("SELECT count(*) FROM subscription_orders")[0][0]

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertIsNone(self._column())
        self.assertEqual(self._q("SELECT count(*) FROM subscription_orders")[0][0], rows)

        self._alembic("upgrade", REV)
        self.assertEqual(self._column(), ("YES", "timestamp with time zone"))


if __name__ == "__main__":
    unittest.main()
