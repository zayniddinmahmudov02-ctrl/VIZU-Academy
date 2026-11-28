"""Multilevel exam mode (app/services/mock_exam/multilevel_exam_service.py): the owner's 0–75 bands and the configurable
overall rule (pure), 401/403 on the routes (teachers only look, the Super Admin changes scores), and against PostgreSQL
(VIZU_WB_TEST_DB_URL) the full flow: one open attempt, keys never in the paper, own attempts only, server deadline, idempotent
submit, Lesen / Hören through the Lesen table, Schreiben / Sprechen queued for the AI, Super Admin override with history,
overall rule, retake, publish guard, untimed generic endpoints blocked. AI grading itself: test_multilevel_ai_scoring."""

import io
import os
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")


class TestBands(unittest.TestCase):
    def test_scale(self):
        from app.services.mock_exam.multilevel_exam_service import scale

        self.assertEqual(scale(35, 35), 75)
        self.assertEqual(scale(0, 35), 0)
        self.assertEqual(scale(18, 35), 39)  # 38.57 → 39
        self.assertEqual(scale(99, 35), 75)  # never above 75
        self.assertIsNone(scale(3, 0))

    def test_section_levels(self):
        """Owner's bands (2026-11-28): below B1 0–37, B1 38–50, B2 51–64, C1 65–75 (configurable; 50 is B1 now)."""
        from app.services.mock_exam.multilevel_exam_service import section_level

        cases = {0: "NICHT_BESTANDEN", 37: "NICHT_BESTANDEN", 38: "B1", 49: "B1", 50: "B1", 51: "B2", 64: "B2", 65: "C1", 75: "C1"}
        for score, level in cases.items():
            self.assertEqual(section_level(score), level, score)
        self.assertEqual(section_level(50, {"bands": {"B1": 39, "B2": 50, "C1": 65}}), "B2")  # configured bands
        self.assertEqual(section_level(50, "B2"), "B1")  # the old score_50 argument no longer decides
        with self.assertRaises(ValueError):
            section_level(76)
        with self.assertRaises(ValueError):
            section_level(-1)

    def test_overall_rules(self):
        from app.services.mock_exam import multilevel_scoring as scoring
        from app.services.mock_exam.multilevel_exam_service import overall_level

        base = {"score_50": "UNGEKLAERT", "bands": scoring.DEFAULT_BANDS}
        self.assertEqual(overall_level([70, 60, None, 40], base | {"overall_rule": "AVERAGE"}), "PENDING")
        self.assertEqual(overall_level([70, 60, 55, 40], base | {"overall_rule": "UNCONFIRMED"}), "UNGEKLAERT")
        self.assertEqual(overall_level([70, 60, 55, 40], base | {"overall_rule": "AVERAGE"}), "B2")  # 56.25
        self.assertEqual(overall_level([70, 60, 55, 40], base | {"overall_rule": "LOWEST"}), "B1")
        self.assertEqual(overall_level([70, 60, 55, 30], base | {"overall_rule": "LOWEST"}), "NICHT_BESTANDEN")
        self.assertEqual(overall_level([50, 50, 50, 50], base | {"overall_rule": "AVERAGE"}), "B1")


