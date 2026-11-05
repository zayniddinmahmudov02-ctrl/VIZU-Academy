"""Migration f2b6d8a4c1e9 (app_releases): upgrade -> downgrade -> upgrade on a throwaway database. Runs only with
VIZU_MIGRATION_TEST_DB_URL (a database of its own, at head): it changes the schema, so it must never share the
database of the other integration tests."""

import os
import unittest

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "f2b6d8a4c1e9", "e5a9c3f1b7d2"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestAppReleasesMigration(unittest.TestCase):
    def setUp(self):
        from pathlib import Path

        from alembic.config import Config
        from sqlalchemy import create_engine

        root = Path(__file__).resolve().parents[1]
        self.cfg = Config()  # no ini file: env.py's fileConfig() would silence the app's loggers
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

    def _exists(self) -> bool:
        return bool(self._q("SELECT 1 FROM information_schema.tables WHERE table_name = 'app_releases'"))

    def _insert(self, code: int, latest: bool):
        self._q("INSERT INTO app_releases (id, version_name, version_code, storage_name, original_name, size_bytes, sha256, is_latest) "
                "VALUES (gen_random_uuid(), :n, :c, :s, 'a.apk', 1, repeat('0', 64), :l)", n=f"1.{code}", c=code, s=f"{code}.apk", l=latest)

    def test_upgrade_downgrade_upgrade(self):
        from sqlalchemy.exc import IntegrityError

        self._alembic("upgrade", "head")
        self.assertTrue(self._exists())
        users = self._q("SELECT count(*) FROM users")[0][0]
        self._insert(1, True)
        with self.assertRaises(IntegrityError):  # only one latest per platform
            self._insert(2, True)
        with self.assertRaises(IntegrityError):  # version code unique per platform
            self._insert(1, False)

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertFalse(self._exists())
        self.assertEqual(self._q("SELECT count(*) FROM users")[0][0], users)

        self._alembic("upgrade", REV)
        self.assertTrue(self._exists())
        self.assertEqual(self._q("SELECT count(*) FROM app_releases")[0][0], 0)


if __name__ == "__main__":
    unittest.main()
