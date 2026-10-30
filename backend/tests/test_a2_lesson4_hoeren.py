"""A2 4. Unterricht Hören: Text 1 / Text 2 / Text 3 instead of the old
"Familie Mannsberg" task (app/services/a2_audio/lesson4_hoeren.py).

Runs against PostgreSQL (VIZU_WB_TEST_DB_URL, a migrated throwaway
database). Storage is a temporary folder; the A2 lessons' Hören tasks and the
A2 library are emptied per test (test database only)."""

import asyncio
import importlib.util
import json
import os
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")


def mp3(seed: str = "") -> bytes:
    return b"ID3\x04\x00\x00\x00\x00\x00\x00" + (seed or uuid.uuid4().hex).encode() * 64


def m4a(seed: str = "") -> bytes:
    return b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00" + (seed or uuid.uuid4().hex).encode() * 64


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestA2Lesson4Hoeren(unittest.TestCase):
    PREFIX = "test-a2l4-"

    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker

        from app.models.language import Language
        from app.models.user import User
        from app.services.lms import structure

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        db = cls.Session()
        if db.scalar(select(Language).where(Language.code == "de")) is None:
            db.add(Language(code="de", locale="de-DE", name="Deutsch"))
            db.commit()
        for level in ("A1", "A2"):
            structure.ensure_structure(db, level)
        tag = uuid.uuid4().hex[:6]
        users = {}
        for name, role in (("super", "SUPER_ADMIN"), ("editor", "CONTENT_MANAGER"), ("student", "STUDENT")):
            users[name] = User(email=f"a2l4-{name}-{tag}@test.local", username=f"a2l4_{name}_{tag}", password_hash="x", is_active=True,
                               is_verified=True, is_superuser=False, role=role, is_banned=False, preferred_language="uz", first_name=name)
            db.add(users[name])
        db.commit()
        cls.ids = {k: v.id for k, v in users.items()}
        db.close()

    def setUp(self):
        from sqlalchemy import select, text

        from app.models.listening import Listening
        from app.models.user import User
        from app.services.a2_audio import assets
        from app.services.lesson_skills.admin import listening_storage

        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "lesson-listening"
        self.root.mkdir()
        self.backups = Path(self.tmp.name) / "backups"
        self._patch = patch.object(listening_storage, "ROOT", self.root)
        self._patch.start()
        self.db = self.Session()
        self.db.execute(text("TRUNCATE a2_audio_assets"))
        a2_ids = [lesson.id for lesson in assets.a2_lessons(self.db)]
        mine = list(self.db.scalars(select(Listening).where(Listening.lesson_id.in_(a2_ids) | Listening.content_id.like(f"{self.PREFIX}%"))))
        if mine:
            self.db.execute(text("DELETE FROM listening_audio_archives WHERE listening_id = ANY(:ids)"), {"ids": [m.id for m in mine]})
            for m in mine:
                self.db.delete(m)
        self.db.commit()
        self.user = {k: self.db.get(User, v) for k, v in self.ids.items()}
        self.lessons = {lesson.number: lesson for lesson in assets.a2_lessons(self.db)}

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        self._patch.stop()
        self.tmp.cleanup()

    # ---------- helpers ----------

    def _file(self, data: bytes) -> str:
        name = f"{uuid.uuid4().hex}.mp3"
        (self.root / name).write_bytes(data)
        return name

    def _task(self, lesson, title, content_id=None, audio=None, published=False, questions=0):
        from app.models.lesson_skill import ListeningOption, ListeningQuestion
        from app.models.listening import Listening

        t = Listening(lesson_id=lesson.id, title=title, content_id=content_id or f"{self.PREFIX}{uuid.uuid4().hex[:8]}",
                      is_published=published, order_index=5)
        if audio:
            t.audio_storage_path, t.audio_content_type, t.audio_size_bytes, t.audio_original_name = audio, "audio/mpeg", 10, "alt.mp3"
        self.db.add(t)
        self.db.flush()
        for n in range(questions):
            q = ListeningQuestion(listening_id=t.id, question=f"Wer ist {n}?", order_index=n + 1)
            q.options = [ListeningOption(option_text=name, is_correct=i == 0, order_index=i + 1)
                         for i, name in enumerate(("Johan Mannsberg", "Anna Mannsberg", "Julio Mannsberg"))]
            self.db.add(q)
        self.db.commit()
        return t

    def _a1_lesson(self, number):
        from sqlalchemy import select

        from app.models.course import Course
        from app.models.lesson import Lesson
        from app.models.module import Module

        return self.db.scalar(select(Lesson).join(Module, Module.id == Lesson.module_id).join(Course, Course.id == Module.course_id)
                              .where(Course.level == "A1", Lesson.number == number))

    def _files(self):
        return sorted(str(p.relative_to(self.root)).replace("\\", "/") for p in self.root.rglob("*") if p.is_file())

    def _up(self, slot, name, data, mime="audio/mpeg", duration=42):
        from app.services.a2_audio import lesson4_hoeren

        upload = UploadFile(file=BytesIO(data), filename=name, headers=Headers({"content-type": mime}))
        return asyncio.run(lesson4_hoeren.upload(self.db, self.user["editor"], slot, upload, duration))

    def _up_status(self, *args, **kwargs):
        with self.assertRaises(HTTPException) as ctx:
            self._up(*args, **kwargs)
        return ctx.exception.status_code, ctx.exception.detail

    def _setup_slots(self):
        from app.services.a2_audio import lesson4_hoeren

        lesson4_hoeren.ensure_slots(self.db, self.user["editor"])
        return {s["slot"]: s for s in lesson4_hoeren.overview(self.db)["slots"]}

    # ---------- the old task ----------

    def test_legacy_removal_backs_up_deletes_or_archives_and_keeps_shared_files(self):
        from sqlalchemy import select

        from app.models.audit_log import AuditLog
        from app.models.lesson_skill import LessonSkillAttempt, ListeningQuestion
        from app.models.listening import Listening
        from app.models.listening_audio_track import ListeningAudioTrack
        from app.services.a2_audio import lesson4_hoeren

        l4 = self.lessons[4]
        own, shared, archived_file, a1_file = (self._file(mp3()) for _ in range(4))
        current = self._task(l4, "Hören: Familie Mannsberg", content_id="vizu-a2buch-l04-hoeren-01", audio=own, questions=3)
        self.db.add(ListeningAudioTrack(listening_id=current.id, label="Text 2", storage_path=shared, order_index=1))
        first_edition = self._task(l4, "[Archiv] Hören: Familie Mannsberg", content_id="vizu-a2-l04-hoeren-01", audio=archived_file, questions=2)
        archived = self._task(l4, "Hören: Familie Mannsberg (Kopie)", published=True, questions=2)  # has learner history
        already = self._task(l4, "[Archiv] Familie Mannsberg alt", questions=1)  # archived + history: nothing to do
        for t in (archived, already):
            self.db.add(LessonSkillAttempt(user_id=self.ids["student"], lesson_id=l4.id, skill="HOEREN", listening_id=t.id,
                                           attempt_number=1, status="SUBMITTED", score=50, started_at=datetime.now(timezone.utc)))
        lesen4 = self._task(l4, "Hören: Wochenende", questions=1)  # another task of lesson 4: untouched
        other_lesson = self._task(self.lessons[5], "Hören: Familie Mannsberg (L5)", audio=shared)  # same title elsewhere: untouched
        a1 = self._task(self._a1_lesson(4), "Hören: Familie Mannsberg", audio=a1_file, questions=1)  # other level: untouched
        self.db.commit()
        current_id, current_questions = current.id, [q.id for q in current.questions]

        plan = lesson4_hoeren.plan(self.db)
        self.assertEqual({str(t["listening_id"]): t["action"] for t in plan["tasks"]},
                         {str(current.id): "delete", str(first_edition.id): "delete", str(archived.id): "archive"})
        first_edition_id = first_edition.id
        self.assertEqual(plan["slots_missing"], [1, 2, 3])
        with self.assertRaises(RuntimeError):
            asyncio.run(lesson4_hoeren.remove_legacy(self.db, self.backups, "wrong", self.user["super"]))
        self.assertIsNotNone(self.db.get(Listening, current_id))  # a wrong plan id changes nothing
        self.assertEqual(len(self._files()), 4)

        report = asyncio.run(lesson4_hoeren.remove_legacy(self.db, self.backups, plan["plan_id"], self.user["super"]))
        self.db.expire_all()
        # backup: rows, questions, options with the key, files (SHA-256 checked)
        folder = Path(report["backup"])
        saved = json.loads((folder / "tasks.json").read_text(encoding="utf-8"))
        first = next(t for t in saved if t["listening"]["id"] == str(current_id))
        self.assertEqual(len(first["questions"]), 3)
        self.assertTrue(any(o["is_correct"] for o in first["questions"][0]["options"]))
        self.assertEqual(len(first["audio_tracks"]), 1)
        files = json.loads((folder / "files.json").read_text(encoding="utf-8"))
        self.assertEqual(set(files), {own, shared, archived_file})
        self.assertEqual(len(saved), 3)
        for rel in files:
            self.assertTrue((folder / "files" / rel).is_file())
        # the task without history is gone (with its questions), its own file too
        self.assertIsNone(self.db.get(Listening, current_id))
        self.assertEqual(self.db.scalars(select(ListeningQuestion).where(ListeningQuestion.id.in_(current_questions))).all(), [])
        self.assertIsNone(self.db.get(Listening, first_edition_id))
        self.assertEqual(report["files_removed"], sorted([own, archived_file]))
        # files still used elsewhere stay
        self.assertEqual(self._files(), sorted([shared, a1_file]))
        # the task with learner history is archived, never deleted
        archived = self.db.get(Listening, archived.id)
        self.assertEqual(archived.title, "[Archiv] Hören: Familie Mannsberg (Kopie)")
        self.assertEqual(self.db.get(Listening, already.id).title, "[Archiv] Familie Mannsberg alt")
        self.assertFalse(archived.is_published)
        self.assertEqual(len(archived.questions), 2)
        self.assertEqual(self.db.scalar(select(LessonSkillAttempt).where(LessonSkillAttempt.listening_id == archived.id)).score, 50)
        # other lesson, other level, other lesson-4 task unchanged
        for t, title in ((lesen4, "Hören: Wochenende"), (other_lesson, "Hören: Familie Mannsberg (L5)"), (a1, "Hören: Familie Mannsberg")):
            row = self.db.get(Listening, t.id)
            self.assertEqual(row.title, title)
        self.assertEqual(self.db.get(Listening, other_lesson.id).audio_storage_path, shared)
        # Text 1-3 created as drafts, audit log written
        slots = {s["slot"]: s for s in lesson4_hoeren.overview(self.db)["slots"]}
        self.assertEqual([slots[n]["title"] for n in (1, 2, 3)], ["Hören: Text 1", "Hören: Text 2", "Hören: Text 3"])
        self.assertTrue(all(not s["is_published"] and s["question_count"] == 0 for s in slots.values()))
        actions = set(self.db.scalars(select(AuditLog.action).where(AuditLog.details.contains(folder.name))))
        self.assertEqual(actions, {"a2_l04_legacy_task_deleted", "a2_l04_legacy_task_archived", "a2_l04_legacy_audio_deleted"})
        # re-running: nothing left to do
        again = lesson4_hoeren.plan(self.db)
        self.assertEqual((again["tasks"], again["slots_missing"]), ([], []))
        self.assertEqual(lesson4_hoeren.overview(self.db)["legacy_tasks"], [])

    # ---------- Text 1-3 ----------

    def test_each_text_uploads_and_is_replaced_independently(self):
        from sqlalchemy import select

        from app.models.a2_audio_asset import A2AudioAsset
        from app.models.listening import Listening

        self._setup_slots()
        t1 = self._up(1, "A2 4.Unterricht Text 1.mp3", mp3())
        t2 = self._up(2, "A2 4.Unterricht Text 2.m4a", m4a(), mime="audio/x-m4a")
        t3 = self._up(3, "A2 4.Unterricht Text 3.mp3", mp3(), duration=75)
        for n, s in ((1, t1), (2, t2), (3, t3)):
            with self.subTest(slot=n):
                self.assertEqual(s["audio"]["status"], "ok")
                self.assertEqual(s["audio"]["file_name"], f"A2 4.Unterricht Text {n}.{'m4a' if n == 2 else 'mp3'}")
                self.assertEqual(s["asset"]["verification"], "pending")
                self.assertFalse(s["is_published"])
                self.assertFalse(s["can_activate"])
                asset = self.db.get(A2AudioAsset, s["asset"]["id"])
                self.assertEqual((asset.unterricht, asset.audio_kind, asset.part), (4, "TEXT", n))
        self.assertEqual((t2["audio"]["format"], t3["audio"]["duration_seconds"]), ("M4A", 75))
        before2 = self.db.get(Listening, t2["listening_id"]).audio_storage_path
        before3 = self.db.get(Listening, t3["listening_id"]).audio_storage_path
        new1 = self._up(1, "Text 1 neu.mp3", mp3())
        self.assertNotEqual(new1["asset"]["id"], t1["asset"]["id"])
        self.db.expire_all()
        self.assertEqual(self.db.get(Listening, t2["listening_id"]).audio_storage_path, before2)
        self.assertEqual(self.db.get(Listening, t3["listening_id"]).audio_storage_path, before3)
        old = self.db.get(A2AudioAsset, t1["asset"]["id"])
        self.assertIsNone(old.listening_id)  # the replaced file stays in the library, unlinked
        self.assertEqual(self.db.scalar(select(A2AudioAsset.listening_id).where(A2AudioAsset.id == new1["asset"]["id"])), new1["listening_id"])

    def test_format_validation_and_duplicates(self):
        slots = self._setup_slots()
        for (name, data, mime), prefix in (
            (("Text 1.wav", b"RIFF\x24\x00\x00\x00WAVEfmt " * 8, "audio/wav"), "UNSUPPORTED_AUDIO"),
            (("Text 1.mp3", m4a(), "audio/mpeg"), "EXTENSION_MISMATCH"),
            (("Text 1.mp3", b"MZ\x90\x00" + b"\x00" * 200, "audio/mpeg"), "NOT_AUDIO"),
            (("Text 1.mp3", mp3(), "text/plain"), "UNSUPPORTED_MIME"),
        ):
            with self.subTest(prefix=prefix):
                code, detail = self._up_status(1, name, data, mime)
                self.assertEqual(code, 400)
                self.assertTrue(str(detail).startswith(prefix), detail)
        self.assertEqual(self._files(), [])
        same = mp3("same")
        self._up(1, "Text 1.mp3", same)
        code, detail = self._up_status(2, "Kopie.mp3", same)
        self.assertEqual((code, detail["code"], detail["used_by"]), (409, "DUPLICATE", slots[1]["title"]))
        self.assertEqual(self._up_status(1, "nochmal.mp3", same)[1]["code"], "SAME_FILE")
        # a file in the library that nothing plays any more is reused, not stored twice
        self._up(1, "Text 1 neu.mp3", mp3())
        reused = self._up(3, "wieder.mp3", same)
        self.assertTrue(reused["reused"])
        self.assertEqual(len(self._files()), 2)

    def test_verify_activate_and_delete(self):
        from app.models.a2_audio_asset import A2AudioAsset
        from app.services.a2_audio import lesson4_hoeren as l4

        self._setup_slots()
        editor = self.user["editor"]
        with self.assertRaises(HTTPException) as ctx:
            l4.set_active(self.db, editor, 1, True)
        self.assertEqual(ctx.exception.status_code, 409)  # no audio
        s = self._up(1, "Text 1.mp3", mp3())
        with self.assertRaises(HTTPException):
            l4.set_active(self.db, editor, 1, True)  # not verified yet
        self.assertTrue(l4.verify(self.db, editor, 1, "verified", None)["can_activate"])
        self.assertTrue(l4.set_active(self.db, editor, 1, True)["is_published"])
        self.assertFalse(l4.verify(self.db, editor, 1, "problem", "rauscht")["is_published"])  # faulty file: hidden again
        l4.verify(self.db, editor, 1, "verified", None)
        l4.set_active(self.db, editor, 1, True)
        self.assertFalse(l4.set_active(self.db, editor, 1, False)["is_published"])
        self._up(2, "Text 2.mp3", mp3())
        gone = asyncio.run(l4.remove_audio(self.db, editor, 1))
        self.assertTrue(gone["file_deleted"])
        self.assertEqual((gone["audio"]["status"], gone["is_published"], gone["asset"]), ("none", False, None))
        self.assertIsNone(self.db.get(A2AudioAsset, s["asset"]["id"]))
        self.assertEqual(len(self._files()), 1)  # Text 2 keeps its file
        self.assertEqual({x["slot"]: x["audio"]["status"] for x in l4.overview(self.db)["slots"]}, {1: "none", 2: "ok", 3: "none"})
        for bad in (0, 4):
            with self.assertRaises(HTTPException) as ctx:
                l4.verify(self.db, editor, bad, "verified", None)
            self.assertEqual(ctx.exception.status_code, 404)

    # ---------- HTTP: students and permissions ----------

    def _client(self, who):
        from fastapi.testclient import TestClient

        from app.api.dependencies.auth import get_current_user
        from app.db.session import get_db
        from app.main import app

        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides.pop(get_current_user, None)
        if who:
            app.dependency_overrides[get_current_user] = lambda: self.user[who]
        self.addCleanup(app.dependency_overrides.clear)
        return TestClient(app)

    @unittest.skipUnless(importlib.util.find_spec("httpx"), "HTTP part needs httpx (FastAPI TestClient); not in requirements.txt")
    def test_students_see_only_active_texts_and_audio_needs_access(self):
        from app.services.a2_audio import lesson4_hoeren as l4

        l4_lesson = self.lessons[4]
        l4_lesson.is_published = True
        self._task(l4_lesson, "[Archiv] Hören: Familie Mannsberg", audio=self._file(mp3()))  # archived: never shown
        self._setup_slots()
        data = mp3()
        s1 = self._up(1, "Text 1.mp3", data)
        self._up(2, "Text 2.mp3", mp3())  # uploaded, not active
        l4.verify(self.db, self.user["editor"], 1, "verified", None)
        l4.set_active(self.db, self.user["editor"], 1, True)
        base = f"/api/v1/lesson-skills/{l4_lesson.id}/hoeren"
        body = self._client("super").get(base).json()
        self.assertEqual([t["title"] for t in body["tasks"]], ["Hören: Text 1"])
        self.assertEqual(body["audio_pending"], 0)
        audio = f"{base}/{s1['listening_id']}/audio"
        r = self._client("super").get(audio)
        self.assertEqual((r.status_code, r.content, r.headers["cache-control"]), (200, data, "private, no-store"))
        self.assertEqual(self._client("student").get(audio).status_code, 403)  # paid lesson, no access
        self.assertEqual(self._client(None).get(audio).status_code, 401)
        admin = "/api/v1/admin/media-management/a2/lesson-4/hoeren"
        student = self._client("student")
        self.assertEqual(student.get(admin).status_code, 403)
        self.assertEqual(student.get(f"{admin}/1/audio").status_code, 403)
        self.assertEqual(student.post(f"{admin}/1/active", json={"active": False}).status_code, 403)
        self.assertEqual(student.post(f"{admin}/1/audio", files={"file": ("x.mp3", mp3(), "audio/mpeg")}).status_code, 403)
        editor = self._client("editor")
        overview = editor.get(admin).json()
        self.assertTrue(overview["set_up"])
        self.assertNotIn("storage_path", json.dumps(overview))
        self.assertEqual(editor.get(f"{admin}/1/audio").content, data)
        up = editor.post(f"{admin}/3/audio", files={"file": ("A2 4.Unterricht Text 3.mp3", mp3(), "audio/mpeg")}, data={"duration_seconds": "61"})
        self.assertEqual((up.status_code, up.json()["audio"]["duration_seconds"]), (200, 61))


if __name__ == "__main__":
    unittest.main()
