"""A2 audio processing (app/scripts/a2_audio_processing.py, services/a2_audio/
processing.py): transcripts per audio content, match with the task, answer
keys, publish rules, the admin overview and access control.

The data checks run without a database. The rest runs against PostgreSQL
(VIZU_WB_TEST_DB_URL, a migrated throwaway database) with a temporary
storage folder and generated test audio — no course audio is touched."""

import asyncio
import hashlib
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

from starlette.datastructures import Headers, UploadFile

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")


def mp3(seed: str = "") -> bytes:
    return b"ID3\x04\x00\x00\x00\x00\x00\x00" + (seed or uuid.uuid4().hex).encode() * 64


def record(data: bytes, name: str, text: str, status: str = "TRANSCRIBED") -> dict:
    return {"sha256": hashlib.sha256(data).hexdigest(), "original_name": name, "size_bytes": len(data), "duration_seconds": 61.4, "status": status,
            "text": text, "segments": [{"start": 0.0, "end": 61.4, "text": text}], "model": "test", "quality": {"agreement": 1.0}, "review_note": None}


class TestProcessingData(unittest.TestCase):
    """The shipped data: one record per content, every task names transcribed files, nothing guessed for lesson 13."""

    def test_records_and_tasks_fit_together(self):
        from app.scripts import a2_audio_processing as script
        from app.scripts.a2_audio_processing_data import TASKS

        records, names = script.load_records()
        self.assertEqual(len(records), len(names))  # one record per content, no duplicate names
        for r in records.values():
            with self.subTest(file=r["original_name"]):
                self.assertEqual(len(r["sha256"]), 64)
                self.assertIn(r["status"], ("TRANSCRIBED", "NEEDS_REVIEW", "FAILED"))
                self.assertTrue(r["segments"] and r["text"])
                self.assertNotRegex(r["text"], r"<[^>]*\?\d")  # no raw confidence markup left
        self.assertNotIn("A2 13.Unterricht Teil 1.m4a", names)  # identical to 12. Unterricht: same record
        for key, spec in TASKS.items():
            with self.subTest(task=key):
                self.assertTrue(all(script.nfc(n) in names for n in spec["audio"]), spec["audio"])
                self.assertIn(spec["match"]["status"], ("MATCHED", "NEEDS_REVIEW", "MISMATCH"))
                if spec["match"]["status"] == "MISMATCH":
                    self.assertNotIn("keys", spec)  # a wrong audio never gets keys
                if not spec.get("audio_only") and spec["match"]["status"] == "MATCHED":
                    self.assertTrue(spec["keys"] and spec["evidence"].startswith("Neu geprüft 2026-10-30"))
        self.assertEqual(sorted(k for k, s in TASKS.items() if s["match"]["status"] == "MISMATCH"),
                         [f"vizu-a2buch-l13-hoeren-0{n}" for n in (1, 2, 3, 4)])
        self.assertTrue(all(TASKS["vizu-a2buch-l06-hoeren-01"]["review"].get(n) for n in range(1, 13)))  # open questions stay NEEDS_REVIEW
        self.assertIn("[unverständlich]", records[names["A2 2.Unterricht Hören.mp3"]]["text"])  # a non-word is marked, not corrected


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestA2AudioProcessing(unittest.TestCase):
    PREFIX = "test-a2p-"

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
        structure.ensure_structure(db, "A2")
        tag = uuid.uuid4().hex[:6]
        users = {}
        for name, role in (("super", "SUPER_ADMIN"), ("editor", "CONTENT_MANAGER"), ("student", "STUDENT")):
            users[name] = User(email=f"a2p-{name}-{tag}@test.local", username=f"a2p_{name}_{tag}", password_hash="x", is_active=True,
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
        self._patch = patch.object(listening_storage, "ROOT", self.root)
        self._patch.start()
        self.db = self.Session()
        self.db.execute(text("TRUNCATE a2_audio_assets, a2_audio_transcripts"))
        a2_ids = [lesson.id for lesson in assets.a2_lessons(self.db)]
        mine = list(self.db.scalars(select(Listening).where(Listening.lesson_id.in_(a2_ids))))
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

    def _task(self, n, title, data: bytes | None, keyed: list[tuple[str, list[str], int]] | None = None, transcript=None, content_id=None):
        """keyed: [(question, options, index of the correct option or -1 for none)]"""
        from app.models.lesson_skill import ListeningOption, ListeningQuestion
        from app.models.listening import Listening

        t = Listening(lesson_id=self.lessons[n].id, title=title, content_id=content_id or f"{self.PREFIX}{uuid.uuid4().hex[:8]}", order_index=1,
                      is_published=False, transcript=transcript)
        if data is not None:
            name = f"{uuid.uuid4().hex}.mp3"
            (self.root / name).write_bytes(data)
            t.audio_storage_path, t.audio_content_type, t.audio_size_bytes, t.audio_original_name = name, "audio/mpeg", len(data), f"{title}.mp3"
        self.db.add(t)
        self.db.flush()
        for i, (q, options, ok) in enumerate(keyed or [], 1):
            self.db.add(ListeningQuestion(listening_id=t.id, question=q, order_index=i,
                                          options=[ListeningOption(option_text=o, is_correct=j == ok, order_index=j + 1) for j, o in enumerate(options)]))
        self.db.commit()
        return t

    def _run(self, tasks: dict, records: list[dict], audio_dir=None, publish=True):
        from app.scripts import a2_audio_processing as script

        recs = {r["sha256"]: r for r in records}
        names = {r["original_name"]: r["sha256"] for r in records}
        items = script.plan(self.db, audio_dir, recs, names, tasks)
        return items, script.apply(self.db, items, recs, names, publish)

    def _overview_task(self, listening_id):
        from app.services.a2_audio import processing

        for lesson in processing.overview(self.db)["lessons"]:
            for t in lesson["tasks"]:
                if t["listening_id"] == listening_id:
                    return t
        raise AssertionError("task not in overview")

    @staticmethod
    def _spec(audio, keys=None, status="MATCHED", **extra):
        spec = {"audio": audio, "match": {"status": status, "note": "test"}, "evidence": "Neu geprüft (Test): [0:05] „…“"}
        if keys is not None:
            spec["keys"] = keys
        spec.update(extra)
        return spec

    # ---------- tests ----------

    def test_matched_task_gets_verified_keys_transcript_and_is_published(self):
        from app.models.answer_key_review import AnswerKeyReview
        from app.models.listening import Listening

        data = mp3("hoeren-2")
        t = self._task(2, "Hören 2", data, [("Wer arbeitet in München?", ["Professor Müller", "Frau Millner"], 1),
                                            ("Wer hat zwei Kinder?", ["Professor Müller", "Frau Millner"], -1)])
        self.assertEqual(self._overview_task(t.id)["status"], "UPLOADED")  # no transcript yet
        rec = record(data, "A2 2.Unterricht Hören.mp3", "Er arbeitet an der Universität München. Sie ist Mutter von zwei Kindern.")
        items, report = self._run({t.content_id: self._spec(["A2 2.Unterricht Hören.mp3"], ["Professor Müller", "Frau Millner"])}, [rec])
        self.db.expire_all()
        t = self.db.get(Listening, t.id)
        self.assertTrue(t.is_published)
        self.assertEqual([o.is_correct for q in sorted(t.questions, key=lambda q: q.order_index) for o in q.options], [True, False, False, True])
        self.assertEqual(self.db.query(AnswerKeyReview).filter(AnswerKeyReview.listening_question_id.in_([q.id for q in t.questions]),
                                                               AnswerKeyReview.status == "verified").count(), 2)
        self.assertIn("Universität München", t.transcript)
        self.assertTrue(t.transcript.startswith("Transkript (automatisch"))
        self.assertEqual(t.audio_duration_seconds, 61)
        ov = self._overview_task(t.id)
        self.assertEqual((ov["status"], ov["keys"]["verified"], ov["match"]["status"]), ("PUBLISHED", 2, "MATCHED"))
        self.assertEqual(ov["files"][0]["transcript"]["status"], "TRANSCRIBED")
        self.assertNotIn("storage_path", json.dumps(ov, default=str))
        self.assertEqual(report[0]["transcripts"], {"created": 1, "reused": 0})

    def test_same_content_is_transcribed_once_and_a_wrong_audio_is_never_keyed(self):
        from app.models.a2_audio_transcript import A2AudioTranscript
        from app.models.listening import Listening

        data = mp3("teil-1")
        right = self._task(12, "Teil 1 (12)", data, [("Wie ist das Zimmer?", ["hell", "dunkel"], -1)])
        wrong = self._task(13, "Teil 1 (13)", data, [("Was wünscht sich Carmen?", ["ein Rad", "ein Buch"], -1)])
        rec = record(data, "A2 12.Unterricht Teil_1.m4a", "Es ist hell und gemütlich.")
        tasks = {right.content_id: self._spec(["A2 12.Unterricht Teil_1.m4a"], ["hell"]),
                 wrong.content_id: {"audio": ["A2 12.Unterricht Teil_1.m4a"], "match": {"status": "MISMATCH", "note": "byte-identisch mit 12"}}}
        self._run(tasks, [rec])
        rows = self.db.query(A2AudioTranscript).all()
        self.assertEqual(len(rows), 1)  # one transcript for one content
        self.assertEqual(len(rows[0].storage_paths), 2)
        self.assertEqual({v["status"] for v in rows[0].matches.values()}, {"MATCHED", "MISMATCH"})
        self.db.expire_all()
        wrong = self.db.get(Listening, wrong.id)
        self.assertFalse(wrong.is_published)
        self.assertFalse(any(o.is_correct for q in wrong.questions for o in q.options))
        self.assertIsNone(wrong.transcript)  # the other lesson's text is not shown
        self.assertEqual(self._overview_task(wrong.id)["status"], "NEEDS_REVIEW")
        self.assertTrue(self.db.get(Listening, right.id).is_published)
        # a second run reuses the finished transcript
        _, report = self._run(tasks, [rec])
        self.assertEqual(report[0]["transcripts"], {"created": 0, "reused": 2})

    def test_replaced_audio_review_keys_and_book_transcripts(self):
        from app.models.listening import Listening

        checked, stored = mp3("checked"), mp3("other")
        replaced = self._task(3, "Hören 3", stored, [("Richtig?", ["Richtig", "Falsch"], -1)])
        open_q = self._task(6, "Hören 6", data6 := mp3("six"), [("Wo?", ["im Sommerlager", "zu Hause"], -1)])
        book = self._task(1, "Hören 1", data1 := mp3("one"), [("Wer?", ["Johann", "Julia"], 0)], transcript="Buch-Transkript S. 14")
        recs = [record(checked, "A2 3.mp3", "x"), record(data6, "A2 6.mp3", "im Sommerlager"), record(data1, "A2 1.mp3", "Johann")]
        tasks = {replaced.content_id: self._spec(["A2 3.mp3"], ["Richtig"]),
                 open_q.content_id: self._spec(["A2 6.mp3"], ["im Sommerlager"], review={1: "offene Frage — Varianten prüfen"}),
                 book.content_id: self._spec(["A2 1.mp3"], ["Johann"])}
        items, _ = self._run(tasks, recs)
        self.assertIn("nicht die geprüften", next(i for i in items if i["task"].id == replaced.id)["problem"])
        self.db.expire_all()
        replaced, open_q, book = (self.db.get(Listening, x.id) for x in (replaced, open_q, book))
        self.assertFalse(replaced.is_published)
        self.assertFalse(any(o.is_correct for q in replaced.questions for o in q.options))  # nothing applied to a changed file
        self.assertEqual(self._overview_task(replaced.id)["status"], "UPLOADED")  # the stored file has no transcript
        self.assertFalse(open_q.is_published)  # a NEEDS_REVIEW key blocks publishing
        self.assertEqual(self._overview_task(open_q.id)["status"], "NEEDS_REVIEW")
        self.assertTrue(book.is_published)
        self.assertEqual(book.transcript, "Buch-Transkript S. 14")  # the book's transcript stays

    def test_missing_book_track_is_added_from_the_audio_dir(self):
        from app.models.listening import Listening

        one, two = mp3("max"), mp3("sara")
        t = self._task(7, "Reisen", one, [("Wer kommt aus Madrid?", ["Max", "Sara"], -1), ("Wer fliegt nach Rom?", ["Max", "Sara"], -1)])
        recs = [record(one, "Text 1.mp3", "Ich komme aus Madrid."), record(two, "Text 2.mp3", "mit dem Flugzeug nach Rom")]
        spec = self._spec(["Text 1.mp3", "Text 2.mp3"], ["Max", "Sara"], audio_label="Text 1", add_tracks=[{"label": "Text 2", "file": "Text 2.mp3"}])
        items, _ = self._run({t.content_id: spec}, recs)  # no --audio-dir: refused
        self.assertIn("fehlt", items[0]["problem"])
        self.db.expire_all()
        self.assertFalse(self.db.get(Listening, t.id).is_published)
        src = Path(self.tmp.name) / "book"
        src.mkdir()
        (src / "Text 2.mp3").write_bytes(b"not the same file")
        self.assertIn("anderen Inhalt", self._run({t.content_id: spec}, recs, audio_dir=src)[0][0]["problem"])
        (src / "Text 2.mp3").write_bytes(two)
        self._run({t.content_id: spec}, recs, audio_dir=src)
        self.db.expire_all()
        t = self.db.get(Listening, t.id)
        self.assertEqual((t.audio_label, [x.label for x in t.audio_tracks]), ("Text 1", ["Text 2"]))
        self.assertTrue(t.is_published)
        self.assertIn("Text 1:\nIch komme aus Madrid.", t.transcript)
        self.assertIn("Text 2:\nmit dem Flugzeug nach Rom", t.transcript)
        self.assertEqual(len(self._overview_task(t.id)["files"]), 2)

    def test_text_slot_is_published_with_verified_audio_and_transcript(self):
        from app.models.a2_audio_asset import A2AudioAsset
        from app.models.listening import Listening
        from app.services.a2_audio import lesson4_hoeren

        lesson4_hoeren.ensure_slots(self.db, self.user["editor"])
        data = mp3("text-1")
        upload = UploadFile(file=BytesIO(data), filename="A2 4.Unterricht Text 1.mp3", headers=Headers({"content-type": "audio/mpeg"}))
        slot = asyncio.run(lesson4_hoeren.upload(self.db, self.user["editor"], 1, upload, 50))
        rec = record(data, "A2 4.Unterricht Text 1.mp3", "Mein Name ist Johann.")
        self._run({"a2-u04-hoeren-text-1": {"audio": ["A2 4.Unterricht Text 1.mp3"], "audio_only": True, "match": {"status": "MATCHED", "note": "Text 1"}}},
                  [rec])
        self.db.expire_all()
        t = self.db.get(Listening, slot["listening_id"])
        self.assertTrue(t.is_published)
        asset = self.db.query(A2AudioAsset).filter_by(listening_id=t.id).one()
        self.assertEqual((asset.verification, asset.verified_by), ("verified", None))
        self.assertTrue(asset.verification_note.startswith("Automatisch geprüft"))
        self.assertEqual(self._overview_task(t.id)["status"], "PUBLISHED")
        # the other slots have no audio: not published, shown as FAILED (no audio)
        others = [self._overview_task(s["listening_id"]) for s in lesson4_hoeren.overview(self.db)["slots"] if s["slot"] != 1]
        self.assertEqual({o["status"] for o in others}, {"FAILED"})

    def test_slot_audio_from_the_general_upload_is_adopted_into_the_library(self):
        from app.models.a2_audio_asset import A2AudioAsset
        from app.models.listening import Listening
        from app.services.a2_audio import lesson4_hoeren
        from app.services.lesson_skills import admin as skill_admin

        lesson4_hoeren.ensure_slots(self.db, self.user["editor"])
        slot = next(s for s in lesson4_hoeren.overview(self.db)["slots"] if s["slot"] == 2)
        data = mp3("text-2")
        upload = UploadFile(file=BytesIO(data), filename="A2 4.Unterricht Text 2.mp3", headers=Headers({"content-type": "audio/mpeg"}))
        asyncio.run(skill_admin.upload_listening_audio(self.db, slot["listening_id"], upload, None))  # Media Management, not the slot page
        state = next(s for s in lesson4_hoeren.overview(self.db)["slots"] if s["slot"] == 2)
        self.assertEqual((state["audio"]["source"], state["can_activate"]), ("task", False))
        files_before = sorted(p.name for p in self.root.rglob("*") if p.is_file())
        self._run({"a2-u04-hoeren-text-2": {"audio": ["A2 4.Unterricht Text 2.mp3"], "audio_only": True, "match": {"status": "MATCHED", "note": "Text 2"}}},
                  [record(data, "A2 4.Unterricht Text 2.mp3", "Mein Name ist Anna.")])
        self.db.expire_all()
        t = self.db.get(Listening, slot["listening_id"])
        asset = self.db.query(A2AudioAsset).filter_by(listening_id=t.id).one()
        self.assertEqual((asset.storage_path, asset.unterricht, asset.audio_kind, asset.part), (t.audio_storage_path, 4, "TEXT", 2))
        self.assertEqual(asset.verification, "verified")
        self.assertTrue(t.is_published)
        self.assertEqual(sorted(p.name for p in self.root.rglob("*") if p.is_file()), files_before)  # same file, nothing copied
        state = next(s for s in lesson4_hoeren.overview(self.db)["slots"] if s["slot"] == 2)
        self.assertEqual((state["audio"]["source"], state["verified"]), ("library", True))  # the slot page manages it again

    def test_readiness_lists_unpublished_hoeren(self):
        from app.services.a2_audio import readiness

        self._task(5, "Hören 5", mp3("five"))
        check = next(c for c in readiness.compute(self.db)["checks"] if c["key"] == "hoeren_published")
        self.assertFalse(check["ok"])
        self.assertEqual(check["items"], ["5. Unterricht · Hören 5: UPLOADED — noch nicht transkribiert"])

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
    def test_access_scoring_and_transcript_after_the_attempt(self):
        data = mp3("lesson-1")
        t = self._task(1, "Hören 1", data, [("Wer ist Architekt?", ["Johann", "Julia"], -1), ("Wer ist Ärztin?", ["Johann", "Julia"], -1)])
        self._run({t.content_id: self._spec(["A2 1.mp3"], ["Johann", "Julia"])}, [record(data, "A2 1.mp3", "Johann ist Architekt.")])
        lesson = self.lessons[1]
        lesson.is_published = True
        self.db.commit()
        url = "/api/v1/admin/media-management/a2-audio/processing"
        self.assertEqual(self._client(None).get(url).status_code, 401)
        self.assertEqual(self._client("student").get(url).status_code, 403)
        body = self._client("editor").get(url).json()
        self.assertEqual(body["summary"]["published"], 1)
        self.assertEqual(len(body["lessons"]), 13)
        # the student side: published, transcript hidden before the first attempt, graded on the server
        staff = self._client("student")  # lesson 1 is the free preview: a logged-in student may open it
        section = staff.get(f"/api/v1/lesson-skills/{lesson.id}/hoeren").json()
        task = next(x for x in section["tasks"] if x["id"] == str(t.id))
        self.assertIsNone(task["transcript"])
        self.assertNotIn("is_correct", json.dumps(task))
        attempt = staff.post(f"/api/v1/lesson-skills/{lesson.id}/hoeren/{t.id}/start").json()
        q = {x["question"]: x for x in task["questions"]}
        answers = {q["Wer ist Architekt?"]["id"]: next(o["id"] for o in q["Wer ist Architekt?"]["options"] if o["text"] == "Johann"),
                   q["Wer ist Ärztin?"]["id"]: next(o["id"] for o in q["Wer ist Ärztin?"]["options"] if o["text"] == "Johann")}
        result = staff.post(f"/api/v1/lesson-skills/{lesson.id}/hoeren/{t.id}/submit", json={"attempt_id": attempt["id"], "answers": answers}).json()
        self.assertEqual((result["correct_count"], result["question_count"], result["score"]), (1, 2, 50))
        self.assertIn("Johann ist Architekt.", result["transcript"])
        again = staff.get(f"/api/v1/lesson-skills/{lesson.id}/hoeren").json()
        self.assertEqual(next(x for x in again["tasks"] if x["id"] == str(t.id))["summary"]["attempts_count"], 1)  # progress is kept
        self.assertEqual(staff.get(f"/api/v1/lesson-skills/{lesson.id}/hoeren/{t.id}/audio").content, data)


if __name__ == "__main__":
    unittest.main()
