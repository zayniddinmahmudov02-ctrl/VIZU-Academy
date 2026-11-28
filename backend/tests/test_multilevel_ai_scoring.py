"""Multilevel AI grading + Super Admin overrides (multilevel_ai.py, multilevel_exam_service.py; owner 2026-11-28). The AI is mocked — no
network. Pure: Schreiben Teil scores (0.5 steps, ranges, literal mistakes, empty Teil = 0), Sprechen criteria (integers 0–5, Aussprache /
Flüssigkeit only when the audio was heard, an unrecorded Teil counts its full maximum). Against PostgreSQL (VIZU_WB_TEST_DB_URL): close →
PENDING → worker → table conversion + ai_evaluations row + GRADED + notification; override wins and survives a re-run; clear; failure is
kept and retried; a raw score in the unreadable table range waits for the admin until the table is completed; rescore script for old rows."""

import asyncio
import io
import json
import os
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from app.services.mock_exam import multilevel_ai as ai

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")

W_PARTS = [{"key": "1.1", "title": "Teil 1.1", "max": 5.0, "task": "E-Mail an Freund", "word_limit": 50, "answer": "Ich habe keine Zeit, weil ich arbeite."},
           {"key": "1.2", "title": "Teil 1.2", "max": 7.0, "task": "Beschwerde", "word_limit": 80, "answer": "Sehr geehrte Damen und Herren, ich bin unzufrieden."},
           {"key": "2", "title": "Teil 2", "max": 24.0, "task": "Forumsbeitrag", "word_limit": 200, "answer": ""}]


def w_result(s11, s12, s2=None):
    teile = [{"teil": "1.1", "score": s11, "explanation": "gut", "criteria": [{"name": "Grammatik", "comment": "ok"}],
              "mistakes": [{"original": "weil ich arbeite", "correction": "weil ich arbeiten muss", "explanation": "Modalverb"},
                           {"original": "steht nicht im Text", "correction": "x", "explanation": "erfunden"}],
              "strengths": ["klar"], "recommendations": ["mehr Konnektoren"]},
             {"teil": "Teil 1.2", "score": s12, "explanation": "ok"}]
    if s2 is not None:
        teile.append({"teil": "2", "score": s2, "explanation": "Argumente"})
    return {"teile": teile, "summary": "Zusammenfassung", "strengths": ["a"], "mistakes": ["b"], "recommendations": ["c"]}


