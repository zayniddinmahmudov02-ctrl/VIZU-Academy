"""Multilevel groups (owner 2026-11-28) against PostgreSQL (VIZU_WB_TEST_DB_URL = a migrated test database).

* access: an ACTIVE student member of an ACTIVE group linked to the Multilevel level opens its Modelltests without the Premium; leaving /
  removal / a paused group / an unlinked group / another level close them; the Premium status says "group_access".
* link: only a SUPER_ADMIN sets `mock_exam_level_id` (teacher 403 multilevel_link_admin_only), only to the Multilevel level, audited.
* results (read only): overview per student (tests taken, attempts, last attempt, latest sections + total, best total, estimated level), the
  drill-down per Modelltest, the student's own view; an open attempt shows no score; scoping = group managers / the member only (404).
* script multilevel_groups_link: plan is read-only, apply links + removes the C1 course link with a JSON copy, idempotent."""

import os
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import HTTPException

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestMultilevelGroups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
        from app.models.certification_provider import CertificationProvider
        from app.models.course import Course
        from app.models.kompetenz import Kompetenz
        from app.models.language import Language
        from app.models.mock_exam_level import MockExamLevel
        from app.models.model_test import ModelTest
        from app.models.user import User
        from app.services.mock_exam import multilevel_service

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        db = cls.Session()
        if db.scalar(select(MockExamLevel).where(MockExamLevel.title == multilevel_service.LEVEL_TITLE)):
            db.close()
            raise unittest.SkipTest("the test database already holds a Multilevel level")
        tag = uuid.uuid4().hex[:6]
        cls.tag = tag
        users = {}
        for name, role in (("a", "STUDENT"), ("b", "STUDENT"), ("out", "STUDENT"), ("t", "TEACHER"), ("t2", "TEACHER"), ("s", "SUPER_ADMIN")):
            users[name] = User(email=f"mlg-{name}-{tag}@test.local", username=f"mlg_{name}_{tag}", password_hash="x", is_active=True,
                               is_verified=True, is_superuser=role == "SUPER_ADMIN", role=role, is_banned=False, preferred_language="uz",
                               first_name=f"N{name}", last_name="Test")
            db.add(users[name])
        db.flush()
        provider = CertificationProvider(name=f"MLG {tag}", code=f"MLG{tag}", is_active=True)
        db.add(provider)
        db.flush()
        level = MockExamLevel(provider_id=provider.id, level="B1–C1", title=multilevel_service.LEVEL_TITLE, is_active=True)
        other = MockExamLevel(provider_id=provider.id, level="B1", title=f"Other {tag}", is_active=True)
        db.add_all([level, other])
        db.flush()
        cls.tests, cls.komps = [], {}
        for sort, lv in ((1, level), (2, level), (2, other)):  # other level: not number 1 (free there by the old provider rule)
            t = ModelTest(level_id=lv.id, title=f"Modelltest {sort} {lv.title}", status="PUBLISHED", sort_order=sort)
            db.add(t)
            db.flush()
            cls.tests.append(t.id)
            for i, kind in enumerate(["LESEN", "HOEREN", "SCHREIBEN", "SPRECHEN"], start=1):
                k = Kompetenz(model_test_id=t.id, type=kind, title=kind.title(), total_points=0, duration_minutes=10, sort_order=i)
                db.add(k)
                db.flush()
                cls.komps[(t.id, kind)] = k.id
        lang = Language(code=f"m{tag}", locale=f"m-{tag}", name=f"MLG {tag}")
        db.add(lang)
        db.flush()
        course = Course(language_id=lang.id, level="C1", title=f"C1 Advanced {tag}", order_index=1, is_active=True)
        db.add(course)
        db.commit()
        cls.user_ids = {k: u.id for k, u in users.items()}
        cls.level_id, cls.other_level_id, cls.provider_id = level.id, other.id, provider.id
        cls.course_id, cls.lang_id = course.id, lang.id
        db.close()

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete

        from app.models.audit_log import AuditLog
        from app.models.certification_provider import CertificationProvider
        from app.models.course import Course
        from app.models.language import Language
        from app.models.study_group import StudyGroup
        from app.models.user import User

        ids = list(cls.user_ids.values())
        with cls.Session() as db:
            db.execute(delete(StudyGroup).where(StudyGroup.teacher_id.in_(ids)))
            db.execute(delete(CertificationProvider).where(CertificationProvider.id == cls.provider_id))  # levels, tests, attempts cascade
            db.execute(delete(Course).where(Course.id == cls.course_id))
            db.execute(delete(Language).where(Language.id == cls.lang_id))
            db.execute(delete(AuditLog).where(AuditLog.actor_id.in_([str(i) for i in ids])))
            db.execute(delete(AuditLog).where(AuditLog.target_user_id.in_([str(i) for i in ids])))
            db.execute(delete(AuditLog).where(AuditLog.action == "multilevel_groups_link_script"))  # test database only
            db.execute(delete(User).where(User.id.in_(ids)))
            db.commit()
        cls.engine.dispose()

    def setUp(self):
        self.db = self.Session()
        self.groups = []

    def tearDown(self):
        from sqlalchemy import delete

        from app.models.mock_test_attempt import MockTestAttempt
        from app.models.study_group import StudyGroup

        self.db.rollback()
        self.db.execute(delete(MockTestAttempt).where(MockTestAttempt.user_id.in_(list(self.user_ids.values()))))
        self.db.execute(delete(StudyGroup).where(StudyGroup.id.in_(self.groups)))
        self.db.commit()
        self.db.close()

    # helpers -------------------------------------------------------------
    def u(self, name):
        from app.models.user import User

        self.db.info.clear()  # per-session access caches (one request = one session in the app)
        return self.db.get(User, self.user_ids[name])

    def group(self, linked=True, teacher="t", members=("a", "b"), name=None, status="active"):
        from app.models.study_group import StudyGroup, StudyGroupMember

        g = StudyGroup(name=name or f"Multilevel {uuid.uuid4().hex[:4]} ", level="C1", teacher_id=self.user_ids[teacher], status=status,
                       mock_exam_level_id=self.level_id if linked else None)
        self.db.add(g)
        self.db.flush()
        for m in members:
            self.db.add(StudyGroupMember(group_id=g.id, user_id=self.user_ids[m], role="student", status="active", joined_at=datetime.now(timezone.utc)))
        self.db.commit()
        self.groups.append(g.id)
        return g

    def mt(self, i):
        from app.models.model_test import ModelTest

        return self.db.get(ModelTest, self.tests[i])

    def attempt(self, who, test_i, scores, status="GRADED", days_ago=0):
        """Attempt with closed sections (scores = dict kind -> score) or an open one."""
        from app.models.mock_attempt_section import MockAttemptSection
        from app.models.mock_test_attempt import MockTestAttempt

        t0 = datetime.now(timezone.utc) - timedelta(days=days_ago)
        test_id = self.tests[test_i]
        finished = status != "IN_PROGRESS"
        a = MockTestAttempt(model_test_id=test_id, user_id=self.user_ids[who], status=status, started_at=t0,
                            submitted_at=t0 + timedelta(hours=3) if finished else None,
                            total_score=sum(scores.values()) if finished and len(scores) == 4 else None, max_score=300 if finished else None,
                            time_spent_seconds=600, result_level="UNGEKLAERT" if finished else None)
        self.db.add(a)
        self.db.flush()
        for kind, score in scores.items():
            self.db.add(MockAttemptSection(attempt_id=a.id, kompetenz_id=self.komps[(test_id, kind)], section_type=kind,
                                           status="SUBMITTED", started_at=t0, deadline_at=t0 + timedelta(hours=1), submitted_at=t0 + timedelta(minutes=50),
                                           raw_points=score, raw_max=75, score=score, level=None))
        self.db.commit()
        return a

    # access ----------------------------------------------------------------
    def test_group_membership_opens_the_level(self):
        from app.models.study_group import StudyGroupMember
        from app.services.vizu_pay import multilevel_premium
        from app.services.vizu_pay.access import can_access_model_test

        self.assertFalse(can_access_model_test(self.mt(0), self.u("a")))
        g = self.group(name="Multilevel 1.Gruppe ")
        self.assertTrue(can_access_model_test(self.mt(0), self.u("a")))
        self.assertTrue(can_access_model_test(self.mt(1), self.u("a")))
        self.assertFalse(can_access_model_test(self.mt(2), self.u("a")))  # another level: never
        self.assertFalse(can_access_model_test(self.mt(0), self.u("out")))  # not a member
        st = multilevel_premium.status(self.db, self.u("a"))
        self.assertEqual((st["entitled"], st["group_access"], st["groups"]), (False, True, ["Multilevel 1.Gruppe"]))
        self.assertFalse(multilevel_premium.status(self.db, self.u("out"))["group_access"])
        # paused group, removed member, unlinked group: closed again
        g.status = "paused"
        self.db.commit()
        self.assertFalse(can_access_model_test(self.mt(0), self.u("a")))
        g.status = "active"
        m = self.db.query(StudyGroupMember).filter_by(group_id=g.id, user_id=self.user_ids["a"]).one()
        m.status = "removed"
        self.db.commit()
        self.assertFalse(can_access_model_test(self.mt(0), self.u("a")))
        self.assertTrue(can_access_model_test(self.mt(0), self.u("b")))
        g.mock_exam_level_id = None
        self.db.commit()
        self.assertFalse(can_access_model_test(self.mt(0), self.u("b")))

    def test_exam_list_and_start_follow_the_group(self):
        from app.services.mock_exam import multilevel_exam_service as svc

        self.group(linked=False)
        with self.assertRaises(HTTPException) as c:
            svc.start_attempt(self.db, self.u("a"), self.tests[0])
        self.assertEqual(c.exception.status_code, 403)
        self.group(linked=True, members=("a",))
        exams = {e["model_test_id"]: e for e in svc.list_exams(self.db, self.u("a"))}
        self.assertFalse(exams[self.tests[0]]["is_locked"])
        self.assertTrue(exams[self.tests[1]]["is_locked"] is False)
        with self.assertRaises(HTTPException) as c:  # past the access gate: the fixture test has no questions
            svc.start_attempt(self.db, self.u("a"), self.tests[0])
        self.assertEqual((c.exception.status_code, c.exception.detail), (409, "EXAM_NOT_READY"))
        self.assertTrue(all(e["is_locked"] for e in svc.list_exams(self.db, self.u("out"))))

    # link permissions ----------------------------------------------------------
    def test_only_super_admin_links(self):
        from sqlalchemy import select

        from app.models.study_group import StudyGroupAuditLog
        from app.services.study_groups import groups

        g = self.group(linked=False)
        with self.assertRaises(HTTPException) as c:
            groups.update(self.db, self.u("t"), g.id, {"mock_exam_level_id": self.level_id})
        self.assertEqual((c.exception.status_code, c.exception.detail), (403, "multilevel_link_admin_only"))
        self.db.rollback()
        with self.assertRaises(HTTPException) as c:
            groups.update(self.db, self.u("s"), g.id, {"mock_exam_level_id": self.other_level_id})
        self.assertEqual((c.exception.status_code, c.exception.detail), (422, "unknown_multilevel_level"))
        self.db.rollback()
        out = groups.update(self.db, self.u("s"), g.id, {"mock_exam_level_id": self.level_id})
        self.assertEqual(out["multilevel"]["id"], self.level_id)
        log = self.db.scalar(select(StudyGroupAuditLog).where(StudyGroupAuditLog.group_id == g.id, StudyGroupAuditLog.action == "group.update")
                             .order_by(StudyGroupAuditLog.created_at.desc()))
        self.assertEqual(log.meta["mock_exam_level_id"], str(self.level_id))
        # a teacher's other edits keep working (the link is not sent / unchanged)
        self.assertEqual(groups.update(self.db, self.u("t"), g.id, {"name": "Multilevel X", "mock_exam_level_id": self.level_id})["name"], "Multilevel X")
        with self.assertRaises(HTTPException):
            groups.update(self.db, self.u("t"), g.id, {"mock_exam_level_id": None})  # unlinking is admin-only too
        self.db.rollback()
        self.assertIsNone(groups.update(self.db, self.u("s"), g.id, {"mock_exam_level_id": None})["multilevel"])
        # creating: a teacher may not create a linked group; options list the level only for the admin
        with self.assertRaises(HTTPException):
            groups.create(self.db, self.u("t"), {"name": "ML neu", "level": "C1", "mock_exam_level_id": self.level_id})
        self.db.rollback()
        self.assertEqual(groups.options(self.db, self.u("t"))["multilevel_levels"], [])
        self.assertEqual([x["id"] for x in groups.options(self.db, self.u("s"))["multilevel_levels"]], [self.level_id])

    # results ---------------------------------------------------------------------
    def test_overview_detail_and_mine(self):
        from app.services.study_groups import multilevel

        g = self.group()
        self.attempt("a", 0, {"LESEN": 60, "HOEREN": 50, "SCHREIBEN": 40, "SPRECHEN": 30}, days_ago=5)  # total 180
        self.attempt("a", 0, {"LESEN": 70, "HOEREN": 66, "SCHREIBEN": 65, "SPRECHEN": 67}, days_ago=2)  # total 268, avg 67 -> C1
        self.attempt("a", 1, {"LESEN": 55}, status="IN_PROGRESS", days_ago=0)
        self.attempt("out", 0, {"LESEN": 75, "HOEREN": 75, "SCHREIBEN": 75, "SPRECHEN": 75})  # not in the group: never shown
        ov = multilevel.overview(self.db, g)
        self.assertEqual([t["number"] for t in ov["tests"]], [1, 2])
        rows = {r["user_id"]: r for r in ov["students"]}
        self.assertEqual(set(rows), {self.user_ids["a"], self.user_ids["b"]})
        a = rows[self.user_ids["a"]]
        self.assertEqual((a["attempts"], a["tests_taken"], a["in_progress"], a["best_total"]), (3, 1, 1, 268))
        self.assertEqual(a["latest"]["total_score"], 268)
        self.assertEqual({k: v["score"] for k, v in a["latest"]["sections"].items()}, {"LESEN": 70, "HOEREN": 66, "SCHREIBEN": 65, "SPRECHEN": 67})
        self.assertEqual(a["latest"]["estimated_level"], "C1")
        self.assertIsNotNone(a["last_attempt_at"])
        b = rows[self.user_ids["b"]]
        self.assertEqual((b["attempts"], b["tests_taken"], b["latest"], b["best_total"]), (0, 0, None, None))

        detail = multilevel.student_detail(self.db, g, self.user_ids["a"])
        per = {t["number"]: t for t in detail["tests"]}
        self.assertEqual([x["total_score"] for x in per[1]["attempts"]], [268, 180])  # newest first, every attempt kept
        self.assertEqual(per[1]["attempts"][1]["estimated_level"], "B1")  # avg 45
        open_ = per[2]["attempts"][0]
        self.assertEqual(open_["status"], "IN_PROGRESS")
        self.assertIsNone(open_["total_score"])
        self.assertNotIn("score", open_["sections"]["LESEN"])  # no score of an unfinished attempt
        self.assertEqual(multilevel.mine(self.db, g, self.u("a"))["tests"], detail["tests"])

    def test_results_scope(self):
        import importlib

        router = importlib.import_module("app.api.study_groups.router")

        g = self.group()
        other = self.group(teacher="t2", members=("out",))
        self.assertEqual(len(router.multilevel_overview(g.id, self.db, self.u("t"))["students"]), 2)
        self.assertEqual(len(router.multilevel_overview(g.id, self.db, self.u("s"))["students"]), 2)  # SUPER_ADMIN
        for who in ("t2", "a"):  # another group's teacher, a student member
            with self.subTest(who=who), self.assertRaises(HTTPException) as c:
                router.multilevel_overview(g.id, self.db, self.u(who))
            self.assertEqual(c.exception.status_code, 404)
        with self.assertRaises(HTTPException) as c:
            router.multilevel_student(g.id, self.user_ids["out"], self.db, self.u("t"))  # not a member of this group
        self.assertEqual(c.exception.status_code, 404)
        self.assertIn("tests", router.multilevel_mine(g.id, self.db, self.u("a")))
        for who, gid in (("out", g.id), ("t", g.id)):  # non-member, the teacher (no "own" results)
            with self.subTest(mine=who), self.assertRaises(HTTPException) as c:
                router.multilevel_mine(gid, self.db, self.u(who))
            self.assertEqual(c.exception.status_code, 404)
        plain = self.group(linked=False)
        with self.assertRaises(HTTPException) as c:
            router.multilevel_overview(plain.id, self.db, self.u("t"))
        self.assertEqual((c.exception.status_code, c.exception.detail), (404, "not_a_multilevel_group"))
        self.assertIsNotNone(other)

    # production script ---------------------------------------------------------------
    def test_link_script(self):
        from sqlalchemy import select

        from app.models.study_group import StudyGroup, StudyGroupCourse
        from app.scripts import multilevel_groups_link as script

        prefix = f"Multilevel {self.tag}"
        g = self.group(linked=False, name=f"{prefix} 1.Gruppe ")
        self.db.add(StudyGroupCourse(group_id=g.id, course_id=self.course_id))
        self.db.commit()
        plan = script.build_plan(self.db, prefix)
        self.assertEqual((plan["changes"], plan["groups"][0]["set_link"], plan["groups"][0]["remove_courses"]), (1, True, [f"C1 Advanced {self.tag}"]))
        self.db.rollback()
        self.assertIsNone(self.db.get(StudyGroup, g.id).mock_exam_level_id)  # plan is read-only
        with self.assertRaises(RuntimeError):
            script.apply_plan(self.db, "wrong", Path(tempfile.gettempdir()), prefix)
        with tempfile.TemporaryDirectory() as tmp:
            out = script.apply_plan(self.db, plan["plan_id"], Path(tmp), prefix)
            self.assertEqual(out["changed"], 1)
            self.assertTrue(Path(out["backup"]).read_text(encoding="utf-8").count(str(self.course_id)) >= 1)
        self.db.expire_all()
        self.assertEqual(self.db.get(StudyGroup, g.id).mock_exam_level_id, self.level_id)
        self.assertEqual(list(self.db.scalars(select(StudyGroupCourse).where(StudyGroupCourse.group_id == g.id))), [])
        again = script.build_plan(self.db, prefix)
        self.assertEqual(again["changes"], 0)
        self.assertEqual(script.apply_plan(self.db, again["plan_id"], Path(tempfile.gettempdir()), prefix)["changed"], 0)


if __name__ == "__main__":
    unittest.main()
