"""Multilevel Modelltest 1: ONE shared Hören audio for all Teile (kompetenzen.audio_file_id), every other Modelltest unchanged.

Against PostgreSQL (VIZU_WB_TEST_DB_URL = a migrated test database) and real ffmpeg (FFMPEG_BIN; skipped without it); the real ten Modelltests are built in a
throwaway provider / level and the files go to a temp storage root. Covers: only Modelltest 1 is in shared mode; one upload / replace / trim / delete
for the whole Hören section; the per-Teil slots of Modelltest 1 are refused while the other tests keep theirs; the student paper carries one signed URL
and six Teile with their own questions (no per-Teil audio, no keys); the stream route (Range, token rules, draft = staff only); the audio length and the exam
time are independent; the publish check; scoring unchanged; 401 / 403 on the new routes."""

import asyncio
import os
import shutil
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from fastapi import HTTPException

from tests.test_multilevel_audio import sine_wav, upload

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
FFMPEG = shutil.which(os.environ.get("FFMPEG_BIN", "ffmpeg"))
TEIL_QUESTIONS = [5, 5, 6, 7, 6, 6]  # Modelltest 1 Hören: six Teile, 35 questions


class TestSharedAudioRoutesAuth(unittest.TestCase):
    def test_401_403(self):
        try:
            from fastapi.testclient import TestClient
        except Exception:  # httpx missing (server)
            self.skipTest("httpx not installed")
        from app.api.dependencies.auth import get_current_user
        from app.main import app

        client = TestClient(app)
        a = uuid.uuid4()
        base = f"/api/v1/admin/multilevel-audio/shared/{a}"
        calls = [("get", base, None), ("put", base, {"audio_file_id": str(a)}), ("post", base + "/trim", {"start_ms": 0, "end_ms": 1000}), ("delete", base, None), ("get", base + "/file", None)]
        for method, url, body in calls:
            self.assertEqual(getattr(client, method)(url, **({"json": body} if body else {})).status_code, 401, url)
        for role, writes_only in (("STUDENT", False), ("TEACHER", True)):  # a teacher may look (admin panel), only a content editor may change
            app.dependency_overrides[get_current_user] = lambda role=role: NS(id=uuid.uuid4(), role=role)
            try:
                for method, url, body in calls:
                    if writes_only and method == "get":
                        continue
                    self.assertEqual(getattr(client, method)(url, **({"json": body} if body else {})).status_code, 403, (role, url))
            finally:
                app.dependency_overrides.pop(get_current_user, None)
        # the student stream needs the token that comes with the exam paper
        self.assertEqual(client.get(f"/api/v1/multilevel-exam/audio-shared/{a}").status_code, 422)
        self.assertEqual(client.get(f"/api/v1/multilevel-exam/audio-shared/{a}?token=garbage").status_code, 401)


