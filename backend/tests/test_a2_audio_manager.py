"""A2 Audio Manager, A2 access / purchase and the old A2 archive cleanup.

File name parsing and format detection run without a database; upload,
duplicates, linking, removal, manifest, student access, the purchase flow,
sales readiness and the cleanup stages run against PostgreSQL
(VIZU_WB_TEST_DB_URL, a migrated throwaway database). Storage is a temporary
folder: no real file is ever touched. The A2 lessons' Hören tasks and the
A2 library are emptied per test (test database only)."""

import asyncio
import importlib.util
import os
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
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


class TestFilenameParser(unittest.TestCase):
    def test_screenshot_names(self):
        from app.services.a2_audio.filename import parse

        cases = {
            "A2 1.Unterricht Hören.m4a": (1, "HOEREN", None),
            "A2 2.Unterricht Hören.mp3": (2, "HOEREN", None),
            "A2 4.Unterricht Text 1.mp3": (4, "TEXT", 1),
            "A2 4.Unterricht Text 3.mp3": (4, "TEXT", 3),
            "A2 6.Unterricht.mp3": (6, "UNTERRICHT", None),
            "A2 7.Unterricht Text 2.mp3": (7, "TEXT", 2),
            "A2 9.Unterricht Hören.mp3": (9, "HOEREN", None),
            "A2 10.Unterricht Teil 1.m4a": (10, "UNTERRICHT", 1),
            "A2 11.Unterricht Teil_3.m4a": (11, "UNTERRICHT", 3),
            "A2 12.Unterricht Teil_4.m4a": (12, "UNTERRICHT", 4),
            "A2 13.Unterricht Teil 2.m4a": (13, "UNTERRICHT", 2),
            "A2 3.Unterricht Hören.mp3": (3, "HOEREN", None),  # macOS: decomposed umlaut
            "a2_5_unterricht_hoeren.mp3": (5, "HOEREN", None),
            "A2 10.UNTERICHT Hören Teil 2.m4a": (10, "HOEREN", 2),  # the book's spelling
        }
        for name, (n, kind, part) in cases.items():
            with self.subTest(name=name):
                p = parse(name)
                self.assertTrue(p["recognized"])
                self.assertEqual((p["unterricht"], p["audio_kind"], p["part"]), (n, kind, part))
                self.assertIsNone(p["other_level"])

    def test_unknown_and_other_levels(self):
        from app.services.a2_audio.filename import parse

        for name in ("Aufnahme 17.mp3", "IMG_2024.m4a", "", "A2.mp3", "Hören Teil 1.mp3"):
            with self.subTest(name=name):
                p = parse(name)
                self.assertFalse(p["recognized"])
                self.assertEqual((p["unterricht"], p["audio_kind"], p["part"]), (None, None, None))
        self.assertEqual(parse("A1 3.Unterricht Hören.mp3")["other_level"], "A1")
        self.assertEqual(parse("B1 1.Unterricht.mp3")["other_level"], "B1")
        # a printed track number is not a part; unknown words are "other"
        p = parse("A2 12.Unterricht Track 27.mp3")
        self.assertEqual((p["part"], p["audio_kind"]), (None, "OTHER"))
        self.assertEqual(parse("../../A2 1.Unterricht Hören.mp3")["title"], "A2 1.Unterricht Hören")  # no path in the title