class TestValidation(unittest.TestCase):
    def test_schreiben(self):
        out = ai.validate_schreiben(w_result(4.3, 6), W_PARTS)
        teile = {t["teil"]: t for t in out["teile"]}
        self.assertEqual((teile["1.1"]["score"], teile["1.2"]["score"], teile["2"]["score"]), (4.5, 6.0, 0.0))  # 4.3 → 4.5; Teil 2 empty → 0
        self.assertEqual((out["raw"], out["raw_max"]), (10.5, 36.0))
        self.assertEqual([m["original"] for m in teile["1.1"]["mistakes"]], ["weil ich arbeite"])  # only quotes that are in the text
        self.assertFalse(teile["2"]["answered"])
        for bad in (w_result(5.5, 6), w_result(4, -1), {"teile": [{"teil": "1.1", "score": 3}]}, {"teile": [{"teil": "1.1", "score": "3"}, {"teil": "1.2", "score": 2}]}, []):
            with self.subTest(bad=str(bad)[:60]), self.assertRaises(ai.InvalidAIResult):
                ai.validate_schreiben(bad, W_PARTS)

    def test_sprechen(self):
        parts = [{"key": "Teil 1", "title": "Teil 1", "submission": object(), "transcript": "Ich wohne in Taschkent.",
                  "observations": {"pronunciation": "klar", "fluency": "flüssig"}},
                 {"key": "Teil 2", "title": "Teil 2", "submission": object(), "transcript": "Ich mag Sport.", "observations": None},
                 {"key": "Teil 3", "title": "Teil 3", "submission": None, "transcript": "", "observations": None}]
        crit = lambda score: [{"key": k, "score": score, "comment": "c"} for k, _ in ai.scoring.SPRECHEN_CRITERIA]  # noqa: E731
        raw = {"teile": [{"teil": "Teil 1", "criteria": crit(4)}, {"teil": "teil 2", "criteria": crit(5),
                                                                    "mistakes": [{"original": "mag Sport", "correction": "mag den Sport"}]}]}
        out = ai.validate_sprechen(raw, parts)
        t1, t2, t3 = out["teile"]
        self.assertEqual((t1["score"], t1["max"]), (24, 30))  # heard: all six criteria
        self.assertEqual((t2["score"], t2["max"]), (20, 20))  # not heard: Aussprache + Flüssigkeit left out
        self.assertEqual({c["key"] for c in t2["criteria"] if c["status"] == "not_assessed"}, {"aussprache", "fluessigkeit"})
        self.assertEqual((t3["score"], t3["max"]), (0, 30))  # nothing recorded: 0 of the full maximum
        self.assertEqual((out["raw"], out["raw_max"]), (44.0, 80.0))
        self.assertTrue(out["limitations"])
        bad = {"teile": [{"teil": "Teil 1", "criteria": crit(4.5)}, {"teil": "Teil 2", "criteria": crit(5)}]}
        with self.assertRaises(ai.InvalidAIResult):
            ai.validate_sprechen(bad, parts)


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestAiFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
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
        from app.models.user_entitlement import PRODUCT_MULTILEVEL_PREMIUM, UserEntitlement
        from app.models.writing_task import WritingTask
        from app.services.mock_exam import multilevel_service

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        db = cls.Session()
        if db.scalar(select(MockExamLevel).where(MockExamLevel.title == multilevel_service.LEVEL_TITLE)):
            db.close()
            raise unittest.SkipTest("the test database already holds a Multilevel level")
        tag = uuid.uuid4().hex[:6]
        users = {}
        for name, role in (("st", "STUDENT"), ("sa", "SUPER_ADMIN"), ("tc", "TEACHER")):
            users[name] = User(email=f"mla-{name}-{tag}@test.local", username=f"mla_{name}_{tag}", password_hash="x", is_active=True,
                               is_verified=True, is_superuser=role == "SUPER_ADMIN", role=role, is_banned=False, preferred_language="uz")
            db.add(users[name])
        db.flush()
        db.add(UserEntitlement(user_id=users["st"].id, product=PRODUCT_MULTILEVEL_PREMIUM, source="PAYMENT", granted_at=datetime.now(timezone.utc)))
        provider = CertificationProvider(name=f"MLA {tag}", code=f"MLA{tag}", is_active=True)
        db.add(provider)
        db.flush()
        level = MockExamLevel(provider_id=provider.id, level="B1–C1", title=multilevel_service.LEVEL_TITLE, is_active=True)
        db.add(level)
        db.flush()
        test = ModelTest(level_id=level.id, title="Modelltest AI", status="PUBLISHED", sort_order=1)
        db.add(test)
        db.flush()
        cls.ids = {"writing": {}, "speaking": None, "q": {}}
        for i, kind in enumerate(["LESEN", "HOEREN", "SCHREIBEN", "SPRECHEN"], start=1):
            k = Kompetenz(model_test_id=test.id, type=kind, title=kind.title(), total_points=0, duration_minutes=10, sort_order=i)
            db.add(k)
            db.flush()
            titles = ["Teil 1.1", "Teil 1.2", "Teil 2"] if kind == "SCHREIBEN" else ["Teil 1"]
            for n, title in enumerate(titles, start=1):
                teil = Teil(kompetenz_id=k.id, title=title, points=0, sort_order=n)
                db.add(teil)
                db.flush()
                if kind in ("LESEN", "HOEREN"):
                    content = (ReadingContent(teil_id=teil.id, content_type="TEXT", text="Text") if kind == "LESEN"
                               else ListeningContent(teil_id=teil.id, audio_url="/uploads/audio/x.mp3"))
                    db.add(content)
                    db.flush()
                    q = MockQuestion(reading_content_id=content.id if kind == "LESEN" else None, listening_content_id=content.id if kind == "HOEREN" else None,
                                     question_type="SINGLE_CHOICE", question_text="F", points=1, sort_order=1)
                    db.add(q)
                    db.flush()
                    opts = [MockQuestionOption(question_id=q.id, option_text=x, is_correct=x == "b", sort_order=j) for j, x in enumerate("ab", start=1)]
                    db.add_all(opts)
                    db.flush()
                    cls.ids["q"][kind] = (q.id, opts[1].id)
                elif kind == "SCHREIBEN":
                    w = WritingTask(teil_id=teil.id, task_text=f"Aufgabe {title}", word_limit=60, points=0)
                    db.add(w)
                    db.flush()
                    cls.ids["writing"][title] = w.id
                else:
                    sp = SpeakingTask(teil_id=teil.id, task_text="Stellen Sie sich vor.")
                    db.add(sp)
                    db.flush()
                    cls.ids["speaking"] = sp.id
        db.commit()
        cls.test_id, cls.provider_id = test.id, provider.id
        cls.user_ids = {k: u.id for k, u in users.items()}
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
        from app.models.lesson_skill import AiEvaluation
        from app.models.user import User

        from app.models.study_group import StudyGroup

        ids = list(cls.user_ids.values())
        with cls.Session() as db:
            db.execute(delete(StudyGroup).where(StudyGroup.teacher_id.in_(ids)))
            db.execute(delete(AiEvaluation).where(AiEvaluation.kind == "ML_SECTION", AiEvaluation.user_id.in_(ids)))
            db.execute(delete(AppSetting).where(AppSetting.key == "multilevel_scoring"))
            db.execute(delete(CertificationProvider).where(CertificationProvider.id == cls.provider_id))
            db.execute(delete(AuditLog).where(AuditLog.actor_id.in_([str(i) for i in ids])))
            db.execute(delete(AuditLog).where(AuditLog.target_user_id.in_([str(i) for i in ids])))
            db.execute(delete(AuditLog).where(AuditLog.action == "multilevel_rescore_script"))
            db.execute(delete(User).where(User.id.in_(ids)))
            db.commit()
        cls.patch.stop()
        cls.tmp.cleanup()
        cls.engine.dispose()

    def user(self, db, name):
        from app.models.user import User

        db.info.clear()
        return db.get(User, self.user_ids[name])

    def section(self, db, attempt_id, kind):
        from app.models.mock_attempt_section import MockAttemptSection

        db.expire_all()
        return db.query(MockAttemptSection).filter_by(attempt_id=attempt_id, section_type=kind).one()

    def exam_until_ai(self, db, texts=("Ich habe keine Zeit, weil ich arbeite.", "", "Meiner Meinung nach ist das wichtig.")):
        from starlette.datastructures import Headers, UploadFile

        from app.services.mock_exam import multilevel_exam_service as svc

        st = self.user(db, "st")
        att = svc.start_attempt(db, st, self.test_id)
        for kind in ("LESEN", "HOEREN"):
            svc.start_section(db, st, att.id, kind)
            q, right = self.ids["q"][kind]
            svc.save_answer(db, st, att.id, kind, q, [right])
            svc.submit_section(db, st, att.id, kind)
        svc.start_section(db, st, att.id, "SCHREIBEN")
        for title, value in zip(("Teil 1.1", "Teil 1.2", "Teil 2"), texts):
            svc.save_writing(db, st, att.id, self.ids["writing"][title], value)
        svc.submit_section(db, st, att.id, "SCHREIBEN")
        svc.start_section(db, st, att.id, "SPRECHEN")
        asyncio.run(svc.upload_recording(db, st, att.id, self.ids["speaking"],
                                         UploadFile(io.BytesIO(b"\x1aE\xdf\xa3" + b"\0" * 2048), headers=Headers({"content-type": "audio/webm"}))))
        svc.submit_section(db, st, att.id, "SPRECHEN")
        return att.id

    @staticmethod
    def fake_ai(schreiben: dict, sprechen_score: int = 4):
        def call(prompt):
            if "Schreiben" in prompt:
                return schreiben, "test-model"
            crit = [{"key": k, "score": sprechen_score, "comment": "c"} for k, _ in ai.scoring.SPRECHEN_CRITERIA]
            return {"teile": [{"teil": "Teil 1", "criteria": crit, "strengths": ["s"]}], "summary": "gut"}, "test-model"
        return call

    @staticmethod
    def fake_stt(parts):
        for p in parts:
            p["transcript"], p["observations"] = ("Ich heiße Ali.", {"pronunciation": "deutlich", "fluency": "ruhig"}) if p["submission"] else ("", None)

    def test_full_ai_flow_override_rerun_failure(self):
        from sqlalchemy import select

        from app.models.lesson_skill import AiEvaluation
        from app.models.mock_test_attempt import MockTestAttempt
        from app.models.notification import Notification
        from app.services.mock_exam import multilevel_exam_service as svc

        with self.Session() as db:
            aid = self.exam_until_ai(db)
            self.assertEqual((self.section(db, aid, "SCHREIBEN").ai_status, self.section(db, aid, "SPRECHEN").ai_status), ("PENDING", "PENDING"))
            # Teil 1.1 4.5 + 1.2 0 (empty, not asked) + Teil 2 20 = 24.5 → 58 in the official table (24.1–24.5); Sprechen 24 / 30 → 60
            with patch.object(ai, "_call", self.fake_ai({"teile": [{"teil": "1.1", "score": 4.5}, {"teil": "2", "score": 20}]})), \
                    patch.object(ai, "_transcribe", self.fake_stt):
                self.assertGreaterEqual(ai.tick(db), 2)
            w, sp = self.section(db, aid, "SCHREIBEN"), self.section(db, aid, "SPRECHEN")
            self.assertEqual((w.ai_raw, w.auto_score, w.score, w.score_source, w.ai_status, w.ai_runs), (24.5, 58, 58, "AI", "DONE", 1))
            self.assertEqual((sp.ai_raw, sp.ai_raw_max, sp.score, sp.score_source), (24.0, 30.0, 60, "AI"))
            attempt = db.get(MockTestAttempt, aid)
            self.assertEqual((attempt.status, attempt.total_score), ("GRADED", 75 + 75 + 58 + 60))
            self.assertTrue(db.scalar(select(Notification).where(Notification.user_id == self.user_ids["st"],
                                                                 Notification.link_path == f"/vorbereitung/multilevel/ergebnis/{aid}")))
            res = svc.results(db, self.user(db, "st"), aid)
            ev = {s["type"]: s for s in res["sections"]}["SCHREIBEN"]["evaluation"]
            self.assertEqual((ev["raw"], ev["converted"], len(ev["teile"])), (24.5, 58, 3))
            self.assertNotIn("model", ev)

            # Super Admin override: wins, kept through an AI re-run, cleared again
            sa = self.user(db, "sa")
            svc.override_section(db, sa, aid, "SCHREIBEN", 70, "Prüfer-Korrektur")
            self.assertEqual((self.section(db, aid, "SCHREIBEN").score, self.section(db, aid, "SCHREIBEN").score_source), (70, "MANUAL"))
            svc.request_reevaluation(db, sa, aid, "SCHREIBEN")
            with patch.object(ai, "_call", self.fake_ai({"teile": [{"teil": "1.1", "score": 5}, {"teil": "2", "score": 22}]})):
                self.assertGreaterEqual(ai.tick(db), 1)
            w = self.section(db, aid, "SCHREIBEN")
            self.assertEqual((w.auto_score, w.score, w.score_source, w.ai_runs), (63, 70, "MANUAL", 2))  # 27.0 → 63, the override stays
            svc.override_section(db, sa, aid, "SCHREIBEN", None, "Korrektur zurückgenommen")
            w = self.section(db, aid, "SCHREIBEN")
            self.assertEqual((w.score, w.score_source, w.override_score), (w.auto_score, "AI", None))

            # a failing AI run is kept, nothing else changes, it is retried later
            svc.request_reevaluation(db, sa, aid, "SCHREIBEN")
            with patch.object(ai, "_call", side_effect=RuntimeError("network down")):
                ai.tick(db)
            w = self.section(db, aid, "SCHREIBEN")
            self.assertEqual((w.ai_status, w.score, w.ai_runs), ("FAILED", w.auto_score, 3))
            history = svc.admin_attempt_detail(db, aid)
            hist = {s["type"]: s["history"] for s in history["sections"]}["SCHREIBEN"]
            self.assertEqual([h["source"] + "/" + h["status"] for h in hist],
                             ["AI/FAILED", "MANUAL_OVERRIDE/SUCCEEDED", "AI/SUCCEEDED", "MANUAL_OVERRIDE/SUCCEEDED", "AI/SUCCEEDED"])
            self.assertEqual((hist[3]["old_score"], hist[3]["new_score"], hist[3]["reason"], hist[3]["actor"]), (58, 70, "Prüfer-Korrektur", sa.username))
            rows = db.scalars(select(AiEvaluation).where(AiEvaluation.kind == "ML_SECTION")).all()
            self.assertTrue(all(r.user_id == self.user_ids["st"] for r in rows))

    def test_raw_in_the_unreadable_range_waits_for_the_admin(self):
        from app.models.mock_test_attempt import MockTestAttempt
        from app.services.mock_exam import multilevel_exam_service as svc

        with self.Session() as db:
            aid = self.exam_until_ai(db)
            # 1.1 3 + 2 16 = 19.0 → the table has no row for 16.6–22.0
            with patch.object(ai, "_call", self.fake_ai({"teile": [{"teil": "1.1", "score": 3}, {"teil": "2", "score": 16}]})), \
                    patch.object(ai, "_transcribe", self.fake_stt):
                ai.tick(db)
            w = self.section(db, aid, "SCHREIBEN")
            self.assertEqual((w.ai_raw, w.auto_score, w.score, w.ai_status), (19.0, None, None, "NEEDS_ADMIN"))
            self.assertEqual(db.get(MockTestAttempt, aid).result_level, "PENDING")
            detail = svc.admin_attempt_detail(db, aid)
            self.assertTrue({s["type"]: s for s in detail["sections"]}["SCHREIBEN"]["conversion_missing"])
            # the Super Admin completes the table → the stored raw score is converted, nothing else is asked from the AI
            rows = svc.get_settings(db)["schreiben_table"] + [[18.6, 19.0, 46]]
            out = svc.update_settings(db, self.user(db, "sa"), schreiben_table=rows)
            self.assertGreaterEqual(out["results_changed"], 1)
            self.assertIn([17.0, 18.5], out["schreiben_missing"])
            w = self.section(db, aid, "SCHREIBEN")
            self.assertEqual((w.score, w.ai_status, w.score_source), (46, "DONE", "AI"))
            self.assertEqual(db.get(MockTestAttempt, aid).status, "GRADED")
            svc.update_settings(db, self.user(db, "sa"), schreiben_table=[list(r) for r in svc.scoring.DEFAULT_SCHREIBEN_TABLE])

    def test_group_teacher_sees_ai_result_and_hears_only_members(self):
        from fastapi import HTTPException
        from sqlalchemy import select

        from app.models.model_test import ModelTest
        from app.models.study_group import StudyGroup, StudyGroupMember
        from app.services.mock_exam import multilevel_exam_service as svc
        from app.services.study_groups import multilevel

        with self.Session() as db:
            aid = self.exam_until_ai(db)
            with patch.object(ai, "_call", self.fake_ai({"teile": [{"teil": "1.1", "score": 4}, {"teil": "2", "score": 18}]})), \
                    patch.object(ai, "_transcribe", self.fake_stt):
                ai.tick(db)
            level_id = db.get(ModelTest, self.test_id).level_id
            now = datetime.now(timezone.utc)
            groups = []
            for members in ((self.user_ids["st"],), ()):
                g = StudyGroup(name=f"ML AI {uuid.uuid4().hex[:4]}", level="C1", teacher_id=self.user_ids["tc"], status="active", mock_exam_level_id=level_id)
                db.add(g)
                db.flush()
                for uid in members:
                    db.add(StudyGroupMember(group_id=g.id, user_id=uid, role="student", status="active", joined_at=now))
                groups.append(g)
            db.commit()
            mine, other = groups
            detail = multilevel.student_detail(db, mine, self.user_ids["st"])
            attempt = next(a for t in detail["tests"] for a in t["attempts"] if a["attempt_id"] == aid)
            self.assertEqual(attempt["sections"]["SCHREIBEN"]["evaluation"]["raw"], 22.0)  # the AI explanation reaches the teacher
            self.assertEqual(attempt["writings"][0]["answer_text"], "Ich habe keine Zeit, weil ich arbeite.")
            sub_id = attempt["recordings"][0]["submission_id"]
            path, media = multilevel.recording(db, self.user(db, "tc"), mine, sub_id)
            self.assertTrue(path.is_file() and media == "audio/webm")
            with self.assertRaises(HTTPException) as c:
                multilevel.recording(db, self.user(db, "tc"), other, sub_id)  # the student is not in that group
            self.assertEqual(c.exception.status_code, 404)
            self.assertTrue(db.scalar(select(StudyGroup.id).where(StudyGroup.id == mine.id)))
            self.assertIsNotNone(svc)

    def test_rescore_script_on_rows_from_before(self):
        from app.models.mock_attempt_section import MockAttemptSection
        from app.models.mock_test_attempt import MockTestAttempt
        from app.scripts import multilevel_rescore
        from app.services.mock_exam import multilevel_exam_service as svc

        with self.Session() as db:
            aid = self.exam_until_ai(db)
            # make it look like an attempt from before the AI: Lesen by the old linear rule, Schreiben graded by a person, Sprechen never graded
            for s in db.query(MockAttemptSection).filter_by(attempt_id=aid):
                s.score_source, s.auto_score, s.ai_status = None, None, None
                if s.section_type == "LESEN":
                    s.raw_points, s.raw_max, s.score, s.level = 26, 35, 56, "B2"
                elif s.section_type == "SCHREIBEN":
                    s.score, s.graded_by = 40, self.user_ids["sa"]
            db.commit()
            plan = multilevel_rescore.build_plan(db)
            self.assertIn(str(aid), plan["attempt_ids"])
            self.assertEqual(self.section(db, aid, "LESEN").score, 56)  # plan is read-only
            for key in ("LESEN score changed", "SCHREIBEN kept as manual score", "SPRECHEN queued for the AI"):
                self.assertGreaterEqual(plan["counts"].get(key, 0), 1, key)
            with tempfile.TemporaryDirectory() as tmp:
                done = multilevel_rescore.apply_plan(db, plan["plan_id"], Path(tmp))
                snap = json.loads(Path(done["backup"]).read_text(encoding="utf-8"))
                self.assertTrue(any(s["attempt_id"] == str(aid) and s["section_type"] == "LESEN" and s["score"] == 56 for s in snap["sections"]))
            les, sch, spr = (self.section(db, aid, k) for k in ("LESEN", "SCHREIBEN", "SPRECHEN"))
            self.assertEqual((les.score, les.score_source), (63, "AUTO"))  # 26 / 35 → 63 in the table
            self.assertEqual((sch.score, sch.override_score, sch.score_source), (40, 40, "MANUAL"))
            self.assertEqual(spr.ai_status, "PENDING")
            self.assertEqual(db.get(MockTestAttempt, aid).result_level, "PENDING")
            self.assertEqual(multilevel_rescore.build_plan(db)["attempts"], 0)  # idempotent
            self.assertEqual(svc.get_settings(db)["bands"], svc.scoring.DEFAULT_BANDS)


if __name__ == "__main__":
    unittest.main()