@unittest.skipUnless(DB_URL and FFMPEG, "integration test: set VIZU_WB_TEST_DB_URL and have ffmpeg (FFMPEG_BIN)")
class TestSharedAudioAgainstDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
        from app.core.storage.local import LocalStorage
        from app.models.audit_log import AuditLog
        from app.models.certification_provider import CertificationProvider
        from app.models.mock_exam_level import MockExamLevel
        from app.models.user import User
        from app.services.lesson_skills import admin as skill_admin
        from app.services.mock_exam import multilevel_service

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        db = cls.Session()
        if db.scalar(select(MockExamLevel).where(MockExamLevel.title == multilevel_service.LEVEL_TITLE)):
            db.close()
            raise unittest.SkipTest("the test database already holds a Multilevel level")
        cls.audit_before = set(db.scalars(select(AuditLog.id)))
        cls.tmp = tempfile.TemporaryDirectory()
        cls.images = tempfile.TemporaryDirectory()
        cls.patches = [patch.object(type(skill_admin.listening_storage), "ROOT", Path(cls.tmp.name)), patch.object(LocalStorage, "ROOT", Path(cls.images.name))]
        for p in cls.patches:
            p.start()
        tag = uuid.uuid4().hex[:6]
        users = []
        for name, role in (("s", "STUDENT"), ("e", "CONTENT_MANAGER")):
            u = User(email=f"mls-{name}-{tag}@test.local", username=f"mls_{name}_{tag}", password_hash="x", is_active=True, is_verified=True, is_superuser=False,
                     role=role, is_banned=False, preferred_language="uz", premium_until=datetime.now(timezone.utc) + timedelta(days=30))
            db.add(u)
            users.append(u)
        db.flush()
        # the student holds the Multilevel Premium (since 2026-11-16 every Multilevel Modelltest needs it)
        from app.models.user_entitlement import PRODUCT_MULTILEVEL_PREMIUM, UserEntitlement

        db.add(UserEntitlement(user_id=users[0].id, product=PRODUCT_MULTILEVEL_PREMIUM, source="PAYMENT", granted_at=datetime.now(timezone.utc)))
        # the audio slots only exist under provider NATIONAL (like production): reuse it, or create it for the run
        provider = db.scalar(select(CertificationProvider).where(CertificationProvider.code == multilevel_service.PROVIDER_CODE))
        cls.own_provider = provider is None
        if provider is None:
            provider = CertificationProvider(name=f"National {tag}", code=multilevel_service.PROVIDER_CODE, is_active=True)
            db.add(provider)
            db.flush()
        level = MockExamLevel(provider_id=provider.id, level="B1–C1", title=multilevel_service.LEVEL_TITLE, is_active=True)
        db.add(level)
        db.flush()
        cls.test_ids = {}
        for doc in multilevel_service.load_docs():
            cls.test_ids[doc["number"]] = multilevel_service._create_test(db, level, doc, multilevel_service.DATA_DIR).id
        db.commit()
        cls.user_ids = [u.id for u in users]
        cls.provider_id, cls.level_id = provider.id, level.id
        cls.created_audio = []
        db.close()

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete

        from app.models.audio_file import AudioFile
        from app.models.audit_log import AuditLog
        from app.models.certification_provider import CertificationProvider
        from app.models.user import User

        from app.models.mock_exam_level import MockExamLevel

        with cls.Session() as db:
            db.execute(delete(MockExamLevel).where(MockExamLevel.id == cls.level_id))  # its Modelltests, Teile, questions and attempts go with it
            if cls.own_provider:
                db.execute(delete(CertificationProvider).where(CertificationProvider.id == cls.provider_id))
            db.execute(delete(AudioFile).where(AudioFile.created_by_id.in_(cls.user_ids), AudioFile.kind == "TRIMMED"))
            db.execute(delete(AudioFile).where(AudioFile.created_by_id.in_(cls.user_ids)))
            db.execute(delete(AuditLog).where(AuditLog.id.not_in(cls.audit_before), AuditLog.action.like("multilevel_%")))
            db.execute(delete(AuditLog).where(AuditLog.actor_id.in_(cls.user_ids)))
            db.execute(delete(User).where(User.id.in_(cls.user_ids)))
            db.commit()
        for p in cls.patches:
            p.stop()
        cls.tmp.cleanup()
        cls.images.cleanup()
        cls.engine.dispose()

    # ---------------- helpers ----------------
    def users(self, db):
        from app.models.user import User

        return [db.get(User, i) for i in self.user_ids]

    def tid(self, number):
        return self.test_ids[number]

    def up(self, db, seconds=12.0, name="hoeren.wav"):
        from app.services.audio_files import service

        _, editor = self.users(db)
        return asyncio.run(service.store_original(db, upload(name, sine_wav(seconds), "audio/wav"), editor))

    def komp(self, db, number):
        from sqlalchemy import select

        from app.models.kompetenz import Kompetenz

        return db.scalar(select(Kompetenz).where(Kompetenz.model_test_id == self.tid(number), Kompetenz.type == "HOEREN"))

    def papers(self, db, number):
        from app.services.mock_exam import multilevel_exam_service as exam

        student, _ = self.users(db)
        attempt = exam.start_attempt(db, student, self.tid(number))
        exam.start_section(db, student, attempt.id, "HOEREN")
        return attempt, exam.section_paper(db, student, attempt.id, "HOEREN")

    # ---------------- tests (order matters: later ones build on earlier state) ----------------
    def test_1_only_modelltest_1_is_in_shared_mode_and_the_check_asks_for_one_audio(self):
        from app.services.mock_exam import multilevel_audio as ml_audio
        from app.services.mock_exam import multilevel_service as ml

        self.assertEqual(ml.SHARED_AUDIO_NUMBERS, frozenset({1}))
        with self.Session() as db:
            overview = {t["sort_order"]: t for t in ml_audio.overview(db)["tests"]}
            self.assertEqual((overview[1]["shared"]["status"], len(overview[1]["slots"]), all(s["shared"] for s in overview[1]["slots"])), ("missing", 6, True))
            self.assertEqual([t["teil_id"] is not None and t["questions"] for t in overview[1]["shared"]["teile"]], TEIL_QUESTIONS)
            for number in range(2, 11):
                self.assertIsNone(overview[number]["shared"], number)  # every other Modelltest keeps one slot per Teil
                self.assertFalse(any(s["shared"] for s in overview[number]["slots"]), number)
            self.assertEqual(ml.readiness(db, self.tid(1))["missing_audio"], ["Hören: gemeinsames Audio"])  # one thing missing, not six
            self.assertEqual(len(ml.readiness(db, self.tid(2))["missing_audio"]), 4)
            with self.assertRaises(HTTPException) as ctx:
                ml_audio.shared_status(db, self.tid(2))
            self.assertEqual((ctx.exception.status_code, ctx.exception.detail), (404, "SHARED_AUDIO_NOT_AVAILABLE"))

    def test_2_one_upload_serves_all_six_teile_and_the_per_teil_slots_are_refused(self):
        from app.services.mock_exam import multilevel_audio as ml_audio
        from app.services.mock_exam import multilevel_service as ml

        with self.Session() as db:
            _, editor = self.users(db)
            audio = self.up(db, 12.0)
            self.created_audio.append(audio.id)
            status = asyncio.run(ml_audio.attach_shared(db, self.tid(1), audio.id, editor))
            self.assertEqual((status["status"], status["duration_ms"] // 1000, status["exam_minutes"]), ("ok", 12, 60))
            self.assertEqual([t["questions"] for t in status["teile"]], TEIL_QUESTIONS)
            overview = {t["sort_order"]: t for t in ml_audio.overview(db)["tests"]}
            self.assertEqual({s["status"] for s in overview[1]["slots"]}, {"ok"})  # all six Teile are covered by the one file
            self.assertEqual(ml.readiness(db, self.tid(1))["missing_audio"], [])
            # the six per-Teil slots of this test refuse their own audio; the other Modelltests are untouched and still take one per Teil
            slot = overview[1]["slots"][0]["content_id"]
            for call in (lambda: asyncio.run(ml_audio.attach(db, slot, audio.id, editor)), lambda: asyncio.run(ml_audio.detach(db, slot, editor)),
                         lambda: asyncio.run(ml_audio.trim_slot(db, slot, 0, 1000, editor))):
                with self.assertRaises(HTTPException) as ctx:
                    call()
                self.assertEqual(ctx.exception.status_code, 409)
                self.assertTrue(str(ctx.exception.detail).startswith("SHARED_AUDIO_TEST"))
            other = overview[2]["slots"][0]["content_id"]
            attached = asyncio.run(ml_audio.attach(db, other, self.up(db, 5.0, "teil.wav").id, editor))
            self.assertEqual((attached["status"], attached["shared"]), ("ok", False))
            self.assertIsNone(ml_audio.overview(db)["tests"][1]["shared"])
            asyncio.run(ml_audio.detach(db, other, editor))  # back to the empty state of test 2

    def test_3_the_student_paper_has_one_audio_and_six_separate_teile(self):
        from app.models.model_test import ModelTest
        from app.services.mock_exam import multilevel_exam_service as exam
        from app.services.mock_exam import multilevel_audio as ml_audio

        with self.Session() as db:
            student, editor = self.users(db)
            db.get(ModelTest, self.tid(1)).status = "PUBLISHED"  # a draft is not takeable
            db.commit()
            attempt, paper = self.papers(db, 1)
            self.assertEqual(len(paper["teile"]), 6)
            self.assertEqual([len(t["questions"]) for t in paper["teile"]], TEIL_QUESTIONS)
            self.assertEqual([t["title"] for t in paper["teile"]], [f"Teil {n}" for n in range(1, 7)])
            self.assertTrue(all(t["audio_url"] is None and t["audio_shared"] for t in paper["teile"]))  # no audio of their own: one shared player above
            self.assertNotIn("is_correct", str(paper))
            shared = paper["shared_audio"]
            self.assertEqual(shared["duration_ms"] // 1000, 12)
            self.assertTrue(shared["url"].startswith(f"/api/v1/multilevel-exam/audio-shared/{shared['kompetenz_id']}?token="))
            self.assertEqual(shared["kompetenz_id"], self.komp(db, 1).id)
            # the admin preview shows the same single audio (staff may preview a draft)
            preview = exam.admin_preview(db, self.tid(1), editor.id)
            hoeren = next(s for s in preview["sections"] if s["type"] == "HOEREN")
            self.assertIsNotNone(hoeren["shared_audio"])
            self.assertTrue(all(t["audio_url"] is None for t in hoeren["teile"]))
            self.assertTrue(any("is_correct" in str(t) for t in hoeren["teile"]))
            self.assertTrue(ml_audio.is_shared(db, self.komp(db, 1)) and not ml_audio.is_shared(db, self.komp(db, 2)))
            exam.finish_attempt(db, student, attempt.id)

    def test_4_the_stream_serves_the_file_with_range_and_follows_the_token_rules(self):
        try:
            from fastapi.testclient import TestClient
        except Exception:
            self.skipTest("httpx not installed")
        from app.db.session import get_db
        from app.main import app
        from app.models.model_test import ModelTest
        from app.services.mock_exam import multilevel_audio as ml_audio

        def override():
            with self.Session() as session:
                yield session

        app.dependency_overrides[get_db] = override
        try:
            client = TestClient(app)
            with self.Session() as db:
                student, editor = self.users(db)
                komp = self.komp(db, 1)
                url = ml_audio.shared_for_paper(db, komp, student.id)["url"]
                other_komp = self.komp(db, 2)
            full = client.get(url)
            self.assertEqual((full.status_code, full.headers["content-type"], full.headers["cache-control"]), (200, "audio/wav", "private, no-store"))
            part = client.get(url, headers={"Range": "bytes=0-99"})
            self.assertEqual((part.status_code, len(part.content), part.headers["content-range"].startswith("bytes 0-99/")), (206, 100, True))
            self.assertEqual(len(full.content), int(part.headers["content-range"].split("/")[1]))
            # a token is for one section and one purpose: the per-Teil audio token (other purpose) and another section's token do not work here
            from app.core.config import settings
            from app.core.security.jwt import create_access_token

            wrong_purpose = create_access_token({"sub": str(komp.id), "purpose": "multilevel_audio", "user_id": str(student.id)}, expires_minutes=5)
            self.assertEqual(client.get(f"/api/v1/multilevel-exam/audio-shared/{komp.id}?token={wrong_purpose}").status_code, 403)
            other = create_access_token({"sub": str(other_komp.id), "purpose": ml_audio.SHARED_PURPOSE, "user_id": str(student.id)}, expires_minutes=5)
            self.assertEqual(client.get(f"/api/v1/multilevel-exam/audio-shared/{komp.id}?token={other}").status_code, 403)
            self.assertEqual(client.get(f"/api/v1/multilevel-exam/audio-shared/{other_komp.id}?token={other}").status_code, 404)  # not a shared-audio section
            self.assertEqual(client.get(f"/api/v1/multilevel-exam/audio-shared/{komp.id}?token=garbage").status_code, 401)
            ghost = create_access_token({"sub": str(komp.id), "purpose": ml_audio.SHARED_PURPOSE, "user_id": str(uuid.uuid4())}, expires_minutes=5)
            self.assertEqual(client.get(f"/api/v1/multilevel-exam/audio-shared/{komp.id}?token={ghost}").status_code, 401)
            self.assertGreater(settings.VIDEO_STREAM_TOKEN_EXPIRE_MINUTES, 0)
            # a draft test: students are refused, staff may listen
            with self.Session() as db:
                db.get(ModelTest, self.tid(1)).status = "DRAFT"
                db.commit()
                staff_url = ml_audio.shared_for_paper(db, self.komp(db, 1), editor.id)["url"]
            self.assertEqual(client.get(url).status_code, 404)
            self.assertEqual(client.get(staff_url).status_code, 200)
            with self.Session() as db:
                db.get(ModelTest, self.tid(1)).status = "PUBLISHED"
                db.commit()
            self.assertEqual(client.get(url).status_code, 200)
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_5_audio_length_and_exam_time_are_independent(self):
        from sqlalchemy import select

        from app.models.mock_attempt_section import MockAttemptSection
        from app.services.mock_exam import multilevel_audio as ml_audio
        from app.services.mock_exam import multilevel_exam_service as exam

        with self.Session() as db:
            student, editor = self.users(db)
            attempt, paper = self.papers(db, 1)
            self.assertEqual(paper["shared_audio"]["duration_ms"] // 1000, 12)  # a 12 second audio …
            self.assertTrue(3595 <= paper["remaining_seconds"] <= 3600)  # … in a 60 minute section
            s = db.scalar(select(MockAttemptSection).where(MockAttemptSection.attempt_id == attempt.id, MockAttemptSection.section_type == "HOEREN"))
            self.assertEqual(s.duration_seconds, 3600)
            # another, longer audio does not change the exam time; another exam time does not change the audio
            asyncio.run(ml_audio.attach_shared(db, self.tid(1), self.up(db, 25.0, "lang.wav").id, editor))
            self.assertEqual(self.komp(db, 1).duration_minutes, 60)
            self.assertEqual(exam.section_paper(db, student, attempt.id, "HOEREN")["shared_audio"]["duration_ms"] // 1000, 25)
            self.assertEqual(exam.attempt_view(db, student, attempt.id)["sections"][1]["duration_seconds"], 3600)  # the running section keeps its granted time
            komp = self.komp(db, 1)
            komp.duration_minutes = 50
            db.commit()
            self.assertEqual(ml_audio.shared_status(db, self.tid(1))["duration_ms"] // 1000, 25)
            self.assertEqual(ml_audio.shared_status(db, self.tid(1))["exam_minutes"], 50)
            komp.duration_minutes = 60
            db.commit()
            exam.finish_attempt(db, student, attempt.id)

    def test_6_replace_trim_and_delete(self):
        from sqlalchemy import select

        from app.models.audio_file import AudioFile
        from app.models.model_test import ModelTest
        from app.services.mock_exam import multilevel_audio as ml_audio
        from app.services.mock_exam import multilevel_service as ml

        with self.Session() as db:
            _, editor = self.users(db)
            first = self.komp(db, 1).audio_file
            self.assertEqual(first.kind, "ORIGINAL")
            trimmed = asyncio.run(ml_audio.trim_shared(db, self.tid(1), 0, 8000, editor))
            self.assertEqual((trimmed["status"], trimmed["audio"]["kind"], trimmed["duration_ms"] // 1000), ("ok", "TRIMMED", 8))
            self.assertEqual(trimmed["original"]["id"], first.id)  # re-trim always starts from the original
            cut_name = Path(self.tmp.name) / self.komp(db, 1).audio_file.storage_path
            self.assertTrue(cut_name.is_file())
            again = asyncio.run(ml_audio.trim_shared(db, self.tid(1), 1000, 5000, editor))
            self.assertEqual(again["duration_ms"] // 1000, 4)
            self.assertFalse(cut_name.exists(), "the previous cut nobody uses any more is removed")
            self.assertTrue((Path(self.tmp.name) / first.storage_path).is_file(), "the original stays")
            # replace by a different upload: the old ORIGINAL stays on disk (it can be restored), the section plays the new file
            new = self.up(db, 15.0, "neu.wav")
            replaced = asyncio.run(ml_audio.attach_shared(db, self.tid(1), new.id, editor))
            self.assertEqual((replaced["audio"]["id"], replaced["duration_ms"] // 1000), (new.id, 15))
            self.assertTrue((Path(self.tmp.name) / first.storage_path).is_file())
            # delete: the section has no audio; Modelltest 1 is one of the open tests (1–6, 2026-11-18): it STAYS published (Hören is then
            # shown without a player) — questions / answers stay
            db.get(ModelTest, self.tid(1)).status = "PUBLISHED"
            db.commit()
            gone = asyncio.run(ml_audio.detach_shared(db, self.tid(1), editor))
            self.assertEqual((gone["status"], gone["test_unpublished"], gone["audio"]), ("missing", False, None))
            self.assertEqual(db.get(ModelTest, self.tid(1)).status, "PUBLISHED")
            self.assertEqual([t["questions"] for t in gone["teile"]], TEIL_QUESTIONS)
            self.assertEqual(ml.readiness(db, self.tid(1))["missing_audio"], ["Hören: gemeinsames Audio"])
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(ml_audio.detach_shared(db, self.tid(1), editor))
            self.assertEqual(ctx.exception.status_code, 404)
            self.assertIsNotNone(db.scalar(select(AudioFile).where(AudioFile.id == new.id)))  # the uploaded file itself is kept

    def test_7_scoring_is_unchanged_by_the_shared_audio(self):
        from sqlalchemy import select

        from app.models.mock_attempt_section import MockAttemptSection
        from app.models.model_test import ModelTest
        from app.scripts import multilevel_hoeren_keys as script
        from app.services.mock_exam import multilevel_audio as ml_audio
        from app.services.mock_exam import multilevel_exam_service as exam
        from app.services.mock_exam import multilevel_keys as keys

        with self.Session() as db:
            student, editor = self.users(db)
            plan = script.build_plan(db)
            script.apply_plan(db, plan["plan_id"])  # the owner's Hören keys, as on production
            asyncio.run(ml_audio.attach_shared(db, self.tid(1), self.up(db, 12.0, "final.wav").id, editor))
            db.get(ModelTest, self.tid(1)).status = "PUBLISHED"
            db.commit()
            attempt, _ = self.papers(db, 1)
            rows = keys._questions(db, self.tid(1), "HOEREN")
            self.assertEqual(len(rows), 35)
            for index, (q, _teil) in enumerate(rows):
                good = next(o for o in q.options if o.is_correct)
                chosen = good if index else next(o for o in q.options if not o.is_correct)  # one wrong answer
                exam.save_answer(db, student, attempt.id, "HOEREN", q.id, [chosen.id])
            exam.submit_section(db, student, attempt.id, "HOEREN")
            result = exam.attempt_view(db, student, attempt.id)["sections"][1]
            self.assertEqual(result["status"], "SUBMITTED")
            s = db.scalar(select(MockAttemptSection).where(MockAttemptSection.attempt_id == attempt.id, MockAttemptSection.section_type == "HOEREN"))
            self.assertEqual((s.raw_points, s.raw_max, s.score), (34, 35, 73))
            exam.finish_attempt(db, student, attempt.id)


if __name__ == "__main__":
    unittest.main()
