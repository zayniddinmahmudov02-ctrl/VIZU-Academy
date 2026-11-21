"""Student statistics (app/services/admin/student_stats.py): contract and permissions (no DB) and, against PostgreSQL
(VIZU_WB_TEST_DB_URL at head), the ten required cases — registration +1, teacher / admin not counted, several groups once,
logout changes nothing, Telegram counted, duplicate registration once, blocked / test-account rules, admin API permissions,
API numbers == an independent SQL COUNT (also through the paginated list). The shared test DB has rows of other tests, so
every case compares before / after."""

import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")

# independent of the service code: the documented rule written as plain SQL
SQL_STUDENTS = """
select count(*) from users where role = 'STUDENT' and not (
  split_part(lower(email), '@', 2) in ('example.com', 'example.net', 'example.org')
  or split_part(lower(email), '@', 2) like '%.example' or split_part(lower(email), '@', 2) like '%.test'
  or split_part(lower(email), '@', 2) like '%.invalid' or split_part(lower(email), '@', 2) like '%.localhost')
"""


class TestContract(unittest.TestCase):
    def test_overview_for_staff_list_only_for_super_admin(self):
        from app.api.admin.stats_router import router
        from app.api.dependencies.auth import require_admin_panel_access, require_super_admin

        deps = {r.path: [d.call for d in r.dependant.dependencies] for r in router.routes}
        self.assertIn(require_admin_panel_access, deps["/admin/stats/overview"])
        self.assertIn(require_super_admin, deps["/admin/stats/students"])

    def test_tashkent_calendar(self):
        from app.services.admin.student_stats import tashkent_day_start, tashkent_month_start

        late = datetime(2026, 11, 21, 20, 30, tzinfo=timezone.utc)  # 01:30 on the 22nd in Tashkent
        self.assertEqual(tashkent_day_start(late).astimezone(timezone.utc), datetime(2026, 11, 21, 19, 0, tzinfo=timezone.utc))
        self.assertEqual(tashkent_month_start(datetime(2026, 11, 30, 19, 30, tzinfo=timezone.utc)).astimezone(timezone.utc),
                         datetime(2026, 11, 30, 19, 0, tzinfo=timezone.utc))  # 1 December 00:30 local

    @unittest.skipUnless(__import__("importlib").util.find_spec("httpx"), "needs httpx (TestClient)")
    def test_anonymous_401(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        for path in ("/api/v1/admin/stats/overview", "/api/v1/admin/stats/students"):
            self.assertEqual(client.get(path).status_code, 401, path)


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestStudentStats(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        cls.Session = sessionmaker(bind=create_engine(DB_URL))

    def setUp(self):
        self.db = self.Session()
        self.tag = uuid.uuid4().hex[:8]

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def _stats(self):
        from app.services.admin import student_stats

        self.db.expire_all()
        return student_stats.overview(self.db)

    def _sql_count(self):
        from sqlalchemy import text

        return self.db.execute(text(SQL_STUDENTS)).scalar()

    def _register(self, ident, name="Test Talaba"):
        from app.schemas.auth.user import UserRegister
        from app.services.auth.service import create_user

        return create_user(self.db, UserRegister(identifier=ident, password="Geheim123!", full_name=name))

    def _user(self, role="STUDENT", email=None, **extra):
        from app.models.user import User

        u = User(email=email or f"st-{uuid.uuid4().hex[:10]}@test.local", username=f"st_{uuid.uuid4().hex[:10]}", password_hash="x",
                 is_active=True, is_verified=True, is_superuser=False, role=role, is_banned=False, preferred_language="uz", **extra)
        self.db.add(u)
        self.db.commit()
        return u

    # 1, 10
    def test_registration_adds_one_and_api_equals_sql_count(self):
        before = self._stats()
        u = self._register(f"new-{self.tag}@mail.uz")
        after = self._stats()
        self.assertEqual(after["total_students"], before["total_students"] + 1)
        self.assertEqual(after["total_registrations_today"], before["total_registrations_today"] + 1)
        self.assertEqual(after["total_registrations_this_month"], before["total_registrations_this_month"] + 1)
        self.assertEqual(after["total_students"], self._sql_count())
        self.assertEqual(after["active_students"] + after["inactive_students"], after["total_students"])
        self.assertEqual(u.role, "STUDENT")

    # 2, 3
    def test_teachers_and_admins_are_not_students(self):
        before = self._stats()
        self._user("TEACHER")
        self._user("ADMIN")
        self._user("SUPER_ADMIN")
        promoted = self._register(f"later-teacher-{self.tag}@mail.uz")  # a registration promoted to teacher
        promoted.role = "TEACHER"
        self.db.commit()
        after = self._stats()
        self.assertEqual(after["total_students"], before["total_students"])
        self.assertEqual(after["total_teachers"], before["total_teachers"] + 2)
        self.assertEqual(after["total_admins"], before["total_admins"] + 2)
        self.assertEqual(after["total_accounts"], before["total_accounts"] + 4)

    # 4
    def test_student_in_several_groups_counts_once(self):
        from app.services.study_groups import groups

        teacher = self._user("TEACHER")
        before = self._stats()
        s = self._register(f"groups-{self.tag}@mail.uz")
        for n in range(3):
            _g, code = groups.create(self.db, teacher, {"name": f"Stats {n} {self.tag}", "level": "A1"})
            groups.join(self.db, s, code, "10.20.0.1")
        after = self._stats()
        self.assertEqual(after["total_students"], before["total_students"] + 1)
        self.assertEqual(after["students_in_groups"], before["students_in_groups"] + 1)
        self.assertEqual(after["total_groups"], before["total_groups"] + 3)

    # 5
    def test_logout_changes_nothing(self):
        from app.services.auth.service import issue_token_pair, revoke_refresh_token

        s = self._register(f"logout-{self.tag}@mail.uz")
        s.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
        self.db.commit()
        pair = issue_token_pair(self.db, s)
        before = self._stats()
        revoke_refresh_token(self.db, pair.refresh_token)
        after = self._stats()
        for key in ("total_students", "active_students", "inactive_students"):
            self.assertEqual(after[key], before[key], key)

    # 6
    def test_telegram_registration_counts_once(self):
        from app.services.auth.service import get_or_create_telegram_user

        tg = int(uuid.uuid4().int % 9_000_000_000) + 1_000_000_000
        before = self._stats()
        get_or_create_telegram_user(self.db, {"id": tg, "first_name": "Tg", "username": f"tg_{self.tag}"})
        get_or_create_telegram_user(self.db, {"id": tg, "first_name": "Tg"})  # the same person again
        after = self._stats()
        self.assertEqual(after["total_students"], before["total_students"] + 1)

    # 7
    def test_duplicate_registration_counts_once(self):
        before = self._stats()
        self._register(f"Twice-{self.tag}@Mail.uz")
        for again in (f"twice-{self.tag}@mail.uz", f"  TWICE-{self.tag}@MAIL.UZ "):
            with self.assertRaises(HTTPException) as ctx:
                self._register(again)
            self.assertEqual(ctx.exception.status_code, 409)
        phone = f"+99890{int(self.tag, 16) % 10_000_000:07d}"
        self._register(phone)
        with self.assertRaises(HTTPException):
            self._register(phone.replace("+998", "998 "))
        after = self._stats()
        self.assertEqual(after["total_students"], before["total_students"] + 2)

    # 8
    def test_blocked_stay_registered_test_accounts_are_separate(self):
        before = self._stats()
        banned = self._register(f"banned-{self.tag}@mail.uz")
        banned.is_banned = True
        off = self._register(f"off-{self.tag}@mail.uz")
        off.is_active = False
        suspended = self._register(f"susp-{self.tag}@mail.uz")
        suspended.suspended_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=3)
        for u in (banned, off, suspended):
            u.last_login = datetime.now(timezone.utc).replace(tzinfo=None)  # recent login, still not "active"
        self._user("STUDENT", email=f"qa-{self.tag}@example.com")
        self._user("STUDENT", email=f"qa-{self.tag}@demo.test")
        phone_placeholder = self._user("STUDENT", email=f"99890{self.tag[:7]}@phone.vizu-deutsch.com")
        self.db.commit()
        after = self._stats()
        self.assertEqual(after["total_students"], before["total_students"] + 4)  # 3 blocked + the phone account
        self.assertEqual(after["blocked_students"], before["blocked_students"] + 3)
        self.assertEqual(after["active_students"], before["active_students"])
        self.assertEqual(after["test_accounts"], before["test_accounts"] + 2)
        self.assertEqual(after["total_students"], self._sql_count())
        self.assertTrue(phone_placeholder.id)

    def test_active_means_recent_login_or_lesson_progress(self):
        s = self._register(f"active-{self.tag}@mail.uz")
        before = self._stats()
        s.last_login = (datetime.now(timezone.utc) - timedelta(days=40)).replace(tzinfo=None)
        self.db.commit()
        self.assertEqual(self._stats()["active_students"], before["active_students"])
        s.last_login = (datetime.now(timezone.utc) - timedelta(days=2)).replace(tzinfo=None)
        self.db.commit()
        self.assertEqual(self._stats()["active_students"], before["active_students"] + 1)

    # 10 (through the list): pagination and filters never change the total
    def test_list_totals_match_the_overview(self):
        from app.services.admin import student_stats

        self._register(f"list-{self.tag}@mail.uz")
        st = self._stats()
        page1 = student_stats.list_students(self.db, page=1, page_size=5)
        self.assertEqual(page1["total"], st["total_students"])
        seen, page = set(), 1
        while True:
            chunk = student_stats.list_students(self.db, page=page, page_size=100)
            seen |= {i["id"] for i in chunk["items"]}
            if page * 100 >= chunk["total"]:
                break
            page += 1
        self.assertEqual(len(seen), st["total_students"])  # every student exactly once across the pages
        totals = {s: student_stats.list_students(self.db, status=s, page_size=1)["total"] for s in student_stats.LIST_STATUSES}
        self.assertEqual(totals["active"] + totals["inactive"], totals["all"])
        self.assertEqual(totals["active"], st["active_students"])
        self.assertEqual(totals["blocked"], st["blocked_students"])
        self.assertEqual(totals["test_takers"], st["test_takers"])
        self.assertEqual(totals["test_accounts"], st["test_accounts"])
        hit = student_stats.list_students(self.db, search=f"list-{self.tag}")
        self.assertEqual(hit["total"], 1)
        self.assertEqual(hit["items"][0]["registered_via"], "email")

    def test_test_takers_and_participants_are_separate_numbers(self):
        from app.models.vizu_multilevel_attempt import VizuMultilevelAttempt

        s = self._register(f"tester-{self.tag}@mail.uz")
        before = self._stats()
        self.db.add(VizuMultilevelAttempt(user_id=s.id, attempt_number=1, status="IN_PROGRESS"))
        self.db.commit()
        self.assertEqual(self._stats()["test_takers"], before["test_takers"])  # unfinished does not count
        attempt = self.db.query(VizuMultilevelAttempt).filter_by(user_id=s.id).one()
        attempt.status = "COMPLETED"
        self.db.commit()
        after = self._stats()
        self.assertEqual(after["test_takers"], before["test_takers"] + 1)
        self.assertEqual(after["total_students"], before["total_students"])

    def test_language_learners_follow_the_same_rule(self):
        from app.models.course import Course
        from app.models.language import Language
        from app.models.lesson import Lesson
        from app.models.module import Module
        from app.models.student_progress import StudentProgress
        from app.models.user_language import UserLanguage
        from app.services.language import service as languages

        lang = Language(code=f"x{self.tag[:5]}", locale=f"x-{self.tag[:5]}", name=f"Stats {self.tag}")
        self.db.add(lang)
        self.db.flush()
        course = Course(language_id=lang.id, level="A1", title=f"Stats {self.tag}", order_index=1, is_active=True)
        self.db.add(course)
        self.db.flush()
        module = Module(course_id=course.id, number=1, title="M", order_index=1, is_active=True)
        self.db.add(module)
        self.db.flush()
        lesson = Lesson(module_id=module.id, number=1, title="L", duration=10, is_published=True)
        self.db.add(lesson)
        self.db.commit()
        learner = self._register(f"learner-{self.tag}@mail.uz")
        both = self._register(f"both-{self.tag}@mail.uz")
        teacher, test_acc = self._user("TEACHER"), self._user("STUDENT", email=f"qa2-{self.tag}@example.org")
        for u in (learner, both, teacher, test_acc):
            self.db.add(StudentProgress(user_id=u.id, lesson_id=lesson.id))
        self.db.add(UserLanguage(user_id=both.id, language_id=lang.id))
        self.db.commit()
        self.assertEqual(languages.get_language_statistics(self.db, lang.id)["learners"], 2)  # once each, staff / test out
        self.assertEqual(languages.get_language_statistics(self.db, lang.id)["active_learners"], 2)
        page = languages.get_language_learners(self.db, lang.id, None, 1, 20)
        self.assertEqual((page["total"], {i["id"] for i in page["items"]}), (2, {learner.id, both.id}))
        self.assertEqual(languages.get_language_learners(self.db, lang.id, f"both-{self.tag}", 1, 20)["total"], 1)

    # 9: the router's gates themselves
    def test_api_permissions(self):
        import asyncio

        from app.api.dependencies.auth import require_admin_panel_access, require_super_admin

        student, teacher, admin = self._user("STUDENT"), self._user("TEACHER"), self._user("SUPER_ADMIN")
        run = asyncio.run
        with self.assertRaises(HTTPException) as ctx:
            run(require_admin_panel_access(student))
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIs(run(require_admin_panel_access(teacher)), teacher)
        with self.assertRaises(HTTPException) as ctx:
            run(require_super_admin(teacher))
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIs(run(require_super_admin(admin)), admin)


if __name__ == "__main__":
    unittest.main()
