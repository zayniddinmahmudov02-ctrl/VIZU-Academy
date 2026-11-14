"""Free first lesson + purchase gating against PostgreSQL (VIZU_WB_TEST_DB_URL = a migrated test database).

Own A1 / A2 / B1 / B2 courses with 3 published lessons each; the level settings are those of production (B1 "Verkauf"
flag off, A2 on, one free lesson). Orders go through the real checkout + approval. Checks the one gate
(`lms.access.lesson_access` -> `require_lesson_access`): lesson 1 free, lesson 2+ PREMIUM_REQUIRED (buy prompt, also
for B1 whose old flag is off), A1 opens only A1, A1–B1 opens three levels, A1–C1 opens B2 once released, expiry closes,
direct API calls refused; the legacy quiz lists and preview videos no longer bypass it."""

import asyncio
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
PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 64
PROD_SETTINGS = {"sales": {"A2": True}, "free_lessons": 1}
LEVELS = ("A1", "A2", "B1", "B2")


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestLessonPurchaseGating(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
        from app.models.course import Course
        from app.models.language import Language
        from app.models.lesson import Lesson
        from app.models.module import Module
        from app.models.quiz import Quiz
        from app.models.quiz_option import QuizOption
        from app.models.quiz_question import QuizQuestion
        from app.models.user import User

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        tag = uuid.uuid4().hex[:6]
        cls.tag = tag
        with cls.Session() as db:
            users = []
            for name, role in (("none", "STUDENT"), ("a1", "STUDENT"), ("a1b1", "STUDENT"), ("a1c1", "STUDENT"), ("adm", "SUPER_ADMIN")):
                u = User(email=f"gate-{name}-{tag}@test.local", username=f"gate_{name}_{tag}", password_hash="x", is_active=True,
                         is_verified=True, is_superuser=role == "SUPER_ADMIN", role=role, is_banned=False, preferred_language="uz")
                db.add(u)
                users.append(u)
            lang = Language(code=f"g{tag}", locale=f"g-{tag}", name=f"Gate {tag}")
            db.add(lang)
            db.flush()
            cls.course_ids, cls.lessons = [], {}
            for i, level in enumerate(LEVELS):
                course = Course(language_id=lang.id, level=level, title=f"{level} gate {tag}", order_index=i + 1, is_active=True)
                db.add(course)
                db.flush()
                module = Module(course_id=course.id, number=1, title="Modul 1", order_index=1, is_active=True)
                db.add(module)
                db.flush()
                rows = [Lesson(module_id=module.id, number=n, title=f"{level} Lektion {n}", duration=10, is_published=True) for n in (1, 2, 3)]
                db.add_all(rows)
                db.flush()
                cls.course_ids.append(course.id)
                cls.lessons[level] = [r.id for r in rows]
            # one quiz in A1 lesson 1 (free) and one in lesson 2 (paid)
            cls.quiz_ids = []
            for lesson_id in cls.lessons["A1"][:2]:
                quiz = Quiz(lesson_id=lesson_id, title="Quiz", is_published=True)
                db.add(quiz)
                db.flush()
                q = QuizQuestion(quiz_id=quiz.id, question="Frage?", question_type="SINGLE_CHOICE", points=1, order_index=1, is_published=True)
                db.add(q)
                db.flush()
                db.add_all([QuizOption(question_id=q.id, option_text=t, is_correct=t == "ja", order_index=n) for n, t in enumerate(("ja", "nein"))])
                cls.quiz_ids.append(quiz.id)
            db.commit()
            cls.user_ids = [u.id for u in users]
            cls.lang_id = lang.id
        cls.tmp = tempfile.TemporaryDirectory()
        from app.services.vizu_pay import offers
        from app.services.vizu_pay.service import VizuPayService

        cls.patches = [patch.object(type(VizuPayService(None).proof_storage), "ROOT", Path(cls.tmp.name)),
                       patch.object(offers, "_read_overrides", lambda: PROD_SETTINGS)]
        for p in cls.patches:
            p.start()
        offers.invalidate_cache()
        # buyers: real checkout + approval
        with cls.Session() as db:
            from app.services.vizu_pay.admin_service import AdminVizuPayService

            admin = db.get(User, cls.user_ids[4])
            for uid, plan in zip(cls.user_ids[1:4], ("A1", "A1_B1", "A1_C1")):
                user = db.get(User, uid)
                from starlette.datastructures import Headers, UploadFile

                proof = UploadFile(io.BytesIO(PNG), filename="r.png", headers=Headers({"content-type": "image/png"}))
                out = asyncio.run(VizuPayService(db).create_order(user, plan=plan, payment_method="UZCARD", promo_code=None,
                                                                  proof_file=proof, ip=None))
                AdminVizuPayService(db).approve_order(out["id"], admin, None)
            db.commit()

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete

        from app.models.audit_log import AuditLog
        from app.models.course import Course
        from app.models.language import Language
        from app.models.user import User
        from app.services.vizu_pay import offers

        with cls.Session() as db:
            db.execute(delete(AuditLog).where(AuditLog.actor_id.in_([str(i) for i in cls.user_ids])))
            db.execute(delete(AuditLog).where(AuditLog.target_user_id.in_([str(i) for i in cls.user_ids])))
            db.execute(delete(Course).where(Course.id.in_(cls.course_ids)))  # cascades modules, lessons, quizzes
            db.execute(delete(Language).where(Language.id == cls.lang_id))
            db.execute(delete(User).where(User.id.in_(cls.user_ids)))  # cascades orders
            db.commit()
        for p in cls.patches:
            p.stop()
        offers.invalidate_cache()
        cls.tmp.cleanup()
        cls.engine.dispose()

    def setUp(self):
        from app.services.vizu_pay import offers

        offers.invalidate_cache()
        self.db = self.Session()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    # helpers -----------------------------------------------------------
    def user(self, i):
        from app.models.user import User

        self.db.info.clear()  # per-session access caches (one request = one session in the app)
        return self.db.get(User, self.user_ids[i])

    def access(self, i, level, n):
        from app.models.lesson import Lesson
        from app.services.lms.access import lesson_access

        user = self.user(i)
        return lesson_access(self.db, user, self.db.get(Lesson, self.lessons[level][n - 1]))

    def api(self, i, level, n):
        """The dependency every lesson-content endpoint uses — what a direct API call meets."""
        from app.api.dependencies.progress import require_lesson_access

        return asyncio.run(require_lesson_access(self.lessons[level][n - 1], self.user(i), self.db))

    def assertOpen(self, i, level, *numbers):
        for n in numbers:
            with self.subTest(user=i, level=level, lesson=n):
                self.assertTrue(self.access(i, level, n).unlocked)

    def assertBuy(self, i, level, *numbers, reason="PREMIUM_REQUIRED"):
        for n in numbers:
            with self.subTest(user=i, level=level, lesson=n):
                a = self.access(i, level, n)
                self.assertEqual((a.unlocked, a.reason), (False, reason))

    # 1–3, 9: no purchase ------------------------------------------------
    def test_1_first_lesson_free_rest_needs_purchase(self):
        for level in ("A1", "A2", "B1"):
            self.assertOpen(0, level, 1)
            self.assertBuy(0, level, 2, 3)  # B1 too: its old "Verkauf" flag is off, but a package sells it -> buy prompt
        self.assertBuy(0, "B2", 1, 2, reason="LEVEL_COMING_SOON")  # not released: not even the free lesson
        self.api(0, "A1", 1)
        for level, n in (("A1", 2), ("A1", 3), ("B1", 2)):
            with self.subTest(api=(level, n)), self.assertRaises(HTTPException) as ctx:
                self.api(0, level, n)
            self.assertEqual((ctx.exception.status_code, ctx.exception.detail), (403, "PREMIUM_REQUIRED"))

    def test_2_level_cards_and_sale_block(self):
        from app.services.lms import progress

        user = self.user(0)
        sale = progress.level_sale(user, "B1")
        self.assertEqual((sale["sales_enabled"], sale["sales_closed"], sale["owned"]), (True, False, False))
        from app.models.lesson import Lesson
        from app.services.vizu_pay.access import is_free_lesson

        self.assertEqual([is_free_lesson(self.db.get(Lesson, lid)) for lid in self.lessons["A1"]], [True, False, False])

    # 4–6: purchases ----------------------------------------------------
    def test_3_a1_buyer(self):
        self.assertOpen(1, "A1", 1, 2, 3)
        self.api(1, "A1", 3)
        self.assertOpen(1, "A2", 1)
        self.assertBuy(1, "A2", 2, 3)
        self.assertBuy(1, "B1", 2)

    def test_4_a1_b1_buyer(self):
        for level in ("A1", "A2", "B1"):
            self.assertOpen(2, level, 1, 2, 3)
        self.assertBuy(2, "B2", 2, reason="LEVEL_COMING_SOON")

    # 7: A1–C1 opens B2 once released, without a new payment ---------------
    def test_5_a1_c1_buyer_gets_b2_when_released(self):
        from app.services.vizu_pay import offers

        for level in ("A1", "A2", "B1"):
            self.assertOpen(3, level, 1, 2, 3)
        self.assertBuy(3, "B2", 2, reason="LEVEL_COMING_SOON")
        released = dict(PROD_SETTINGS, levels={"B2": True})
        with patch.object(offers, "_read_overrides", lambda: released):
            offers.invalidate_cache()
            self.assertOpen(3, "B2", 1, 2, 3)
            self.assertOpen(0, "B2", 1)  # the free first lesson of a released level
            self.assertBuy(0, "B2", 2)  # buyable through the A1–C1 package
            self.assertBuy(2, "B2", 2)  # A1–B1 never covered B2
        offers.invalidate_cache()

    # 8: expiry ----------------------------------------------------------
    def test_6_expired_package_closes(self):
        from sqlalchemy import select

        from app.models.subscription_order import SubscriptionOrder

        order = self.db.scalar(select(SubscriptionOrder).where(SubscriptionOrder.user_id == self.user_ids[1], SubscriptionOrder.status == "APPROVED"))
        end = order.access_end_date
        self.assertGreater(end, datetime.now(timezone.utc))
        order.access_end_date = datetime.now(timezone.utc) - timedelta(seconds=1)
        self.db.commit()
        try:
            self.assertOpen(1, "A1", 1)
            self.assertBuy(1, "A1", 2, 3)
            with self.assertRaises(HTTPException):
                self.api(1, "A1", 2)
        finally:
            order = self.db.get(SubscriptionOrder, order.id)
            order.access_end_date = end
            self.db.commit()

    # 9: other ways in ---------------------------------------------------
    def test_7_quiz_lists_follow_the_gate(self):
        from app.services.quiz import student_view

        free_quiz, paid_quiz = self.quiz_ids
        mine = {q.quiz_id for q in student_view.visible_questions(self.db, self.user(0))}
        self.assertIn(free_quiz, mine)
        self.assertNotIn(paid_quiz, mine)
        self.assertNotIn(paid_quiz, {q.quiz_id for q in student_view.visible_questions(self.db, None)})  # anonymous
        with self.assertRaises(HTTPException) as ctx:
            student_view.visible_options(self.db, self.user(0), paid_quiz)
        self.assertEqual(ctx.exception.detail, "PREMIUM_REQUIRED")
        self.assertEqual(len(student_view.visible_options(self.db, self.user(1), paid_quiz)), 2)  # A1 buyer
        from sqlalchemy import select

        from app.models.quiz_question import QuizQuestion

        question = self.db.scalar(select(QuizQuestion).where(QuizQuestion.quiz_id == paid_quiz))
        with self.assertRaises(HTTPException):
            student_view.ensure_question_open(self.db, self.user(0), question)
        student_view.ensure_question_open(self.db, self.user(1), question)

    def test_8_preview_flag_never_opens_a_lesson_video(self):
        from types import SimpleNamespace

        from app.services.video.service import VideoService

        self.assertTrue(VideoService.needs_access_check(SimpleNamespace(is_preview=True, lesson_id=self.lessons["A1"][1])))
        self.assertTrue(VideoService.needs_access_check(SimpleNamespace(is_preview=False, lesson_id=None)))
        self.assertFalse(VideoService.needs_access_check(SimpleNamespace(is_preview=True, lesson_id=None)))


if __name__ == "__main__":
    unittest.main()
