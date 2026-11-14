"""Central audio service + Multilevel Audio against PostgreSQL (VIZU_WB_TEST_DB_URL = a migrated test database) and real
ffmpeg (set FFMPEG_BIN when ffmpeg is not on PATH; tests skip without it). Files go to a temp storage root.

Covers: upload (content check, duration), trim (new file, original kept, re-trim from the original, bad ranges), every
slot (attach = upload/replace, trim, delete -> no audio, wrong provider/level refused), the exam paper with and without
audio (no error), signed student stream (published only, token bound to the slot) and the files left on disk."""

import asyncio
import io
import os
import shutil
import struct
import tempfile
import unittest
import uuid
import wave
from math import pi, sin
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
FFMPEG = shutil.which(os.environ.get("FFMPEG_BIN", "ffmpeg"))


def sine_wav(seconds: float = 10.0) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(22050)
        w.writeframes(b"".join(struct.pack("<h", int(12000 * sin(2 * pi * 440 * i / 22050))) for i in range(int(22050 * seconds))))
    return buf.getvalue()


def upload(name: str, data: bytes, ctype: str):
    from starlette.datastructures import Headers, UploadFile

    return UploadFile(io.BytesIO(data), filename=name, headers=Headers({"content-type": ctype}))


@unittest.skipUnless(DB_URL and FFMPEG, "integration test: set VIZU_WB_TEST_DB_URL and have ffmpeg (FFMPEG_BIN)")
class TestMultilevelAudio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
        from app.models.certification_provider import CertificationProvider
        from app.models.kompetenz import Kompetenz
        from app.models.listening_content import ListeningContent
        from app.models.mock_exam_level import MockExamLevel
        from app.models.model_test import ModelTest
        from app.models.teil import Teil
        from app.models.user import User
        from app.services.lesson_skills import admin as skill_admin
        from app.services.mock_exam import multilevel_service as ml

        cls.tmp = tempfile.TemporaryDirectory()
        cls.patch = patch.object(type(skill_admin.listening_storage), "ROOT", Path(cls.tmp.name))
        cls.patch.start()
        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        tag = uuid.uuid4().hex[:6]
        cls.created = {"tests": [], "levels": [], "providers": []}
        with cls.Session() as db:
            users = []
            for name, role in (("student", "STUDENT"), ("admin", "ADMIN")):
                u = User(email=f"mla-{name}-{tag}@test.local", username=f"mla_{name}_{tag}", password_hash="x", is_active=True,
                         is_verified=True, is_superuser=False, role=role, is_banned=False, preferred_language="uz")
                db.add(u)
                users.append(u)
            provider = db.scalar(select(CertificationProvider).where(CertificationProvider.code == ml.PROVIDER_CODE))
            if provider is None:
                provider = CertificationProvider(name=f"National {tag}", code=ml.PROVIDER_CODE)
                db.add(provider)
                db.flush()
                cls.created["providers"].append(provider.id)
            level = db.scalar(select(MockExamLevel).where(MockExamLevel.provider_id == provider.id, MockExamLevel.title == ml.LEVEL_TITLE))
            if level is None:
                level = MockExamLevel(provider_id=provider.id, level=ml.LEVEL_CODE, title=ml.LEVEL_TITLE)
                db.add(level)
                db.flush()
                cls.created["levels"].append(level.id)
            other_provider = CertificationProvider(name=f"Other {tag}", code=f"X{tag}"[:30])
            db.add(other_provider)
            db.flush()
            cls.created["providers"].append(other_provider.id)
            other_level = MockExamLevel(provider_id=other_provider.id, level="A1", title=f"A1 {tag}")
            db.add(other_level)
            db.flush()
            cls.created["levels"].append(other_level.id)
            cls.content_ids, cls.test_ids = [], []
            for lvl, count in ((level, 3), (other_level, 1)):
                test = ModelTest(level_id=lvl.id, title=f"MLA {tag} {lvl.title}", status="DRAFT", sort_order=99)
                db.add(test)
                db.flush()
                cls.created["tests"].append(test.id)
                k = Kompetenz(model_test_id=test.id, type="HOEREN", title="Hören", duration_minutes=40, sort_order=2)
                db.add(k)
                db.flush()
                ids = []
                for n in range(1, count + 1):
                    teil = Teil(kompetenz_id=k.id, title=f"Teil {n}", sort_order=n)
                    db.add(teil)
                    db.flush()
                    lc = ListeningContent(teil_id=teil.id, audio_url="")
                    db.add(lc)
                    db.flush()
                    ids.append(lc.id)
                cls.content_ids.append(ids)
                cls.test_ids.append(test.id)
            db.commit()
            cls.user_ids = [u.id for u in users]
        cls.wav = sine_wav(10.0)

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete

        from app.models.audio_file import AudioFile
        from app.models.certification_provider import CertificationProvider
        from app.models.mock_exam_level import MockExamLevel
        from app.models.model_test import ModelTest
        from app.models.user import User
        from app.models.audit_log import AuditLog

        with cls.Session() as db:
            db.execute(delete(ModelTest).where(ModelTest.id.in_(cls.created["tests"])))
            db.execute(delete(AuditLog).where(AuditLog.actor_id.in_([str(i) for i in cls.user_ids])))
            db.execute(delete(AudioFile).where(AudioFile.created_by_id.in_(cls.user_ids), AudioFile.kind == "TRIMMED"))
            db.execute(delete(AudioFile).where(AudioFile.created_by_id.in_(cls.user_ids)))
            db.execute(delete(MockExamLevel).where(MockExamLevel.id.in_(cls.created["levels"])))
            db.execute(delete(CertificationProvider).where(CertificationProvider.id.in_(cls.created["providers"])))
            db.execute(delete(User).where(User.id.in_(cls.user_ids)))
            db.commit()
        cls.patch.stop()
        cls.tmp.cleanup()
        cls.engine.dispose()

    def setUp(self):
        self.db = self.Session()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    # helpers
    def admin(self):
        from app.models.user import User

        return self.db.get(User, self.user_ids[1])

    def student(self):
        from app.models.user import User

        return self.db.get(User, self.user_ids[0])

    def up(self, name="a.wav", data=None, ctype="audio/wav"):
        from app.services.audio_files import service

        return asyncio.run(service.store_original(self.db, upload(name, data or self.wav, ctype), self.admin()))

    def files_on_disk(self):
        return {p.name for p in Path(self.tmp.name).iterdir() if p.is_file()}

    # 1 + 2: Media Management upload, trim, original kept ----------------------------------------------------
    def test_1_upload_trim_keeps_original(self):
        from app.services.audio_files import service

        original = self.up()
        self.assertEqual(original.kind, "ORIGINAL")
        self.assertAlmostEqual(original.duration_ms, 10_000, delta=120)
        self.assertEqual(service.serialize(original)["file_status"], "ok")
        cut = asyncio.run(service.trim(self.db, original.id, 2_000, 6_500, self.admin()))
        self.assertEqual((cut.kind, cut.source_id, cut.trim_start_ms, cut.trim_end_ms), ("TRIMMED", original.id, 2_000, 6_500))
        self.assertAlmostEqual(cut.duration_ms, 4_500, delta=200)
        self.assertNotEqual(cut.storage_path, original.storage_path)
        self.assertTrue(service.path_of(original).exists() and service.path_of(cut).exists())  # original untouched
        again = asyncio.run(service.trim(self.db, cut.id, 0, 3_000, self.admin()))  # re-trim: from the ORIGINAL again
        self.assertEqual(again.source_id, original.id)
        self.assertAlmostEqual(again.duration_ms, 3_000, delta=200)
        for bad in ((5_000, 5_000), (6_000, 2_000), (0, 99_999), (1_000, 1_200)):
            with self.subTest(bad=bad), self.assertRaises(HTTPException) as ctx:
                asyncio.run(service.trim(self.db, original.id, *bad, self.admin()))
            self.assertEqual(ctx.exception.status_code, 422)

    def test_2_mp3_m4a_and_bad_files(self):
        import subprocess

        from app.services.audio_files import service

        for ext in ("mp3", "m4a"):
            with self.subTest(fmt=ext):
                src = Path(self.tmp.name) / f"src-{uuid.uuid4().hex}.wav"
                dst = Path(self.tmp.name) / f"enc-{uuid.uuid4().hex}.{ext}"
                src.write_bytes(self.wav)
                subprocess.run([FFMPEG, "-nostdin", "-v", "error", "-y", "-i", str(src), *(["-c:a", "aac"] if ext == "m4a" else []), str(dst)], check=True)
                data = dst.read_bytes()
                src.unlink(), dst.unlink()
                original = self.up(f"a.{ext}", data, "audio/mpeg" if ext == "mp3" else "audio/mp4")
                cut = asyncio.run(service.trim(self.db, original.id, 1_000, 4_000, self.admin()))
                self.assertTrue(cut.storage_path.endswith(f".{ext}"))
                self.assertAlmostEqual(cut.duration_ms, 3_000, delta=300)
        with self.assertRaises(HTTPException) as ctx:
            self.up("x.mp3", b"this is not audio at all, just text", "audio/mpeg")
        self.assertEqual(ctx.exception.status_code, 400)
        with self.assertRaises(HTTPException) as ctx:
            self.up("x.wav", b"RIFF\x00\x00\x00\x00WAVEgarbage" + b"\0" * 200, "audio/wav")  # right header, not decodable
        self.assertEqual(ctx.exception.status_code, 400)

    # 5-9: slots ------------------------------------------------------------------------------------------------
    def test_3_slots_upload_replace_delete(self):
        from app.models.listening_content import ListeningContent
        from app.models.model_test import ModelTest
        from app.services.audio_files import service
        from app.services.mock_exam import multilevel_audio as ml_audio

        ov = ml_audio.overview(self.db)
        mine = next(t for t in ov["tests"] if t["model_test_id"] == self.test_ids[0])
        self.assertEqual([s["aufgabe_number"] for s in mine["slots"]], [1, 2, 3])
        self.assertTrue(all(s["status"] == "missing" for s in mine["slots"]))
        self.assertFalse(any(t["model_test_id"] == self.test_ids[1] for t in ov["tests"]))  # other provider's test: not listed

        # every slot: upload -> ok, plays in its own Teil
        for content_id in self.content_ids[0]:
            original = self.up()
            slot = asyncio.run(ml_audio.attach(self.db, content_id, original.id, self.admin()))
            self.assertEqual(slot["status"], "ok")
            self.assertAlmostEqual(slot["duration_ms"], 10_000, delta=120)
            lc = self.db.get(ListeningContent, content_id)
            self.assertEqual(lc.audio_url, f"mlaudio:{original.id}")
        first = self.content_ids[0][0]

        # trim the slot: a new cut plays, the original stays, the previous cut (if any) is gone
        slot = asyncio.run(ml_audio.trim_slot(self.db, first, 1_000, 4_000, self.admin()))
        self.assertAlmostEqual(slot["duration_ms"], 3_000, delta=250)
        cut_id, original_id = slot["audio"]["id"], slot["original"]["id"]
        slot = asyncio.run(ml_audio.trim_slot(self.db, first, 0, 2_000, self.admin()))
        self.assertAlmostEqual(slot["duration_ms"], 2_000, delta=250)
        self.assertEqual(slot["original"]["id"], original_id)
        self.db.expire_all()
        self.assertIsNotNone(self.db.get(__import__("app.models.audio_file", fromlist=["AudioFile"]).AudioFile, cut_id).deleted_at)  # replaced cut removed
        self.assertTrue(service.path_of(self.db.get(__import__("app.models.audio_file", fromlist=["AudioFile"]).AudioFile, uuid.UUID(str(original_id)))).exists())

        # replace with a new upload
        replacement = self.up("b.wav", sine_wav(5.0))
        slot = asyncio.run(ml_audio.attach(self.db, first, replacement.id, self.admin()))
        self.assertAlmostEqual(slot["duration_ms"], 5_000, delta=120)

        # a published test goes back to DRAFT when a slot loses its audio; no error without audio
        test = self.db.get(ModelTest, self.test_ids[0])
        test.status = "PUBLISHED"
        self.db.commit()
        out = asyncio.run(ml_audio.detach(self.db, first, self.admin()))
        self.assertEqual((out["status"], out["audio"], out["test_unpublished"]), ("missing", None, True))
        self.assertEqual(self.db.get(ModelTest, self.test_ids[0]).status, "DRAFT")
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(ml_audio.detach(self.db, first, self.admin()))
        self.assertEqual(ctx.exception.status_code, 404)

        # the exam paper of a slot without audio: audio_url None, nothing breaks
        from app.models.kompetenz import Kompetenz
        from app.services.mock_exam import multilevel_exam_service as exam
        from sqlalchemy import select

        komp = self.db.scalar(select(Kompetenz).where(Kompetenz.model_test_id == self.test_ids[0], Kompetenz.type == "HOEREN"))
        paper = exam._paper(self.db, komp, user_id=self.user_ids[0])
        self.assertIsNone(paper[0]["audio_url"])
        self.assertTrue(paper[1]["audio_url"].startswith(f"/api/v1/multilevel-exam/audio/{self.content_ids[0][1]}?token="))

    def test_4_wrong_level_refused(self):
        from app.services.mock_exam import multilevel_audio as ml_audio

        foreign = self.content_ids[1][0]  # a Hören Teil of another provider's level
        original = self.up()
        for call in (lambda: asyncio.run(ml_audio.attach(self.db, foreign, original.id, self.admin())),
                     lambda: asyncio.run(ml_audio.detach(self.db, foreign, self.admin())),
                     lambda: ml_audio.slot_status(self.db, foreign),
                     lambda: ml_audio.slot_status(self.db, uuid.uuid4())):
            with self.assertRaises(HTTPException) as ctx:
                call()
            self.assertEqual((ctx.exception.status_code, ctx.exception.detail), (404, "SLOT_NOT_FOUND"))

    def test_5_signed_stream(self):
        from app.models.model_test import ModelTest
        from app.models.listening_content import ListeningContent
        from app.services.mock_exam import multilevel_audio as ml_audio

        content_id = self.content_ids[0][2]
        asyncio.run(ml_audio.attach(self.db, content_id, self.up().id, self.admin()))
        lc = self.db.get(ListeningContent, content_id)
        student_token = ml_audio.signed_url(lc, self.user_ids[0]).split("token=")[1]
        admin_token = ml_audio.signed_url(lc, self.user_ids[1]).split("token=")[1]
        with self.assertRaises(HTTPException) as ctx:  # DRAFT test: a student gets nothing
            ml_audio.stream_target(self.db, content_id, student_token)
        self.assertEqual(ctx.exception.status_code, 404)
        path, ctype = ml_audio.stream_target(self.db, content_id, admin_token)  # staff may preview
        self.assertTrue(path.exists() and ctype == "audio/wav")
        test = self.db.get(ModelTest, self.test_ids[0])
        test.status = "PUBLISHED"
        self.db.commit()
        self.assertTrue(ml_audio.stream_target(self.db, content_id, student_token)[0].exists())
        for bad_token, other_slot, code in (("garbage", content_id, 401), (student_token, self.content_ids[0][1], 403)):
            with self.subTest(code=code), self.assertRaises(HTTPException) as ctx:
                ml_audio.stream_target(self.db, other_slot, bad_token)
            self.assertEqual(ctx.exception.status_code, code)
        test.status = "DRAFT"
        self.db.commit()


if __name__ == "__main__":
    unittest.main()
