"""Multilevel Modelltest 1–6 open for every student (2026-11-18), against PostgreSQL (VIZU_WB_TEST_DB_URL):
* publish guard: missing answer keys / Hören audio are warnings for 1–6 (publishable), a structurally incomplete test is still refused, 7–10
  keep the full rule;
* access (since 2026-11-19): every Modelltest 1–10 needs the Multilevel Premium (staff always), nobody anonymous — the lenient publish rule
  of 1–6 does not open them;
* the script app/scripts/multilevel_open_tests.py: read-only plan, wrong id refused, apply links the unused "Variant 1 Hören" upload as
  Modelltest 1's shared audio, reports a per-Teil test's whole-section file as MANUAL (not linked), publishes the complete tests, leaves the
  incomplete one, writes audit entries, a second plan is KEEP only;
* scoring: a question without a key is not graded; a section without any key is not scored and left out of the total (max 225), the result
  is not stuck in "Ausstehend"; removing the audio of a published open test does not hide it."""

import asyncio
import os
import unicodedata
import unittest
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL")
class TestOpenModelltests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
        from app.models.audio_file import AudioFile
        from app.models.audit_log import AuditLog
        from app.models.certification_provider import CertificationProvider
        from app.models.kompetenz import Kompetenz
        from app.models.listening_content import ListeningContent
        from app.models.mock_exam_level import MockExamLevel
        from app.models.mock_question import MockQuestion
        from app.models.mock_question_option import MockQuestionOption
        from app.models.model_test import ModelTest
        from app.models.reading_content import ReadingContent
        from app.models.speaking_task import SpeakingTask
        from app.models.teil import Teil
        from app.models.user import User
        from app.models.writing_task import WritingTask
        from app.services.mock_exam import multilevel_service as ml

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine, expire_on_commit=False)
        tag = uuid.uuid4().hex[:6]
        db = cls.Session()
        cls.audit_before = set(db.scalars(select(AuditLog.id)))
        users = []
        for name, role in (("s", "STUDENT"), ("e", "CONTENT_MANAGER")):
            u = User(email=f"mlo-{name}-{tag}@test.local", username=f"mlo_{name}_{tag}", password_hash="x", is_active=True, is_verified=True,
                     is_superuser=False, role=role, is_banned=False, preferred_language="uz", premium_until=None)
            db.add(u)
            users.append(u)
        provider = db.scalar(select(CertificationProvider).where(CertificationProvider.code == ml.PROVIDER_CODE))
        cls.own_provider = provider is None
        if provider is None:
            provider = CertificationProvider(name="National (test)", code=ml.PROVIDER_CODE, is_active=True)
            db.add(provider)
            db.flush()
        level = MockExamLevel(provider_id=provider.id, level="B1–C1", title=ml.LEVEL_TITLE, is_active=True)
        db.add(level)
        db.flush()

        def build(number: int, lesen_keys: bool, hoeren: bool = True):
            test = ModelTest(level_id=level.id, title=f"Modelltest {number}", status="DRAFT", sort_order=number)
            db.add(test)
            db.flush()
            for i, t in enumerate(("LESEN", "HOEREN", "SCHREIBEN", "SPRECHEN"), start=1):
                k = Kompetenz(model_test_id=test.id, type=t, title=t.title(), total_points=0, duration_minutes=10, sort_order=i)
                db.add(k)
                db.flush()
                if t == "HOEREN" and not hoeren:
                    continue
                teil = Teil(kompetenz_id=k.id, title="Teil 1", points=0, sort_order=1)
                db.add(teil)
                db.flush()
                if t in ("LESEN", "HOEREN"):
                    content = ReadingContent(teil_id=teil.id, content_type="TEXT", text="Text") if t == "LESEN" else ListeningContent(teil_id=teil.id, audio_url="")
                    db.add(content)
                    db.flush()
                    keyed = lesen_keys if t == "LESEN" else True
                    for n in range(1, (3 if t == "LESEN" else 2) + 1):
                        q = MockQuestion(reading_content_id=content.id if t == "LESEN" else None, listening_content_id=content.id if t == "HOEREN" else None,
                                         question_type="SINGLE_CHOICE", question_text=f"{t[0]}{n}", points=1, sort_order=n)
                        db.add(q)
                        db.flush()
                        db.add_all([MockQuestionOption(question_id=q.id, option_text=x, is_correct=keyed and x == "b", sort_order=j)
                                    for j, x in enumerate("abc", start=1)])
                elif t == "SCHREIBEN":
                    db.add(WritingTask(teil_id=teil.id, task_text="Schreiben Sie.", word_limit=50, points=0))
                else:
                    db.add(SpeakingTask(teil_id=teil.id, task_text="Sprechen Sie."))
                db.flush()
            return test

        # 1–6: no Lesen keys (like the PDFs), Hören keys, no audio; 3 is incomplete (no Hören Teil); 7: the same content, but not open
        tests = {n: build(n, lesen_keys=False, hoeren=n != 3) for n in range(1, 8)}
        now = datetime.now(timezone.utc)
        # Variant 1 is stored decomposed ("o" + U+0308), as the production upload from 2026-11-18 is
        names = {1: unicodedata.normalize("NFD", "Variant 1 Hören..m4a"), 2: "Variant 2 Hören..m4a"}
        audio = [AudioFile(storage_path=f"mlo-{tag}-{v}.m4a", kind="ORIGINAL", original_name=names[v], content_type="audio/mp4",
                           size_bytes=1000, duration_ms=2_130_000, sha256="0" * 64, created_at=now) for v in (1, 2)]
        db.add_all(audio)
        db.commit()
        cls.user_ids = [u.id for u in users]
        cls.level_id, cls.provider_id = level.id, provider.id
        cls.tid = {n: t.id for n, t in tests.items()}
        cls.audio_ids = [a.id for a in audio]
        db.close()

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete, select

        from app.models.audio_file import AudioFile
        from app.models.audit_log import AuditLog
        from app.models.certification_provider import CertificationProvider
        from app.models.kompetenz import Kompetenz
        from app.models.mock_exam_level import MockExamLevel
        from app.models.user import User

        with cls.Session() as db:
            db.execute(Kompetenz.__table__.update().where(Kompetenz.audio_file_id.in_(cls.audio_ids)).values(audio_file_id=None))
            db.execute(delete(MockExamLevel).where(MockExamLevel.id == cls.level_id))
            if cls.own_provider:
                db.execute(delete(CertificationProvider).where(CertificationProvider.id == cls.provider_id))
            db.execute(delete(AudioFile).where(AudioFile.id.in_(cls.audio_ids)))
            new = set(db.scalars(select(AuditLog.id))) - cls.audit_before
            if new:
                db.execute(delete(AuditLog).where(AuditLog.id.in_(new)))
            db.execute(delete(User).where(User.id.in_(cls.user_ids)))
            db.commit()
        cls.engine.dispose()

    def users(self, db):
        from app.models.user import User

        db.info.clear()
        return [db.get(User, i) for i in self.user_ids]

    def test_1_guard_and_access(self):
        from app.models.model_test import ModelTest
        from app.services.mock_exam import multilevel_service as ml
        from app.services.vizu_pay.access import can_access_model_test

        with self.Session() as db:
            r1 = ml.readiness(db, self.tid[1])
            self.assertEqual((r1["ready"], r1["warn_only"], r1["publishable"]), (False, True, True))
            self.assertEqual(r1["missing_audio"], [ml.SHARED_AUDIO_MISSING])
            self.assertEqual(len(r1["missing_keys"]), 3)
            ml.assert_publishable(db, self.tid[1])  # warnings only
            with self.assertRaises(HTTPException) as ctx:  # an incomplete open test is still refused
                ml.assert_publishable(db, self.tid[3])
            self.assertIn("unvollständig", ctx.exception.detail)
            self.assertNotIn("ohne Lösung", ctx.exception.detail)
            with self.assertRaises(HTTPException) as ctx:  # 7–10: the full rule
                ml.assert_publishable(db, self.tid[7])
            self.assertIn("ohne Lösung", ctx.exception.detail)
            self.assertFalse(ml.readiness(db, self.tid[7])["warn_only"])

            # access (owner, 2026-11-19): every Modelltest 1–10 needs the Multilevel Premium — the lenient publish rule does not open a test
            student, staff = self.users(db)
            for n in range(1, 8):
                self.assertFalse(can_access_model_test(db.get(ModelTest, self.tid[n]), student), n)
                self.assertTrue(can_access_model_test(db.get(ModelTest, self.tid[n]), staff), n)
            self.assertFalse(can_access_model_test(db.get(ModelTest, self.tid[1]), None))
            self.assertEqual(ml.FREE_TEST_NUMBERS, frozenset())

            from app.models.user_entitlement import PRODUCT_MULTILEVEL_PREMIUM, UserEntitlement
            from app.services.vizu_pay import multilevel_premium

            db.add(UserEntitlement(user_id=student.id, product=PRODUCT_MULTILEVEL_PREMIUM, source="PAYMENT", granted_at=datetime.now(timezone.utc)))
            db.flush()
            student, _ = self.users(db)  # fresh access cache
            for n in range(1, 8):
                self.assertTrue(can_access_model_test(db.get(ModelTest, self.tid[n]), student), n)
            overview = multilevel_premium.tests_overview(db)
            self.assertEqual(overview["free"], 0)
            self.assertEqual(overview["premium_total"], overview["total"])
            db.rollback()

    def test_2_script_plan_and_apply(self):
        from sqlalchemy import select

        from app.models.audit_log import AuditLog
        from app.models.kompetenz import Kompetenz
        from app.models.model_test import ModelTest
        from app.scripts import multilevel_open_tests as script

        with self.Session() as db:
            plan = script.build_plan(db)
            mine = {i["number"]: i for i in plan["items"] if i["model_test_id"] in {str(v) for v in self.tid.values()}}
            self.assertEqual({n: i["action"] for n, i in mine.items()}, {1: "PUBLISH", 2: "PUBLISH", 3: "BLOCKED", 4: "PUBLISH", 5: "PUBLISH", 6: "PUBLISH"})
            self.assertEqual(mine[1]["keys"], {"LESEN": [0, 3], "HOEREN": [2, 2]})
            audio = {a["audio_id"]: a for a in plan["audio"] if a["audio_id"] in {str(v) for v in self.audio_ids}}
            self.assertEqual(audio[str(self.audio_ids[0])]["action"], "LINK_SHARED")  # Variant 1 → Modelltest 1 (one shared audio)
            self.assertEqual(audio[str(self.audio_ids[1])]["action"], "MANUAL")  # Variant 2 → per-Teil test: not cut / linked
            self.assertEqual(mine[1]["audio_missing"], 0)  # the link is part of the plan
            self.assertEqual(db.get(ModelTest, self.tid[1]).status, "DRAFT")  # the plan wrote nothing

            with self.assertRaises(RuntimeError):
                script.apply_plan(db, "wrongplanid0")
            self.assertEqual(db.get(ModelTest, self.tid[1]).status, "DRAFT")

            done = script.apply_plan(db, plan["plan_id"])
            self.assertIn("MT1", done["published"])
            db.expire_all()
            statuses = {n: db.get(ModelTest, t).status for n, t in self.tid.items()}
            self.assertEqual(statuses, {1: "PUBLISHED", 2: "PUBLISHED", 3: "DRAFT", 4: "PUBLISHED", 5: "PUBLISHED", 6: "PUBLISHED", 7: "DRAFT"})
            komp = db.scalar(select(Kompetenz).where(Kompetenz.model_test_id == self.tid[1], Kompetenz.type == "HOEREN"))
            self.assertEqual(komp.audio_file_id, self.audio_ids[0])
            actions = [a for (a,) in db.execute(select(AuditLog.action).where(AuditLog.details.contains(plan["plan_id"])))]
            self.assertGreaterEqual(actions.count("multilevel_open_publish"), 5)

            again = script.build_plan(db)
            mine = {i["number"]: i["action"] for i in again["items"] if i["model_test_id"] in {str(v) for v in self.tid.values()}}
            self.assertEqual(mine, {1: "KEEP", 2: "KEEP", 3: "BLOCKED", 4: "KEEP", 5: "KEEP", 6: "KEEP"})
            self.assertNotIn(str(self.audio_ids[0]), {a["audio_id"] for a in again["audio"]})  # in use now

    def test_3_scoring_without_keys_and_audio(self):
        from sqlalchemy import select

        from app.models.mock_question_answer import MockQuestionAnswer
        from app.services.mock_exam import multilevel_exam_service as exam
        from app.services.mock_exam import multilevel_keys as keys

        from app.models.user_entitlement import PRODUCT_MULTILEVEL_PREMIUM, UserEntitlement

        with self.Session() as db:
            # the student holds the Premium (needed for every Modelltest since 2026-11-19; the row goes with the user, FK CASCADE)
            db.add(UserEntitlement(user_id=self.user_ids[0], product=PRODUCT_MULTILEVEL_PREMIUM, source="PAYMENT", granted_at=datetime.now(timezone.utc)))
            db.commit()
            student, editor = self.users(db)
            listed = {e["number"]: e for e in exam.list_exams(db, student) if e["model_test_id"] in self.tid.values()}
            self.assertEqual({n: (e["available"], e["is_locked"]) for n, e in listed.items() if n <= 2}, {1: (True, False), 2: (True, False)})
            attempt = exam.start_attempt(db, student, self.tid[2])  # Modelltest 2: no audio at all — still takeable
            exam.start_section(db, student, attempt.id, "LESEN")
            for q, _ in keys._questions(db, self.tid[2], "LESEN"):
                exam.save_answer(db, student, attempt.id, "LESEN", q.id, [q.options[0].id])
            exam.submit_section(db, student, attempt.id, "LESEN")
            exam.start_section(db, student, attempt.id, "HOEREN")
            paper = exam.section_paper(db, student, attempt.id, "HOEREN")  # the Hören paper opens without any audio
            self.assertEqual(sum(len(t["questions"]) for t in paper["teile"]), 2)
            self.assertTrue(all(not t.get("audio_url") for t in paper["teile"]))
            hoeren = keys._questions(db, self.tid[2], "HOEREN")
            right = next(o for o in hoeren[0][0].options if o.is_correct)
            wrong = next(o for o in hoeren[1][0].options if not o.is_correct)
            exam.save_answer(db, student, attempt.id, "HOEREN", hoeren[0][0].id, [right.id])
            exam.save_answer(db, student, attempt.id, "HOEREN", hoeren[1][0].id, [wrong.id])
            exam.submit_section(db, student, attempt.id, "HOEREN")
            exam.finish_attempt(db, student, attempt.id)  # Schreiben / Sprechen not started: 0 each

            result = exam.results(db, student, attempt.id)
            sections = {s["type"]: s for s in result["sections"]}
            self.assertTrue(sections["LESEN"]["no_key"])
            self.assertEqual((sections["LESEN"]["score"], sections["LESEN"]["raw_max"]), (None, 0))
            self.assertEqual((sections["HOEREN"]["raw_points"], sections["HOEREN"]["raw_max"], sections["HOEREN"]["score"]), (1, 2, 38))
            self.assertFalse(sections["HOEREN"]["no_key"])
            self.assertEqual((result["total_score"], result["max_score"]), (38, 225))  # Lesen left out: 3 × 75
            self.assertNotEqual(result["result_level"], "PENDING")
            self.assertTrue(all(item["has_key"] is False for item in sections["LESEN"]["review"]))
            self.assertTrue(all(item["has_key"] for item in sections["HOEREN"]["review"]))
            lesen_answers = db.scalars(select(MockQuestionAnswer.is_correct).where(MockQuestionAnswer.attempt_id == attempt.id,
                                                                                   MockQuestionAnswer.question_id.in_([q.id for q, _ in keys._questions(db, self.tid[2], "LESEN")]))).all()
            self.assertEqual(set(lesen_answers), {None})  # neither right nor wrong

            # an admin who sets a Lesen key later: the next attempt counts it
            q0 = keys._questions(db, self.tid[2], "LESEN")[0][0]
            from app.services.mock_exam import multilevel_service as ml

            ml.set_question_key(db, q0.id, [q0.options[1].id])
            self.assertEqual(ml.readiness(db, self.tid[2])["keys_set"], 3)
            del editor

    def test_4_removing_the_audio_keeps_an_open_test_published(self):
        from app.models.model_test import ModelTest
        from app.services.mock_exam import multilevel_audio as ml_audio

        with self.Session() as db:
            _, editor = self.users(db)
            out = asyncio.run(ml_audio.detach_shared(db, self.tid[1], editor))
            self.assertFalse(out["test_unpublished"])
            self.assertEqual(db.get(ModelTest, self.tid[1]).status, "PUBLISHED")


if __name__ == "__main__":
    unittest.main()
