"""Groups & Classroom against PostgreSQL (set VIZU_WB_TEST_DB_URL to a migrated
test database): permissions per role, join codes, chat, announcements, tasks,
monitoring from LMS data and grading through a group."""

import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from pydantic import ValidationError

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")


def _now():
    return datetime.now(timezone.utc)


class TestApiContract(unittest.TestCase):
    def test_every_route_requires_a_logged_in_user(self):
        from app.api.dependencies.auth import get_current_user
        from app.api.study_groups.router import router

        for route in router.routes:
            with self.subTest(route=route.path):
                self.assertIn(get_current_user, [d.call for d in route.dependant.dependencies])

    def test_bodies_cannot_smuggle_user_or_role(self):
        from app.api.study_groups.router import JoinIn, MessageIn, TaskIn

        with self.assertRaises(ValidationError):
            MessageIn(body="hi", user_id=str(uuid.uuid4()))
        with self.assertRaises(ValidationError):
            JoinIn(code="ABCD-EFGH", role="TEACHER")
        with self.assertRaises(ValidationError):
            TaskIn(lesson_id=uuid.uuid4(), teacher_id=uuid.uuid4())

    def test_codes_are_random_readable_and_only_hashed(self):
        from app.services.study_groups import codes

        made = {codes.generate() for _ in range(200)}
        self.assertEqual(len(made), 200)
        for c in made:
            self.assertRegex(c, r"^[A-Z2-9]{4}-[A-Z2-9]{4}$")
            self.assertFalse(set(c.replace("-", "")) & set("ILO01"))
        self.assertEqual(codes.code_hash("abcd efgh"), codes.code_hash("ABCD-EFGH"))
        self.assertNotIn("ABCDEFGH", codes.code_hash("ABCD-EFGH"))


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestGroups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.models.course import Course
        from app.models.language import Language
        from app.models.lesson import Lesson
        from app.models.module import Module
        from app.models.user import User
        from app.models.writing import Writing

        cls.Session = sessionmaker(bind=create_engine(DB_URL))
        db = cls.Session()
        tag = uuid.uuid4().hex[:6]

        def user(role, name):
            u = User(email=f"g-{name}-{tag}@test.local", username=f"g_{name}_{tag}", password_hash="x", is_active=True,
                     is_verified=True, is_superuser=False, role=role, is_banned=False, preferred_language="uz", first_name=name)
            db.add(u)
            return u

        cls.u = {n: user(r, n) for n, r in (("teacher", "TEACHER"), ("teacher2", "TEACHER"), ("admin", "SUPER_ADMIN"),
                                             ("s1", "STUDENT"), ("s2", "STUDENT"), ("s3", "STUDENT"), ("outsider", "STUDENT"))}
        lang = Language(code=f"t{tag}", locale=f"t-{tag}", name=f"Test {tag}")
        db.add(lang)
        db.flush()
        cls.course = Course(language_id=lang.id, level="A1", title=f"A1 test {tag}", order_index=1, is_active=True)
        cls.course_b1 = Course(language_id=lang.id, level="B1", title=f"B1 test {tag}", order_index=2, is_active=True)
        db.add_all([cls.course, cls.course_b1])
        db.flush()
        module = Module(course_id=cls.course.id, number=1, title="Modul 1", order_index=1, is_active=True)
        db.add(module)
        db.flush()
        cls.lessons = [Lesson(module_id=module.id, number=n, title=f"Lektion {n}", duration=10, is_published=True) for n in (1, 2)]
        db.add_all(cls.lessons)
        db.flush()
        cls.writing = Writing(lesson_id=cls.lessons[0].id, title="Brief", instruction="Schreib", order_index=1, is_published=True)
        other_module = Module(course_id=cls.course_b1.id, number=1, title="B1 Modul", order_index=1, is_active=True)
        db.add_all([cls.writing, other_module])
        db.flush()
        cls.b1_lesson = Lesson(module_id=other_module.id, number=1, title="B1 Lektion", duration=10, is_published=True)
        db.add(cls.b1_lesson)
        db.commit()
        cls.ids = {k: v.id for k, v in cls.u.items()}
        cls.course_id, cls.course_b1_id = cls.course.id, cls.course_b1.id
        cls.lesson_ids = [lesson.id for lesson in cls.lessons]
        cls.b1_lesson_id, cls.writing_id = cls.b1_lesson.id, cls.writing.id
        db.close()

    def setUp(self):
        from app.models.user import User

        self.db = self.Session()
        self.user = {k: self.db.get(User, v) for k, v in self.ids.items()}

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def _group(self, **extra):
        from app.services.study_groups import groups

        data = {"name": f"Gruppe {uuid.uuid4().hex[:4]}", "level": "A1", "course_ids": [self.course_id], **extra}
        return groups.create(self.db, self.user["teacher"], data)

    def _join(self, who, code):
        from app.services.study_groups import groups

        return groups.join(self.db, self.user[who], code, "10.0.0.1")

    def _fresh(self, name):
        """A new student only this test uses (no shared memberships, no rate-limit history)."""
        from app.models.user import User

        tag = uuid.uuid4().hex[:6]
        u = User(email=f"g-{name}-{tag}@test.local", username=f"g_{name}_{tag}", password_hash="x", is_active=True, is_verified=True,
                 is_superuser=False, role="STUDENT", is_banned=False, preferred_language="uz", first_name=name)
        self.db.add(u)
        self.db.commit()
        self.user[name] = u
        return u

    def _status(self, fn, *args):
        with self.assertRaises(HTTPException) as ctx:
            fn(*args)
        return ctx.exception.status_code, ctx.exception.detail

    # 1-3, 13: roles, ownership, smuggled teacher_id
    def test_only_teachers_create_and_only_admins_assign_teachers(self):
        from app.services.study_groups import groups

        self.assertEqual(self._status(groups.create, self.db, self.user["s1"], {"name": "x", "level": "A1"})[0], 403)
        self.assertEqual(self._status(groups.create, self.db, self.user["teacher"],
                                      {"name": "xx", "level": "A1", "teacher_id": self.ids["teacher2"]})[0], 403)
        self.assertEqual(self._status(groups.create, self.db, self.user["teacher"],
                                      {"name": "xx", "level": "A1", "course_ids": [self.course_b1_id]})[1], "course_level_mismatch")
        g, code = groups.create(self.db, self.user["admin"], {"name": "Admin group", "level": "A1", "teacher_id": self.ids["teacher2"]})
        self.assertEqual(g["teacher"]["id"], self.ids["teacher2"])
        # teacher 1 cannot manage teacher 2's group, not even see it
        self.assertEqual(self._status(groups.update, self.db, self.user["teacher"], g["id"], {"name": "hijack"})[0], 404)
        self.assertEqual(self._status(groups.list_groups, self.db, self.user["teacher"], "all")[0], 403)
        self.assertEqual(self._status(groups.list_groups, self.db, self.user["s1"], "teaching")[0], 403)
        mine = groups.list_groups(self.db, self.user["teacher"], "teaching", page_size=100)["items"]
        self.assertNotIn(g["id"], [i["id"] for i in mine])

    # 9-11: codes
    def test_join_codes(self):
        from sqlalchemy import func, select

        from app.models.study_group import StudyGroupJoinCode, StudyGroupMember
        from app.services.study_groups import groups

        g, code = self._group(capacity=2)
        stored = self.db.scalars(select(StudyGroupJoinCode.code_hash)).all()
        self.assertNotIn(code, stored)
        self.assertNotIn(code.replace("-", ""), stored)
        self.assertEqual(self._status(self._join, "s1", "ZZZZ-ZZZZ"), (404, "invalid_code"))
        preview = groups.preview(self.db, self.user["s1"], code, "10.0.0.1")
        self.assertEqual((preview["name"], preview["already_member"]), (g["name"], False))
        self.assertFalse(self._join("s1", code.lower().replace("-", " "))["already_member"])
        self.assertTrue(self._join("s1", code)["already_member"])  # same code again: no second row
        count = self.db.scalar(select(func.count()).select_from(StudyGroupMember).where(
            StudyGroupMember.group_id == g["id"], StudyGroupMember.user_id == self.ids["s1"]))
        self.assertEqual(count, 1)
        self.assertEqual(self._status(self._join, "teacher", code), (409, "own_group"))
        self._join("s2", code)
        self.assertEqual(self._status(self._join, "s3", code), (409, "group_full"))  # capacity 2
        # regenerating revokes the old code
        new = groups.regenerate_code(self.db, self.user["teacher"], g["id"])["code"]
        self.assertEqual(self._status(self._join, "s3", code), (404, "invalid_code"))
        groups.update(self.db, self.user["teacher"], g["id"], {"capacity": 5})
        groups.change_code(self.db, self.user["teacher"], g["id"], {"paused": True})
        self.assertEqual(self._status(self._join, "s3", new), (409, "code_paused"))
        groups.change_code(self.db, self.user["teacher"], g["id"], {"paused": False, "expires_at": _now() - timedelta(minutes=1)})
        self.assertEqual(self._status(self._join, "s3", new), (410, "code_expired"))
        groups.change_code(self.db, self.user["teacher"], g["id"], {"expires_at": None, "max_uses": 1})
        self._join("s3", new)  # the one allowed use
        self._fresh("late")
        self.assertEqual(self._status(self._join, "late", new), (409, "code_used_up"))
        # a removed student cannot come back with a code
        groups.update_member(self.db, self.user["teacher"], g["id"], self.ids["s2"], {"remove": True})
        newest = groups.regenerate_code(self.db, self.user["teacher"], g["id"])["code"]
        self.assertEqual(self._status(self._join, "s2", newest), (403, "removed_by_teacher"))
        # a closed group takes nobody
        groups.update(self.db, self.user["teacher"], g["id"], {"status": "paused"})
        self.assertEqual(self._status(self._join, "s3", newest), (409, "group_closed"))

    def test_wrong_codes_are_rate_limited(self):
        from app.services.study_groups import codes, groups

        guesser = self._fresh("guesser")
        for _ in range(codes.MAX_FAILED_JOINS_PER_USER):
            self.assertEqual(self._status(groups.join, self.db, guesser, "QQQQ-QQQQ", None)[1], "invalid_code")
        self.assertEqual(self._status(groups.join, self.db, guesser, "QQQQ-QQQQ", None), (429, "too_many_attempts"))

    # 4, 12: chat access
    def test_chat_permissions_moderation_and_unread(self):
        from app.services.study_groups import chat
        from app.services.study_groups.access import require_view

        g, code = self._group()
        self._join("s1", code)
        self._join("s2", code)
        self.assertEqual(self._status(require_view, self.db, self.user["outsider"], g["id"])[0], 404)
        self.assertEqual(self._status(require_view, self.db, self.user["teacher2"], g["id"])[0], 404)
        group, m1 = require_view(self.db, self.user["s1"], g["id"])
        msg = chat.post_message(self.db, self.user["s1"], group, m1, "<script>alert(1)</script> Hallo")
        self.assertEqual(msg["body"], "<script>alert(1)</script> Hallo")  # stored and returned as text; rendered as text
        self.assertEqual(self._status(chat.post_message, self.db, self.user["s1"], group, m1, "x" * 2001)[1], "too_long")
        group, m2 = require_view(self.db, self.user["s2"], g["id"])
        self.assertEqual(chat.list_messages(self.db, self.user["s2"], group, m2)["unread"], 1)  # "Hallo"; earlier ones predate s2
        chat.mark_read(self.db, m2)
        self.assertEqual(chat.list_messages(self.db, self.user["s2"], group, m2)["unread"], 0)
        # teacher-only chat: students read only
        chat.set_chat_mode(self.db, self.user["teacher"], g["id"], "teacher_only")
        group, m1 = require_view(self.db, self.user["s1"], g["id"])
        self.assertEqual(self._status(chat.post_message, self.db, self.user["s1"], group, m1, "hi")[1], "chat_read_only")
        chat.post_message(self.db, self.user["teacher"], group, None, "Nur ich")
        chat.set_chat_mode(self.db, self.user["teacher"], g["id"], "open")
        # moderation: only the group's teacher; the row stays, the text is hidden
        self.assertEqual(self._status(chat.moderate_message, self.db, self.user["teacher2"], g["id"], msg["id"], {"delete": True})[0], 404)
        self.assertEqual(self._status(chat.moderate_message, self.db, self.user["s2"], g["id"], msg["id"], {"delete": True})[0], 404)
        out = chat.moderate_message(self.db, self.user["teacher"], g["id"], msg["id"], {"delete": True, "reason": "spam"})
        self.assertTrue(out["deleted"] and out["body"] is None)
        # a muted student cannot write
        from app.services.study_groups import groups

        groups.update_member(self.db, self.user["teacher"], g["id"], self.ids["s1"], {"can_post": False})
        group, m1 = require_view(self.db, self.user["s1"], g["id"])
        self.assertEqual(self._status(chat.post_message, self.db, self.user["s1"], group, m1, "hi")[1], "chat_read_only")

    def test_announcements_and_notifications(self):
        from sqlalchemy import select

        from app.models.notification import Notification
        from app.services.study_groups import chat

        g, code = self._group()
        self._join("s1", code)
        self.assertEqual(self._status(chat.save_announcement, self.db, self.user["s1"], g["id"], {"title": "x", "body": "y"})[0], 404)
        a = chat.save_announcement(self.db, self.user["teacher"], g["id"], {"title": "Test morgen", "body": "Lektion 1-2", "is_pinned": True})
        links = list(self.db.scalars(select(Notification.link_path).where(Notification.user_id == self.ids["s1"])))
        self.assertIn(f"/groups/{g['id']}?tab=announcements", links)
        teacher_links = list(self.db.scalars(select(Notification.link_path).where(Notification.user_id == self.ids["teacher"])))
        self.assertIn(f"/teacher/groups/{g['id']}?tab=students", teacher_links)  # "student joined"
        chat.save_announcement(self.db, self.user["teacher"], g["id"], {"archived": True}, a["id"])
        from app.services.study_groups.access import require_view

        group, _ = require_view(self.db, self.user["s1"], g["id"])
        self.assertEqual(chat.list_announcements(self.db, self.user["s1"], group), [])

    # 5-7: monitoring from LMS data
    def test_tasks_dashboard_and_student_pages_use_lms_data(self):
        from app.models.student_progress import StudentProgress
        from app.services.study_groups import groups, progress
        from app.services.study_groups.access import require_manage

        g, code = self._group()
        a, b = self._fresh("pa"), self._fresh("pb")
        self._join("pa", code)
        self._join("pb", code)
        self.assertEqual(self._status(groups.save_task, self.db, self.user["teacher"], g["id"], {"lesson_id": self.b1_lesson_id})[1],
                         "lesson_not_in_group_courses")
        groups.save_task(self.db, self.user["teacher"], g["id"], {"lesson_id": self.lesson_ids[0], "due_at": _now() - timedelta(days=1)})
        groups.save_task(self.db, self.user["teacher"], g["id"], {"lesson_id": self.lesson_ids[1], "due_at": _now() + timedelta(days=3)})
        self.db.add(StudentProgress(user_id=str(a.id), lesson_id=str(self.lesson_ids[0]), lesson_completed=True,
                                    completed_at=_now() - timedelta(days=2), total_score=80, last_activity_at=_now()))
        self.db.commit()
        group = require_manage(self.db, self.user["teacher"], g["id"], write=False)
        d = progress.dashboard(self.db, group)
        self.assertEqual((d["students"], d["tasks"], d["lessons_total"]), (2, 2, 2))
        self.assertEqual(d["tasks_overdue"], 1)  # b missed lesson 1's deadline
        self.assertEqual(d["average_lesson_score"], 80)
        self.assertIsNone(d["average_grade"])  # nothing graded: no invented grade
        self.assertEqual(d["active_students"], 1)
        table = progress.students_table(self.db, group, "overdue")
        self.assertEqual([r["user_id"] for r in table["items"]], [b.id])
        detail = progress.student_detail(self.db, group, a.id)
        self.assertEqual([t["status"] for t in detail["tasks"]], ["completed", "not_started"])
        self.assertEqual(detail["lessons"][0]["status"], "completed")
        self.assertEqual(detail["summary"]["progress"], 50)
        board = progress.task_board(self.db, group)
        self.assertEqual(board["tasks"][0]["counts"], {"completed": 1, "overdue": 1})
        # nobody but the group's teacher (or an admin) sees this
        self.assertEqual(self._status(require_manage, self.db, self.user["teacher2"], g["id"], False)[0], 404)
        self.assertEqual(self._status(require_manage, self.db, b, g["id"], False)[0], 404)
        require_manage(self.db, self.user["admin"], g["id"], False)

    # 8: grading only through one's own group
    def test_group_teacher_grades_through_the_existing_service(self):
        from sqlalchemy import select

        from app.models.notification import Notification
        from app.models.student_writing import StudentWriting
        from app.services.student_writing import StudentWritingService

        g, code = self._group()
        student = self._fresh("writer")
        self._join("writer", code)
        sub = StudentWriting(user_id=str(student.id), writing_id=str(self.writing_id), answer_text="Liebe Anna, ...",
                             status="SUBMITTED", submitted_at=_now(), attempt_count=1)
        self.db.add(sub)
        self.db.commit()
        service = StudentWritingService(self.db)
        self.assertEqual(self._status(service.get_for_teacher, self.ids["teacher2"], sub.id)[0], 404)
        item = service.get_for_teacher(self.ids["teacher"], sub.id)
        self.assertEqual(item.answer_text, "Liebe Anna, ...")
        self.assertEqual(self._status(service.grade, self.ids["teacher2"], sub.id, 90, "gut", "GRADED")[0], 404)
        graded = service.grade(self.ids["teacher"], sub.id, 90, "Sehr gut", "GRADED")
        self.assertEqual((graded.status, graded.score), ("GRADED", 90))
        titles = list(self.db.scalars(select(Notification.title).where(Notification.user_id == student.id)))
        self.assertTrue(any("Brief" in t for t in titles))
        # once the student leaves the group the teacher no longer reaches the work
        from app.services.study_groups import groups

        groups.leave(self.db, student, g["id"])
        self.assertEqual(self._status(service.get_for_teacher, self.ids["teacher"], sub.id)[0], 404)

    def test_blocked_and_archived_groups(self):
        from app.services.study_groups import chat, groups
        from app.services.study_groups.access import require_view

        g, code = self._group()
        self._join("s1", code)
        self.assertEqual(self._status(groups.update, self.db, self.user["teacher"], g["id"], {"status": "blocked"})[0], 403)
        groups.update(self.db, self.user["admin"], g["id"], {"status": "blocked"})
        self.assertEqual(self._status(require_view, self.db, self.user["s1"], g["id"])[0], 404)
        self.assertEqual(self._status(groups.update, self.db, self.user["teacher"], g["id"], {"name": "neu"})[0], 409)
        groups.update(self.db, self.user["admin"], g["id"], {"status": "archived"})
        group, member = require_view(self.db, self.user["s1"], g["id"])
        self.assertFalse(chat.can_post(group, self.user["s1"], member))  # history readable, no new messages
        self.assertGreaterEqual(len(chat.list_messages(self.db, self.user["s1"], group, member)["items"]), 1)

    def test_admin_list_filters_and_stats(self):
        from app.services.study_groups import groups

        g, _ = self._group()
        res = groups.list_groups(self.db, self.user["admin"], "all", search=g["name"], level="A1", teacher_id=self.ids["teacher"])
        self.assertEqual([i["id"] for i in res["items"]], [g["id"]])
        self.assertTrue(res["items"][0]["code"]["usable"])
        self.assertNotIn("code_hash", res["items"][0]["code"])
        stats = groups.admin_stats(self.db, self.user["admin"])
        self.assertGreaterEqual(stats["groups"], 1)
        self.assertEqual(self._status(groups.admin_stats, self.db, self.user["teacher"])[0], 403)


if __name__ == "__main__":
    unittest.main()
