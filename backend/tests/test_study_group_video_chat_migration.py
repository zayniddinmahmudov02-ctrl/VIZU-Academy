"""The group video chat migration adds rooms without changing existing groups."""

import os
import unittest
import uuid

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "c1v7d3e9a5b2", "a6c2e8f4b9d1"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestStudyGroupVideoChatMigration(unittest.TestCase):
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
        from sqlalchemy import text

        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM study_groups WHERE name = :name"), {"name": f"video migration {self.tag}"})
            conn.execute(text("DELETE FROM users WHERE username = :username"), {"username": f"video_mig_{self.tag}"})
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

    def test_existing_groups_get_a_room_and_survive_downgrade(self):
        from sqlalchemy import select
        from sqlalchemy.orm import Session

        from app.models.study_group import StudyGroup, StudyGroupVideoRoom
        from app.models.user import User

        with Session(self.engine) as db:
            user = User(email=f"video-{self.tag}@test.local", username=f"video_mig_{self.tag}", password_hash="x",
                        is_active=True, is_verified=True, is_superuser=False, role="TEACHER", is_banned=False,
                        preferred_language="uz", first_name="Migration")
            db.add(user)
            db.flush()
            group = StudyGroup(name=f"video migration {self.tag}", teacher_id=user.id, level="A1")
            db.add(group)
            db.commit()
            group_id, user_id = group.id, user.id

        try:
            self._alembic("downgrade", PREVIOUS_REV)
            with Session(self.engine) as db:
                self.assertIsNotNone(db.get(StudyGroup, group_id))
            from sqlalchemy import text

            with self.engine.connect() as conn:
                exists = conn.scalar(text("SELECT 1 FROM information_schema.tables WHERE table_name = 'study_group_video_rooms'"))
            self.assertIsNone(exists)
            self._alembic("upgrade", REV)
            with Session(self.engine) as db:
                room = db.scalar(select(StudyGroupVideoRoom).where(StudyGroupVideoRoom.group_id == group_id))
                self.assertIsNotNone(room)
                self.assertEqual((room.livekit_room_name, room.status, room.max_participants), (f"group-{group_id}", "scheduled", 20))
                self.assertIsNotNone(db.get(StudyGroup, group_id))
        finally:
            self._alembic("upgrade", "head")
            with self.engine.begin() as conn:
                from sqlalchemy import text

                conn.execute(text("DELETE FROM study_groups WHERE id = :id"), {"id": group_id})
                conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})


if __name__ == "__main__":
    unittest.main()