class TestFormatDetection(unittest.TestCase):
    def test_content_decides(self):
        from app.services.a2_audio.assets import detect_format

        self.assertEqual(detect_format(b"ID3\x03\x00" + b"\x00" * 11), "mp3")
        self.assertEqual(detect_format(b"\xff\xfb\x90\x64" + b"\x00" * 12), "mp3")  # MPEG-1 Layer III frame
        self.assertEqual(detect_format(b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00"), "m4a")
        self.assertEqual(detect_format(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00"), "m4a")
        for bad in (b"\xff\xf1\x50\x80" + b"\x00" * 12,  # AAC ADTS, not MP3
                    b"\x00\x00\x00\x20ftypM4V \x00\x00\x00\x00",  # video
                    b"RIFF\x24\x00\x00\x00WAVEfmt ", b"%PDF-1.7\n" + b"\x00" * 7, b"MZ" + b"\x00" * 14, b""):
            with self.subTest(head=bad[:12]):
                self.assertIsNone(detect_format(bad))

    def test_formats_come_from_the_configuration(self):
        from app.core.config import settings
        from app.services.a2_audio.assets import allowed_formats

        with patch.object(settings, "A2_AUDIO_FORMATS", "mp3"):
            self.assertEqual(allowed_formats(), ["mp3"])
        with patch.object(settings, "A2_AUDIO_FORMATS", "mp3, M4A, exe"):
            self.assertEqual(allowed_formats(), ["mp3", "m4a"])


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestA2AudioManager(unittest.TestCase):
    PREFIX = "test-a2am-"

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

        def user(role, name):
            u = User(email=f"a2am-{name}-{tag}@test.local", username=f"a2am_{name}_{tag}", password_hash="x", is_active=True,
                     is_verified=True, is_superuser=False, role=role, is_banned=False, preferred_language="uz", first_name=name)
            db.add(u)
            return u

        users = {n: user(r, n) for n, r in (("super", "SUPER_ADMIN"), ("editor", "CONTENT_MANAGER"), ("student", "STUDENT"),
                                             ("buyer", "STUDENT"))}
        db.commit()
        cls.ids = {k: v.id for k, v in users.items()}
        db.close()

    def setUp(self):
        from sqlalchemy import delete, select, text

        from app.models.course import Course
        from app.models.listening import Listening
        from app.models.subscription_order import SubscriptionOrder
        from app.models.user import User
        from app.services.a2_audio import assets
        from app.services.lesson_skills.admin import listening_storage
        from app.services.vizu_pay import offers

        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "lesson-listening"
        self.root.mkdir()
        self.qroot = Path(self.tmp.name) / "quarantine"
        self._patches = [patch.object(listening_storage, "ROOT", self.root), patch.object(offers, "_read_overrides", return_value={})]
        for p in self._patches:
            p.start()
        offers.invalidate_cache()

        self.db = self.Session()
        self.db.execute(text("TRUNCATE a2_audio_assets"))
        a2_ids = [lesson.id for lesson in assets.a2_lessons(self.db)]
        mine = list(self.db.scalars(select(Listening).where((Listening.lesson_id.in_(a2_ids)) | (Listening.content_id.like(f"{self.PREFIX}%")))))
        if mine:
            self.db.execute(text("DELETE FROM listening_audio_archives WHERE listening_id = ANY(:ids)"), {"ids": [m.id for m in mine]})
            for m in mine:
                self.db.delete(m)
        self.db.execute(delete(SubscriptionOrder).where(SubscriptionOrder.user_id.in_([self.ids["student"], self.ids["buyer"]])))
        self.db.execute(text("DELETE FROM app_settings WHERE key = 'a2_sales_readiness'"))
        course = self.db.scalar(select(Course).where(Course.level == "A2").order_by(Course.order_index))
        course.description, course.is_active = None, True
        for lesson in assets.a2_lessons(self.db):
            lesson.is_published = False
        self.db.commit()
        self.user = {k: self.db.get(User, v) for k, v in self.ids.items()}
        self.lessons = {lesson.number: lesson for lesson in assets.a2_lessons(self.db)}

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        for p in self._patches:
            p.stop()
        from app.services.vizu_pay import offers

        offers.invalidate_cache()
        self.tmp.cleanup()

    # ---------- helpers ----------

    def _status(self, fn, *args, **kwargs):
        with self.assertRaises(HTTPException) as ctx:
            fn(*args, **kwargs)
        return ctx.exception.status_code, ctx.exception.detail

    def _upload(self, name, data, mime="audio/mpeg", **fields):
        from app.services.a2_audio import assets

        upload = UploadFile(file=BytesIO(data), filename=name, headers=Headers({"content-type": mime}))
        return asyncio.run(assets.upload(self.db, self.user["editor"], upload, fields))

    def _upload_status(self, *args, **kwargs):
        with self.assertRaises(HTTPException) as ctx:
            self._upload(*args, **kwargs)
        return ctx.exception.status_code, ctx.exception.detail

    def _task(self, number, title, content_id=None, level="A2", published=False, material_key=None, audio: bytes | None = None):
        from sqlalchemy import select

        from app.models.course import Course
        from app.models.lesson import Lesson
        from app.models.listening import Listening
        from app.models.module import Module

        lesson = self.lessons[number] if level == "A2" else self.db.scalar(
            select(Lesson).join(Module, Module.id == Lesson.module_id).join(Course, Course.id == Module.course_id)
            .where(Course.level == level, Lesson.number == number))
        t = Listening(lesson_id=lesson.id, title=title, content_id=content_id or f"{self.PREFIX}{uuid.uuid4().hex[:8]}",
                      is_published=published, a2_material_key=material_key, order_index=1)
        if audio is not None:
            name = f"{uuid.uuid4().hex}.mp3"
            (self.root / name).write_bytes(audio)
            t.audio_storage_path, t.audio_content_type, t.audio_size_bytes, t.audio_original_name = name, "audio/mpeg", len(audio), "alt.mp3"
        self.db.add(t)
        self.db.commit()
        return t

    def _files(self):
        return sorted(str(p.relative_to(self.root)).replace("\\", "/") for p in self.root.rglob("*") if p.is_file())

    # ---------- upload ----------

    def test_upload_parses_name_keeps_original_and_only_suggests(self):
        t1 = self._task(10, "Hören Teil 1", content_id="vizu-a2buch-l10-hoeren-01")
        self._task(10, "Hören Teil 2", content_id="vizu-a2buch-l10-hoeren-02")
        asset = self._upload("A2 10.Unterricht Teil 1.m4a", m4a(), mime="audio/x-m4a", duration_seconds=95)
        self.assertEqual((asset["unterricht"], asset["audio_kind"], asset["part"]), (10, "UNTERRICHT", 1))
        self.assertEqual(asset["original_filename"], "A2 10.Unterricht Teil 1.m4a")
        self.assertEqual((asset["audio_format"], asset["content_type"], asset["duration_seconds"]), ("M4A", "audio/mp4", 95))
        self.assertEqual(len(asset["sha256"]), 64)
        self.assertEqual(asset["verification"], "pending")
        self.assertIsNone(asset["linked"])  # never linked by the upload
        self.assertEqual(asset["suggestion"]["listening_id"], t1.id)
        stored = self._files()
        self.assertEqual(len(stored), 1)
        self.assertTrue(stored[0].startswith("a2-audio/") and stored[0].endswith(".m4a"))
        self.assertNotIn("Unterricht", stored[0])  # safe, unique storage name
        self.db.refresh(t1)
        self.assertIsNone(t1.audio_storage_path)
        # explicit admin values win over the file name; an unknown name has no suggestion
        other = self._upload("Aufnahme.mp3", mp3(), unterricht=3, audio_kind="HOEREN", title="Hörtext Lektion 3")
        self.assertEqual((other["unterricht"], other["audio_kind"], other["title"]), (3, "HOEREN", "Hörtext Lektion 3"))
        self.assertFalse(other["parsed"]["recognized"])
        self.assertIsNone(other["suggestion"])
        # "Text" files are never guessed into an ordinary Hören task — only into the task that is Text N
        plain = self._task(4, "Hören", content_id="vizu-a2buch-l04-hoeren-01")
        self.assertIsNone(self._upload("A2 4.Unterricht Text 1.mp3", mp3())["suggestion"])
        plain.task_key = "a2-u04-hoeren-text-2"
        self.db.commit()
        self.assertEqual(self._upload("A2 4.Unterricht Text 2.mp3", mp3())["suggestion"]["listening_id"], plain.id)
        self.assertIsNone(self._upload("A2 7.Unterricht Text 2.mp3", mp3())["suggestion"])

    def test_duplicate_is_refused_and_leaves_no_file(self):
        data = mp3("same")
        first = self._upload("A2 2.Unterricht Hören.mp3", data)
        code, detail = self._upload_status("Kopie mit anderem Namen.mp3", data)
        self.assertEqual(code, 409)
        self.assertEqual((detail["code"], detail["existing_id"]), ("DUPLICATE", str(first["id"])))
        self.assertEqual(len(self._files()), 1)

    def test_format_mime_size_and_level_checks(self):
        from app.core.config import settings

        cases = [
            (("A2 1.Unterricht Hören.wav", b"RIFF\x24\x00\x00\x00WAVEfmt " * 8, "audio/wav"), 400, "UNSUPPORTED_AUDIO"),
            (("A2 1.Unterricht Hören.mp3", mp3(), "text/plain"), 400, "UNSUPPORTED_MIME"),
            (("A2 1.Unterricht Hören.mp3", m4a(), "audio/mpeg"), 400, "EXTENSION_MISMATCH"),
            (("A2 1.Unterricht Hören.mp3", b"MZ\x90\x00" + b"\x00" * 200, "audio/mpeg"), 400, "NOT_AUDIO"),
            (("A2 1.Unterricht Hören.exe", mp3(), "audio/mpeg"), 400, "UNSUPPORTED_AUDIO"),
            (("A1 1.Unterricht Hören.mp3", mp3(), "audio/mpeg"), 422, "FILENAME_OTHER_LEVEL"),
            (("", mp3(), "audio/mpeg"), 422, "FILENAME_REQUIRED"),
        ]
        for (name, data, mime), code, prefix in cases:
            with self.subTest(prefix=prefix, name=name):
                status, detail = self._upload_status(name, data, mime)
                self.assertEqual(status, code)
                self.assertTrue(str(detail).startswith(prefix), detail)
        with patch.object(settings, "A2_AUDIO_MAX_BYTES", 100):
            self.assertEqual(self._upload_status("A2 1.Unterricht Hören.mp3", mp3())[0], 413)
        with patch.object(settings, "A2_AUDIO_FORMATS", "mp3"):
            self.assertEqual(self._upload_status("A2 1.Unterricht Hören.m4a", m4a(), "audio/mp4")[0], 400)
        self.assertEqual(self._files(), [])  # nothing left behind by a refused upload

    def test_corrections_and_verification(self):
        from app.services.a2_audio import assets

        a = self._upload("A2 15.Unterricht.mp3", mp3())  # there is no 15th lesson: left for the admin
        self.assertIsNone(a["unterricht"])
        fixed = assets.update(self.db, a["id"], {"unterricht": 8, "audio_kind": "hoeren", "title": "  Hören   8 ", "sort_order": 3})
        self.assertEqual((fixed["unterricht"], fixed["audio_kind"], fixed["title"], fixed["sort_order"]), (8, "HOEREN", "Hören 8", 3))
        for bad in ({"unterricht": 15}, {"audio_kind": "VIDEO"}, {"title": "   "}, {"part": 0}):
            with self.subTest(bad=bad):
                self.assertEqual(self._status(assets.update, self.db, a["id"], bad)[0], 422)
        self.assertEqual(self._status(assets.verify, self.db, self.user["editor"], a["id"], "problem", None), (422, "NOTE_REQUIRED: say what is wrong"))
        problem = assets.verify(self.db, self.user["editor"], a["id"], "problem", "bricht nach 10 s ab")
        self.assertEqual((problem["verification"], problem["verification_note"]), ("problem", "bricht nach 10 s ab"))
        ok = assets.verify(self.db, self.user["editor"], a["id"], "verified", None)
        self.assertEqual(ok["verification"], "verified")
        self.assertIsNotNone(ok["verified_at"])
        # a file that disappeared from storage cannot be verified
        for f in self.root.rglob("*.mp3"):
            f.unlink()
        self.assertEqual(self._status(assets.verify, self.db, self.user["editor"], a["id"], "verified", None)[0], 409)

    # ---------- linking ----------

    def test_explicit_link_archives_previous_audio_and_sets_draft(self):
        from sqlalchemy import select

        from app.models.listening_audio_archive import ListeningAudioArchive
        from app.services.a2_audio import assets

        task = self._task(1, "Warum haben Sie Ihren Beruf gewählt", published=True, audio=mp3("old"))
        old_path = task.audio_storage_path
        a = self._upload("A2 1.Unterricht Hören.m4a", m4a(), mime="audio/mp4")
        self.assertEqual(a["suggestion"]["listening_id"], task.id)
        linked = assets.link(self.db, self.user["editor"], a["id"], task.id)
        self.db.refresh(task)
        self.assertEqual(task.audio_storage_path, linked_path := self.db.get(assets.A2AudioAsset, a["id"]).storage_path)
        self.assertEqual((task.audio_original_name, task.audio_content_type), ("A2 1.Unterricht Hören.m4a", "audio/mp4"))
        self.assertFalse(task.is_published)  # checked by the admin before students hear it
        self.assertEqual(linked["linked"]["listening_id"], task.id)
        self.assertTrue(linked["linked"]["in_sync"])
        archived = self.db.scalars(select(ListeningAudioArchive).where(ListeningAudioArchive.listening_id == task.id)).all()
        self.assertEqual([r.storage_path for r in archived], [old_path])
        self.assertTrue((self.root / old_path).is_file())  # nothing deleted
        self.assertTrue((self.root / linked_path).is_file())
        # idempotent
        assets.link(self.db, self.user["editor"], a["id"], task.id)
        self.assertEqual(len(self.db.scalars(select(ListeningAudioArchive).where(ListeningAudioArchive.listening_id == task.id)).all()), 1)

    def test_link_targets_are_only_current_a2_tasks(self):
        from app.services.a2_audio import assets

        a = self._upload("A2 1.Unterricht Hören.mp3", mp3())
        archived = self._task(1, "[Archiv] Hören", content_id="vizu-a2-l01-hoeren-01")
        legacy = self._task(1, "A2 1.Unterricht Hören", material_key=f"a2-l01-audio-{uuid.uuid4().hex[:4]}")
        a1_task = self._task(1, "A1 Hören", level="A1")
        self.assertEqual(self._status(assets.link, self.db, self.user["editor"], a["id"], archived.id)[0], 409)
        self.assertEqual(self._status(assets.link, self.db, self.user["editor"], a["id"], legacy.id)[0], 409)
        self.assertEqual(self._status(assets.link, self.db, self.user["editor"], a["id"], a1_task.id)[0], 422)
        self.assertEqual(self._status(assets.link, self.db, self.user["editor"], a["id"], uuid.uuid4())[0], 404)
        current = self._task(1, "Hören")
        assets.verify(self.db, self.user["editor"], a["id"], "problem", "falsche Datei")
        self.assertEqual(self._status(assets.link, self.db, self.user["editor"], a["id"], current.id)[0], 409)
        self.db.refresh(a1_task)
        self.assertIsNone(a1_task.audio_storage_path)  # other levels untouched

    def test_relink_and_second_file_for_the_same_task(self):
        from app.services.a2_audio import assets

        t1, t2 = self._task(10, "Teil 1", "vizu-a2buch-l10-hoeren-01"), self._task(10, "Teil 2", "vizu-a2buch-l10-hoeren-02")
        a = self._upload("A2 10.Unterricht Teil 1.m4a", m4a(), mime="audio/mp4")
        b = self._upload("A2 10.Unterricht Teil 1 (neu).m4a", m4a(), mime="audio/mp4")
        assets.link(self.db, self.user["editor"], a["id"], t1.id)
        # a was wrong: it belongs to Teil 2 -> moves, t1 is empty again
        moved = assets.link(self.db, self.user["editor"], a["id"], t2.id)
        self.db.refresh(t1)
        self.assertIsNone(t1.audio_storage_path)
        self.assertEqual(moved["linked"]["listening_id"], t2.id)
        # another file for t2 releases a (it stays in the library, unlinked)
        assets.link(self.db, self.user["editor"], b["id"], t2.id)
        self.db.expire_all()
        self.assertIsNone(self.db.get(assets.A2AudioAsset, a["id"]).listening_id)
        self.assertEqual(len(self._files()), 2)

    def test_unlink_and_removal_are_separate_steps(self):
        from app.services.a2_audio import assets

        task = self._task(2, "Hören")
        a = self._upload("A2 2.Unterricht Hören.mp3", mp3())
        path = self.db.get(assets.A2AudioAsset, a["id"]).storage_path
        assets.link(self.db, self.user["editor"], a["id"], task.id)
        self.assertEqual(asyncio.run(self._remove_status(a["id"], False))[0], 409)  # linked: unlink first
        unlinked = assets.unlink(self.db, a["id"])
        self.assertIsNone(unlinked["linked"])
        self.db.refresh(task)
        self.assertIsNone(task.audio_storage_path)
        self.assertTrue((self.root / path).is_file())
        # the entry only: the file stays (shows up as "no database entry" for review)
        self.assertEqual(asyncio.run(assets.remove(self.db, a["id"], False))["file_kept"], True)
        self.assertTrue((self.root / path).is_file())
        # entry + file
        b = self._upload("A2 3.Unterricht Hören.mp3", mp3())
        bpath = self.db.get(assets.A2AudioAsset, b["id"]).storage_path
        self.assertEqual(asyncio.run(assets.remove(self.db, b["id"], True))["file_deleted"], True)
        self.assertFalse((self.root / bpath).exists())
        # a file something else still uses is never deleted
        c = self._upload("A2 5.Unterricht Hören.mp3", mp3())
        cpath = self.db.get(assets.A2AudioAsset, c["id"]).storage_path
        other = self._task(5, "Hören")
        other.audio_storage_path = cpath
        self.db.commit()
        status, detail = asyncio.run(self._remove_status(c["id"], True))
        self.assertEqual(status, 409)
        self.assertTrue(detail.startswith("FILE_IN_USE"))
        self.assertTrue((self.root / cpath).is_file())

    async def _remove_status(self, asset_id, delete_file):
        from app.services.a2_audio import assets

        try:
            await assets.remove(self.db, asset_id, delete_file)
        except HTTPException as exc:
            return exc.status_code, exc.detail
        self.fail("no HTTPException")

    def test_hoeren_endpoints_never_delete_a_library_file(self):
        from app.services.a2_audio import assets
        from app.services.lesson_skills import admin as skill_admin

        task = self._task(6, "Hören")
        a = self._upload("A2 6.Unterricht.mp3", mp3())
        path = self.db.get(assets.A2AudioAsset, a["id"]).storage_path
        assets.link(self.db, self.user["editor"], a["id"], task.id)
        asyncio.run(skill_admin.delete_listening_audio(self.db, task.id))  # the old per-task "Audio löschen"
        self.db.expire_all()
        self.assertTrue((self.root / path).is_file())
        self.assertIsNone(self.db.get(assets.A2AudioAsset, a["id"]).listening_id)  # unlinked, still in the library

    # ---------- manifest, student access ----------

    def test_manifest_counts_the_real_data(self):
        from app.services.a2_audio import assets

        t1 = self._task(1, "Hören")
        self._task(10, "Teil 1", "vizu-a2buch-l10-hoeren-01")
        a = self._upload("A2 1.Unterricht Hören.mp3", mp3())
        self._upload("A2 10.Unterricht Teil 1.m4a", m4a(), mime="audio/mp4")
        self._upload("irgendwas.mp3", mp3())
        assets.link(self.db, self.user["editor"], a["id"], t1.id)
        m = assets.manifest(self.db)
        c = m["counts"]
        self.assertEqual((c["files"], c["linked"], c["unlinked"], c["no_unterricht"]), (3, 1, 2, 1))
        self.assertEqual(c["by_format"], {"MP3": 2, "M4A": 1})
        self.assertEqual((c["tasks"], c["tasks_with_audio"], c["tasks_without_audio"]), (2, 1, 1))
        self.assertEqual([r["title"] for r in m["missing_audio"]], ["Teil 1"])
        self.assertEqual(len(m["lessons"]), len(self.lessons))  # every LMS lesson, not a fixed list
        self.assertEqual([x["original_filename"] for x in m["unassigned"]], ["irgendwas.mp3"])

    def _client(self, who):
        from fastapi.testclient import TestClient

        from app.api.dependencies.auth import get_current_user
        from app.db.session import get_db
        from app.main import app

        app.dependency_overrides[get_db] = lambda: self.db
        if who:
            app.dependency_overrides[get_current_user] = lambda: self.user[who]
        self.addCleanup(app.dependency_overrides.clear)
        return TestClient(app)

    @unittest.skipUnless(importlib.util.find_spec("httpx"), "HTTP part needs httpx (FastAPI TestClient); not in requirements.txt")
    def test_student_reaches_a2_audio_only_through_an_open_lesson(self):
        from app.services.a2_audio import assets

        free, paid = self._task(1, "Hören 1"), self._task(2, "Hören 2")
        a, b = self._upload("A2 1.Unterricht Hören.mp3", data1 := mp3()), self._upload("A2 2.Unterricht Hören.mp3", mp3())
        assets.link(self.db, self.user["editor"], a["id"], free.id)
        assets.link(self.db, self.user["editor"], b["id"], paid.id)
        l1, l2 = self.lessons[1], self.lessons[2]
        url = lambda lesson, task: f"/api/v1/lesson-skills/{lesson.id}/hoeren/{task.id}/audio"  # noqa: E731
        client = self._client("student")
        self.assertEqual(client.get(url(l1, free)).status_code, 404)  # lesson still a draft
        l1.is_published = l2.is_published = True
        self.db.commit()
        self.assertEqual(client.get(url(l1, free)).status_code, 404)  # task still a draft after linking
        free.is_published = paid.is_published = True
        self.db.commit()
        r = client.get(url(l1, free))
        self.assertEqual((r.status_code, r.content), (200, data1))  # lesson 1: the free preview
        self.assertEqual(r.headers["cache-control"], "private, no-store")
        self.assertEqual(client.get(url(l2, paid)).status_code, 403)  # paid lesson, not bought
        # the library and the admin preview are not for students
        self.assertEqual(client.get(f"/api/v1/admin/media-management/a2-audio/assets/{a['id']}/audio").status_code, 403)
        self.assertEqual(client.get("/api/v1/admin/media-management/a2-audio/assets").status_code, 403)
        self.assertEqual(client.post(f"/api/v1/admin/media-management/a2-audio/assets/{a['id']}/link",
                                     json={"listening_id": str(paid.id)}).status_code, 403)
        # no storage path is ever exposed
        admin = self._client("super")
        listing = admin.get("/api/v1/admin/media-management/a2-audio/assets").json()
        self.assertNotIn("storage_path", listing[0])
        self.assertEqual(admin.get(f"/api/v1/admin/media-management/a2-audio/assets/{a['id']}/audio").content, data1)
        from app.api.dependencies.auth import get_current_user
        from app.main import app

        app.dependency_overrides.pop(get_current_user, None)
        self.assertEqual(self._client(None).get(url(l1, free)).status_code, 401)

    @unittest.skipUnless(importlib.util.find_spec("httpx"), "HTTP part needs httpx (FastAPI TestClient); not in requirements.txt")
    def test_student_sees_audio_pending_instead_of_a_broken_player(self):
        from app.services.a2_audio import assets

        lesson = self.lessons[1]
        lesson.is_published = True
        with_audio = self._task(1, "Mit Audio", published=True)
        a = self._upload("A2 1.Unterricht Hören.mp3", mp3())
        assets.link(self.db, self.user["editor"], a["id"], with_audio.id)
        with_audio.is_published = True
        self._task(1, "Ohne Audio", published=True)  # published, audio not uploaded yet
        gone = self._task(1, "Datei verschwunden", published=True, audio=mp3())
        (self.root / gone.audio_storage_path).unlink()  # DB path, no file
        self._task(1, "Entwurf ohne Audio")  # drafts are never counted / revealed
        self.db.commit()
        body = self._client("student").get(f"/api/v1/lesson-skills/{lesson.id}/hoeren").json()
        self.assertEqual([t["title"] for t in body["tasks"]], ["Mit Audio"])
        self.assertEqual(body["audio_pending"], 2)

    # ---------- purchase flow ----------

    def test_a2_purchase_flow_and_access(self):
        from app.services.vizu_pay import offers
        from app.services.vizu_pay.access import can_access_lesson
        from app.services.vizu_pay.admin_service import AdminVizuPayService
        from app.services.vizu_pay.service import VizuPayError, VizuPayService

        buyer = self.user["buyer"]
        lesson2 = self.lessons[2]
        lesson2.is_published = True
        self.db.commit()
        proof_root = Path(self.tmp.name) / "proofs"

        def order():
            svc = VizuPayService(self.db)
            svc.proof_storage.ROOT = proof_root
            proof = UploadFile(file=BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 64), filename="beleg.png", headers=Headers({"content-type": "image/png"}))
            return asyncio.run(svc.create_order(buyer, "A2", "UZCARD", None, proof, "127.0.0.1"))

        def can_open():
            self.db.expire_all()
            self.db.info.clear()
            return can_access_lesson(self.db.get(type(buyer), buyer.id), self.db.get(type(lesson2), lesson2.id))

        # sales not approved for A2 (the code default): no order at all
        with self.assertRaises(HTTPException) as ctx:
            order()
        self.assertEqual((ctx.exception.status_code, ctx.exception.detail), (409, "OFFER_NOT_AVAILABLE"))
        with patch.object(offers, "_read_overrides", return_value={"sales": {"A2": True}}):
            offers.invalidate_cache()
            first = order()
            self.assertEqual((first["status"], first["final_amount"]), ("PENDING", offers.offer("A2")["sale_price"]))  # price from the server
            self.assertFalse(can_open())  # pending: nothing opens
            with self.assertRaises(HTTPException) as ctx:
                order()
            self.assertEqual(ctx.exception.detail, "PAYMENT_REQUEST_ALREADY_PENDING")
            admin = AdminVizuPayService(self.db)
            admin.reject_order(first["id"], "Beleg unleserlich", self.user["super"], None)
            self.assertFalse(can_open())  # rejected: nothing opens
            second = order()
            admin.approve_order(second["id"], self.user["super"], None)
            self.assertTrue(can_open())
            with self.assertRaises(VizuPayError):
                admin.approve_order(second["id"], self.user["super"], None)  # one payment, one access window
            with self.assertRaises(HTTPException) as ctx:
                order()
            self.assertEqual(ctx.exception.detail, "OFFER_ALREADY_OWNED")
            from app.models.subscription_order import SubscriptionOrder

            self.assertEqual(self.db.query(SubscriptionOrder).filter_by(user_id=buyer.id, status="APPROVED").count(), 1)
            admin.refund_order(second["id"], "Test", self.user["super"], None)
            self.assertFalse(can_open())
        # another student never gets the buyer's access
        self.assertFalse(can_access_lesson(self.user["student"], lesson2))

    # ---------- readiness ----------

    def test_readiness_moves_from_configuration_to_ready(self):
        from app.services.a2_audio import assets, readiness

        r = readiness.compute(self.db)
        self.assertEqual(r["status"], "NEEDS_CONFIGURATION")  # lesson 1 (free preview) is not published
        self.assertTrue(next(c for c in r["checks"] if c["key"] == "price")["ok"])  # the price exists in Angebote
        self.assertFalse(r["sales_enabled"])
        self.lessons[1].is_published = True
        self.db.commit()
        r = readiness.compute(self.db)
        self.assertEqual(r["status"], "NEEDS_CONTENT")
        failing = {c["key"] for c in r["checks"] if not c["ok"]}
        self.assertTrue({"description", "manifest", "audio_complete", "audio_verified", "links"} <= failing)
        # real files for every task, linked and listened to
        t1, t2 = self._task(1, "Hören"), self._task(10, "Teil 1", "vizu-a2buch-l10-hoeren-01")
        a, b = self._upload("A2 1.Unterricht Hören.mp3", mp3()), self._upload("A2 10.Unterricht Teil 1.m4a", m4a(), mime="audio/mp4")
        for asset, task in ((a, t1), (b, t2)):
            assets.link(self.db, self.user["editor"], asset["id"], task.id)
        r = readiness.compute(self.db)
        self.assertIn("audio_verified", {c["key"] for c in r["checks"] if not c["ok"]})
        for asset in (a, b):
            assets.verify(self.db, self.user["editor"], asset["id"], "verified", None)
        from app.services.lms import structure

        course = structure.level_course(self.db, "A2")
        course.description = "Goethe A2: 13 Unterrichte mit Hören, Lesen, Schreiben, Sprechen."
        self.db.commit()
        r = readiness.compute(self.db)
        self.assertEqual({c["key"] for c in r["checks"] if not c["ok"] and c["group"] == "content"}, {"hoeren_published"})
        # transcribed, matched and published (app/scripts/a2_audio_processing.py)
        from app.models.a2_audio_transcript import A2AudioTranscript

        for n, (asset, task) in enumerate(((a, t1), (b, t2))):
            self.db.refresh(task)
            self.db.add(A2AudioTranscript(sha256=asset["sha256"], original_name=asset["original_filename"], status="TRANSCRIBED", text=f"Text {n}",
                                          storage_paths=[task.audio_storage_path], matches={str(task.id): {"status": "MATCHED"}}))
            task.is_published = True
        self.db.commit()
        r = readiness.compute(self.db)
        self.assertEqual(r["status"], "NEEDS_TESTING")
        for key in readiness.MANUAL_CHECKS:
            r = readiness.confirm(self.db, self.user["super"], key, True, "Sandbox" if key == "payment_tested" else None)
        self.assertEqual(r["status"], "READY")
        self.assertFalse(r["sales_enabled"])  # readiness never opens sales by itself
        # a missing file brings it back
        for f in self.root.rglob("*.m4a"):
            f.unlink()
        self.assertEqual(readiness.compute(self.db)["status"], "NEEDS_CONTENT")
        self.assertEqual(self._status(readiness.confirm, self.db, self.user["super"], "nonsense", True, None)[0], 422)

    # ---------- old archive cleanup ----------

    def test_cleanup_plan_quarantine_restore_purge(self):
        from sqlalchemy import select

        from app.models.listening_audio_archive import ListeningAudioArchive
        from app.services.a2_audio import assets, cleanup

        old_copy = self._task(1, "[Archiv] Hören", content_id="vizu-a2-l01-hoeren-01", audio=mp3("archiv"))
        legacy = self._task(1, "A2 1.Unterricht Hören", material_key=f"a2-l01-audio-{uuid.uuid4().hex[:4]}", audio=mp3("legacy"))
        current = self._task(2, "Hören", audio=mp3("current"))
        a1_task = self._task(1, "A1 Hören", level="A1", audio=mp3("a1"))
        shared = self._task(3, "[Archiv] Hören 3", content_id="vizu-a2-l03-hoeren-01")
        shared.audio_storage_path = a1_task.audio_storage_path  # the same file as an A1 task
        version_name = f"{uuid.uuid4().hex}.mp3"
        (self.root / version_name).write_bytes(mp3("version"))
        self.db.add(ListeningAudioArchive(listening_id=current.id, storage_path=version_name, archived_at=datetime.now(timezone.utc)))
        (self.root / "orphan.mp3").write_bytes(mp3("orphan"))
        lib = self._upload("A2 4.Unterricht Hören.mp3", mp3("library"))
        archived_lib = self._task(4, "[Archiv] Hören 4", content_id="vizu-a2-l04-hoeren-01")
        archived_lib.audio_storage_path = self.db.get(assets.A2AudioAsset, lib["id"]).storage_path
        self.db.commit()
        before = {p: (self.root / p).read_bytes() for p in self._files()}

        plan = cleanup.build_plan(self.db, self.root)
        by_path = {f["storage_path"]: f for f in plan["files"]}
        eligible = {p for p, f in by_path.items() if f["eligible"]}
        self.assertEqual(eligible, {old_copy.audio_storage_path, legacy.audio_storage_path, version_name})
        self.assertIn("A1", by_path[a1_task.audio_storage_path]["blocked_by"])
        self.assertIn("current A2 task", by_path[current.audio_storage_path]["blocked_by"])
        self.assertIn("A2 Audio Manager", by_path[archived_lib.audio_storage_path]["blocked_by"])
        self.assertEqual([u["storage_path"] for u in plan["unreferenced_files"]], ["orphan.mp3"])  # listed, never touched
        self.assertEqual(plan["summary"]["eligible_files"], 3)
        self.assertEqual(self._files(), sorted(before))  # plan is read-only
        self.assertIn(plan["plan_id"], cleanup.plan_markdown(plan))

        with self.assertRaises(cleanup.CleanupError):
            cleanup.quarantine(self.db, "wrong", self.root, self.qroot)
        q = cleanup.quarantine(self.db, plan["plan_id"], self.root, self.qroot)
        self.assertEqual({f["storage_path"] for f in q["files"]}, eligible)
        self.assertEqual(set(self._files()), set(before) - eligible)  # only the planned files moved
        for p in set(before) - eligible:
            self.assertEqual((self.root / p).read_bytes(), before[p])  # A1, current, library, orphan: unchanged
        self.db.expire_all()
        self.assertEqual(self.db.get(type(legacy), legacy.id).audio_storage_path, legacy.audio_storage_path)  # no DB row changed

        restored = cleanup.restore(Path(q["manifest"]))
        self.assertEqual(restored["state"], "restored")
        self.assertEqual({p: (self.root / p).read_bytes() for p in self._files()}, before)

        plan = cleanup.build_plan(self.db, self.root)
        q = cleanup.quarantine(self.db, plan["plan_id"], self.root, self.qroot)
        with self.assertRaises(cleanup.CleanupError):
            cleanup.purge(self.db, Path(q["manifest"]), "wrong")
        # meanwhile a current task starts using one of the quarantined files again -> that one is kept
        current.audio_storage_path = version_name
        self.db.commit()
        purged = cleanup.purge(self.db, Path(q["manifest"]), plan["plan_id"])
        states = {e["storage_path"]: e["state"] for e in purged["files"]}
        self.assertTrue(states[version_name].startswith("kept"))
        self.assertEqual({states[old_copy.audio_storage_path], states[legacy.audio_storage_path]}, {"purged"})
        self.assertEqual(purged["state"], "partially_purged")
        self.assertTrue((self.root / a1_task.audio_storage_path).is_file())
        self.assertEqual(self.db.scalars(select(ListeningAudioArchive).where(ListeningAudioArchive.storage_path == version_name)).first().storage_path,
                         version_name)  # DB rows are never deleted


if __name__ == "__main__":
    unittest.main()