class TestRoutesAuth(unittest.TestCase):
    def test_401_403(self):
        try:
            from fastapi.testclient import TestClient
        except Exception:  # httpx missing (server)
            self.skipTest("httpx not installed")
        from types import SimpleNamespace

        from app.api.dependencies.auth import get_current_user
        from app.main import app

        client = TestClient(app)
        a = uuid.uuid4()
        student = [("get", "/api/v1/multilevel-exam/exams"), ("get", "/api/v1/multilevel-exam/history"),
                   ("get", f"/api/v1/multilevel-exam/attempts/{a}"), ("post", f"/api/v1/multilevel-exam/attempts/{a}/finish"),
                   ("get", f"/api/v1/multilevel-exam/attempts/{a}/results")]
        staff = [("get", "/api/v1/admin/multilevel-exam/attempts"), ("get", "/api/v1/admin/multilevel-exam/statistics"),
                 ("get", f"/api/v1/admin/multilevel-exam/attempts/{a}"), ("get", f"/api/v1/admin/multilevel-exam/recordings/{a}"),
                 ("get", f"/api/v1/admin/multilevel-exam/model-tests/{a}/preview")]
        writes = [("put", f"/api/v1/admin/multilevel-exam/attempts/{a}/sections/SCHREIBEN/grade", {"score": 50, "reason": "Test"}),
                  ("post", f"/api/v1/admin/multilevel-exam/attempts/{a}/sections/SCHREIBEN/reevaluate", None),
                  ("put", "/api/v1/admin/multilevel-exam/settings", {"overall_rule": "AVERAGE"})]
        for method, url in student + staff:
            self.assertEqual(getattr(client, method)(url).status_code, 401, url)
        for method, url, body in writes:
            self.assertEqual(getattr(client, method)(url, json=body).status_code, 401, url)
        # results of all students (texts, recordings): content editors and up (2026-11-28) — a teacher sees only their groups
        # (/groups/{id}/multilevel); the test preview stays open to admin-panel roles
        results = [x for x in staff if "/preview" not in x[1]]
        for role, urls in (("STUDENT", staff), ("TEACHER", results), ("SUPPORT", results)):
            app.dependency_overrides[get_current_user] = lambda role=role: SimpleNamespace(id=uuid.uuid4(), role=role)
            try:
                for method, url in urls:
                    self.assertEqual(getattr(client, method)(url).status_code, 403, (role, url))
            finally:
                app.dependency_overrides.pop(get_current_user, None)
        # changing scores / settings / re-running the AI: SUPER_ADMIN only
        for role in ("ADMIN", "TEACHER", "CONTENT_MANAGER"):
            app.dependency_overrides[get_current_user] = lambda role=role: SimpleNamespace(id=uuid.uuid4(), role=role)
            try:
                for method, url, body in writes:
                    self.assertEqual(getattr(client, method)(url, json=body).status_code, 403, (role, url))
            finally:
                app.dependency_overrides.pop(get_current_user, None)


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestExamFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
        from app.models.app_setting import AppSetting
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
        from app.services.mock_exam import multilevel_service

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        db = cls.Session()
        if db.scalar(select(MockExamLevel).where(MockExamLevel.title == multilevel_service.LEVEL_TITLE)):
            db.close()
            raise unittest.SkipTest("the test database already holds a Multilevel level")
        cls.setting_before = db.scalar(select(AppSetting).where(AppSetting.key == "multilevel_scoring"))
        if cls.setting_before is not None:
            db.close()
            raise unittest.SkipTest("the test database already holds multilevel_scoring settings")
        tag = uuid.uuid4().hex[:6]
        users = []
        for name, role in (("a", "STUDENT"), ("b", "STUDENT"), ("t", "TEACHER"), ("s", "SUPER_ADMIN")):
            u = User(email=f"mlx-{name}-{tag}@test.local", username=f"mlx_{name}_{tag}", password_hash="x", is_active=True,
                     is_verified=True, is_superuser=role == "SUPER_ADMIN", role=role, is_banned=False, preferred_language="uz",
                     premium_until=None)
            db.add(u)
            users.append(u)
        db.flush()
        # every Multilevel Modelltest needs the Premium (2026-11-19): both students have it (the rows go with the users, FK CASCADE)
        from app.models.user_entitlement import PRODUCT_MULTILEVEL_PREMIUM, UserEntitlement

        for u in users[:2]:
            db.add(UserEntitlement(user_id=u.id, product=PRODUCT_MULTILEVEL_PREMIUM, source="PAYMENT", granted_at=datetime.now(timezone.utc)))
        provider = CertificationProvider(name=f"MLX {tag}", code=f"MLX{tag}", is_active=True)
        db.add(provider)
        db.flush()
        level = MockExamLevel(provider_id=provider.id, level="B1–C1", title=multilevel_service.LEVEL_TITLE, is_active=True)
        db.add(level)
        db.flush()

        def build(sort, hoeren=True):
            test = ModelTest(level_id=level.id, title=f"Modelltest {sort}", status="DRAFT", sort_order=sort)
            db.add(test)
            db.flush()
            ids = {}
            for i, t in enumerate(["LESEN", "HOEREN", "SCHREIBEN", "SPRECHEN"], start=1):
                k = Kompetenz(model_test_id=test.id, type=t, title=t.title(), total_points=0, duration_minutes=10, sort_order=i)
                db.add(k)
                db.flush()
                if t == "HOEREN" and not hoeren:
                    continue
                teil = Teil(kompetenz_id=k.id, title="Teil 1", points=0, sort_order=1)
                db.add(teil)
                db.flush()
                if t in ("LESEN", "HOEREN"):
                    content = (ReadingContent(teil_id=teil.id, content_type="TEXT", text="Text") if t == "LESEN"
                               else ListeningContent(teil_id=teil.id, audio_url="/uploads/audio/x.mp3"))
                    db.add(content)
                    db.flush()
                    for n in range(1, (3 if t == "LESEN" else 2) + 1):
                        q = MockQuestion(reading_content_id=content.id if t == "LESEN" else None,
                                         listening_content_id=content.id if t == "HOEREN" else None,
                                         question_type="SINGLE_CHOICE", question_text=f"A{n}", points=1, sort_order=n)
                        db.add(q)
                        db.flush()
                        opts = [MockQuestionOption(question_id=q.id, option_text=x, is_correct=x == "b", sort_order=j)
                                for j, x in enumerate("abc", start=1)]
                        db.add_all(opts)
                        db.flush()
                        ids.setdefault(t, []).append((q.id, [o.id for o in opts]))
                elif t == "SCHREIBEN":
                    w = WritingTask(teil_id=teil.id, task_text="Schreiben Sie.", word_limit=50, points=0)
                    db.add(w)
                    db.flush()
                    ids["SCHREIBEN"] = w.id
                else:
                    s = SpeakingTask(teil_id=teil.id, task_text="Sprechen Sie.")
                    db.add(s)
                    db.flush()
                    ids["SPRECHEN"] = s.id
            return test, ids

        cls.test, cls.ids = build(1)
        cls.incomplete, _ = build(2, hoeren=False)
        cls.test.status = "PUBLISHED"
        db.commit()
        cls.test_id, cls.incomplete_id = cls.test.id, cls.incomplete.id
        cls.user_ids = [u.id for u in users]
        cls.provider_id = provider.id
        db.close()
        cls.tmp = tempfile.TemporaryDirectory()
        from app.services.mock_exam import multilevel_exam_service as svc

        cls.patch = patch.object(type(svc.speaking_storage), "ROOT", Path(cls.tmp.name))
        cls.patch.start()

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete

        from app.models.app_setting import AppSetting
        from app.models.audit_log import AuditLog
        from app.models.certification_provider import CertificationProvider
        from app.models.user import User

        with cls.Session() as db:
            db.execute(delete(AppSetting).where(AppSetting.key == "multilevel_scoring"))
            db.execute(delete(CertificationProvider).where(CertificationProvider.id == cls.provider_id))
            db.execute(delete(AuditLog).where(AuditLog.actor_id.in_(cls.user_ids)))
            db.execute(delete(AuditLog).where(AuditLog.target_user_id.in_(cls.user_ids)))
            db.execute(delete(User).where(User.id.in_(cls.user_ids)))
            db.commit()
        cls.patch.stop()
        cls.tmp.cleanup()
        cls.engine.dispose()

    def _users(self, db):
        from app.models.user import User

        return [db.get(User, i) for i in self.user_ids]

    def test_full_flow(self):
        from starlette.datastructures import Headers, UploadFile

        from app.models.mock_attempt_section import MockAttemptSection
        from app.models.model_test import ModelTest
        from app.services.mock_exam import multilevel_exam_service as svc
        from app.services.mock_exam import multilevel_service

        with self.Session() as db:
            a, b, teacher, sadmin = self._users(db)
            exams = {e["model_test_id"]: e for e in svc.list_exams(db, a)}
            # every Modelltest is shown; the incomplete draft as "Tayyorlanmoqda" (not startable, no content)
            self.assertEqual((exams[self.test_id]["available"], exams[self.incomplete_id]["available"]), (True, False))
            self.assertEqual(exams[self.incomplete_id]["state"], "PREPARING")
            # every Modelltest needs the Multilevel Premium (2026-11-19; the fixture grants it to "a" — the locks are tested in test_multilevel_premium)
            self.assertFalse(any(e["is_locked"] for e in exams.values()))
            self.assertFalse(any(e["is_locked"] for e in svc.list_exams(db, sadmin)))  # staff review without buying
            att = svc.start_attempt(db, a, self.test_id)
            self.assertEqual(svc.start_attempt(db, a, self.test_id).id, att.id)  # one open attempt
            with self.assertRaises(HTTPException) as c:
                svc.results(db, a, att.id)
            self.assertEqual(c.exception.status_code, 409)
            with self.assertRaises(HTTPException) as c:
                svc.attempt_view(db, b, att.id)  # someone else's attempt
            self.assertEqual(c.exception.status_code, 404)

            svc.start_section(db, a, att.id, "LESEN")
            with self.assertRaises(HTTPException) as c:
                svc.start_section(db, a, att.id, "HOEREN")  # one section at a time
            self.assertEqual(c.exception.detail, "OTHER_SECTION_OPEN")
            paper = svc.section_paper(db, a, att.id, "LESEN")
            self.assertNotIn("is_correct", str(paper))
            (q1, o1), (q2, o2), (q3, o3) = self.ids["LESEN"]
            with self.assertRaises(HTTPException):
                svc.save_answer(db, a, att.id, "LESEN", q1, [o2[0]])  # option of another question
            with self.assertRaises(HTTPException):
                svc.save_answer(db, a, att.id, "LESEN", q1, o1[:2])  # single choice
            with self.assertRaises(HTTPException):
                svc.save_answer(db, b, att.id, "LESEN", q1, [o1[1]])
            svc.save_answer(db, a, att.id, "LESEN", q1, [o1[0]])
            svc.save_answer(db, a, att.id, "LESEN", q1, [o1[1]])  # changed → correct
            svc.save_answer(db, a, att.id, "LESEN", q2, [o2[1]])
            svc.save_answer(db, a, att.id, "LESEN", q3, [o3[2]])  # wrong
            self.assertEqual(svc.section_paper(db, a, att.id, "LESEN")["answers"][str(q1)], [str(o1[1])])
            svc.submit_section(db, a, att.id, "LESEN")
            svc.submit_section(db, a, att.id, "LESEN")  # idempotent
            sec = db.query(MockAttemptSection).filter_by(attempt_id=att.id, section_type="LESEN").one()
            db.refresh(sec)
            # 2 of 3 → 23.3 → 23 on the 35 scale → the Lesen table (B2 band 18–27 → 51–64): 58
            self.assertEqual((sec.raw_points, sec.raw_max, sec.score, sec.level, sec.score_source), (2, 3, 58, "B2", "AUTO"))
            with self.assertRaises(HTTPException) as c:
                svc.save_answer(db, a, att.id, "LESEN", q3, [o3[1]])
            self.assertEqual(c.exception.detail, "SECTION_CLOSED")

            # Hören: the deadline passes on the server → answers are refused, section closes and is graded
            svc.start_section(db, a, att.id, "HOEREN")
            (h1, ho1), (h2, ho2) = self.ids["HOEREN"]
            svc.save_answer(db, a, att.id, "HOEREN", h1, [ho1[1]])
            hs = db.query(MockAttemptSection).filter_by(attempt_id=att.id, section_type="HOEREN").one()
            hs.deadline_at = hs.deadline_at - timedelta(minutes=11)
            hs.started_at = hs.started_at - timedelta(minutes=11)
            db.commit()
            with self.assertRaises(HTTPException) as c:
                svc.save_answer(db, a, att.id, "HOEREN", h2, [ho2[1]])
            self.assertEqual(c.exception.detail, "SECTION_CLOSED")
            db.refresh(hs)
            self.assertEqual((hs.status, hs.score), ("EXPIRED", 51))  # 1/2 → 17.5 → 18 on the 35 scale → 51

            svc.start_section(db, a, att.id, "SCHREIBEN")
            svc.save_writing(db, a, att.id, self.ids["SCHREIBEN"], "Ich schreibe einen Brief.")
            svc.save_writing(db, a, att.id, self.ids["SCHREIBEN"], "Ich schreibe einen langen Brief.")
            svc.submit_section(db, a, att.id, "SCHREIBEN")

            svc.start_section(db, a, att.id, "SPRECHEN")
            webm = b"\x1aE\xdf\xa3" + b"\0" * 2048
            with self.assertRaises(HTTPException) as c:  # declared type ≠ content
                import asyncio

                asyncio.run(svc.upload_recording(db, a, att.id, self.ids["SPRECHEN"],
                                                 UploadFile(io.BytesIO(webm), headers=Headers({"content-type": "audio/mpeg"}))))
            self.assertEqual(c.exception.status_code, 415)
            asyncio.run(svc.upload_recording(db, a, att.id, self.ids["SPRECHEN"],
                                             UploadFile(io.BytesIO(webm), headers=Headers({"content-type": "audio/webm;codecs=opus"}))))
            svc.finish_attempt(db, a, att.id)
            svc.finish_attempt(db, a, att.id)  # idempotent

            res = svc.results(db, a, att.id)
            self.assertEqual(res["status"], "SUBMITTED")
            self.assertEqual(res["result_level"], "PENDING")
            by = {s["type"]: s for s in res["sections"]}
            self.assertTrue(by["SCHREIBEN"]["awaiting_grading"] and by["SPRECHEN"]["awaiting_grading"])
            self.assertEqual((by["SCHREIBEN"]["ai_status"], by["SPRECHEN"]["ai_status"]), ("PENDING", "PENDING"))  # queued for the AI
            self.assertTrue(by["LESEN"]["review"][0]["correct"])  # keys only after the exam

            detail = svc.admin_attempt_detail(db, att.id)
            self.assertEqual(detail["writings"][0]["answer_text"], "Ich schreibe einen langen Brief.")
            path, media = svc.recording_file(db, teacher, detail["recordings"][0]["submission_id"], staff=True)
            self.assertTrue(path.is_file() and media == "audio/webm")
            with self.assertRaises(HTTPException):
                svc.recording_file(db, b, detail["recordings"][0]["submission_id"], staff=False)
            with self.assertRaises(HTTPException) as c:
                svc.override_section(db, sadmin, att.id, "SCHREIBEN", 76, "zu viel")
            self.assertEqual(c.exception.detail, "SCORE_OUT_OF_RANGE")
            with self.assertRaises(HTTPException) as c:
                svc.override_section(db, sadmin, att.id, "SCHREIBEN", 66, " ")
            self.assertEqual(c.exception.detail, "REASON_REQUIRED")
            svc.override_section(db, sadmin, att.id, "SCHREIBEN", 66, "Handbewertung", "gut")
            svc.override_section(db, sadmin, att.id, "SPRECHEN", 60, "Handbewertung")
            res = svc.results(db, a, att.id)
            self.assertEqual((res["status"], res["total_score"], res["max_score"]), ("GRADED", 58 + 51 + 66 + 60, 300))
            self.assertEqual(res["result_level"], "UNGEKLAERT")  # no overall rule confirmed yet
            hist = {s["type"]: s["history"] for s in svc.admin_attempt_detail(db, att.id)["sections"]}
            self.assertEqual((hist["SCHREIBEN"][0]["old_score"], hist["SCHREIBEN"][0]["new_score"], hist["SCHREIBEN"][0]["reason"]),
                             (None, 66, "Handbewertung"))

            out = svc.update_settings(db, sadmin, overall_rule="AVERAGE")
            self.assertEqual(out["results_changed"], 1)
            res = svc.results(db, a, att.id)
            self.assertEqual(res["result_level"], "B2")  # avg 58.75 → 59
            self.assertEqual({s["type"]: s["level"] for s in res["sections"]}["LESEN"], "B2")

            again = svc.start_attempt(db, a, self.test_id)  # retake
            self.assertNotEqual(again.id, att.id)
            self.assertEqual(len(svc.history(db, a)), 2)
            stats = svc.statistics(db)
            self.assertEqual(stats["attempts"], 2)

            # publish guard: Hören without Teile → not a complete exam
            with self.assertRaises(HTTPException) as c:
                multilevel_service.assert_publishable(db, self.incomplete_id)
            self.assertIn("HOEREN", c.exception.detail)
            self.assertTrue(svc.is_multilevel_test(db, db.get(ModelTest, self.test_id)))
            preview = svc.admin_preview(db, self.incomplete_id)
            self.assertIn("HOEREN: keine Teile", preview["gaps"])


if __name__ == "__main__":
    unittest.main()
