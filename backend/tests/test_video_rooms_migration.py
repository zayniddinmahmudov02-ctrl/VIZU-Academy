"""Migration b7e4c2a9d6f1 (video_rooms): upgrade -> downgrade -> upgrade on a throwaway database (VIZU_MIGRATION_TEST_DB_URL, at
head): the three tables appear with their keys (one live room per group, one participant row per user and room, checked
statuses) and disappear again; study_groups and users are untouched."""

import os
import unittest
import uuid

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "b7e4c2a9d6f1", "a6c2e8f4b9d1"
TABLES = {"video_rooms", "video_room_participants", "video_room_events"}


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestVideoRoomsMigration(unittest.TestCase):
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
        self._q("DELETE FROM study_groups WHERE name = :n", n=f"mig-video-{self.tag}")
        self._q("DELETE FROM users WHERE username = :u", u=f"mig_video_{self.tag}")
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
        return {r[0] for r in self._q("SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'video_room%'")}

    def _group(self):
        uid, gid = uuid.uuid4(), uuid.uuid4()
        self._q("INSERT INTO users (id, email, username, password_hash, is_active, is_verified, is_superuser, role, is_banned, preferred_language) "
                "VALUES (:id, :e, :u, 'x', true, true, false, 'TEACHER', false, 'uz')", id=uid, e=f"mig-video-{self.tag}@test.local",
                u=f"mig_video_{self.tag}")
        self._q("INSERT INTO study_groups (id, name, teacher_id, level) VALUES (:id, :n, :t, 'A1')", id=gid, n=f"mig-video-{self.tag}", t=uid)
        return uid, gid

    def test_upgrade_downgrade_upgrade(self):
        from sqlalchemy.exc import IntegrityError

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._tables(), set())
        self.assertTrue(self._q("SELECT 1 FROM information_schema.tables WHERE table_name = 'study_groups'"))
        self._alembic("upgrade", REV)
        self.assertEqual(self._tables(), TABLES)

        uid, gid = self._group()
        room = "INSERT INTO video_rooms (id, group_id, room_name, title, status) VALUES (:id, :g, :n, 'Dars', :s)"
        first = uuid.uuid4()
        self._q(room, id=first, g=gid, n=f"vizu-{first.hex}", s="live")
        self.assertEqual(self._q("SELECT max_participants, chat_enabled, students_can_share_screen, students_mic_allowed FROM video_rooms "
                                 "WHERE id = :id", id=first), [(25, True, False, True)])
        with self.assertRaises(IntegrityError):  # a second live room in the same group
            self._q(room, id=uuid.uuid4(), g=gid, n=f"vizu-{uuid.uuid4().hex}", s="live")
        self._q(room, id=uuid.uuid4(), g=gid, n=f"vizu-{uuid.uuid4().hex}", s="scheduled")  # scheduled ones are fine
        with self.assertRaises(IntegrityError):
            self._q(room, id=uuid.uuid4(), g=gid, n=f"vizu-{uuid.uuid4().hex}", s="paused")
        member = "INSERT INTO video_room_participants (id, room_id, user_id) VALUES (:id, :r, :u)"
        self._q(member, id=uuid.uuid4(), r=first, u=uid)
        with self.assertRaises(IntegrityError):  # one row per user and room
            self._q(member, id=uuid.uuid4(), r=first, u=uid)
        self._q("INSERT INTO video_room_events (id, room_id, user_id, event_type, metadata) VALUES (:id, :r, :u, 'created', '{}')",
                id=uuid.uuid4(), r=first, u=uid)
        # deleting the group removes its rooms, participants and events
        self._q("DELETE FROM study_groups WHERE id = :g", g=gid)
        self.assertEqual(self._q("SELECT count(*) FROM video_room_events WHERE room_id = :r", r=first), [(0,)])

        self._alembic("downgrade", PREVIOUS_REV)
        self.assertEqual(self._tables(), set())
        self.assertTrue(self._q("SELECT 1 FROM users WHERE id = :u", u=uid))
        self._alembic("upgrade", REV)
        self.assertEqual(self._tables(), TABLES)


if __name__ == "__main__":
    unittest.main()
