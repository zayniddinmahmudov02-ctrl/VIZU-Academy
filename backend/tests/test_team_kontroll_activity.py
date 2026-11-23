"""Team / Kontroll / activity tracking (overlay 22).

No DB: the credit rule, the dependencies every new route declares, anonymous 401.
PostgreSQL (VIZU_WB_TEST_DB_URL at head): heartbeat crediting (first beat 0, server clock, gap, idle, two tabs, paused media,
access, final, day change, duplicates, staff not tracked), the student's own Medien statistics, Team (create with hash +
must-change + profile, username login, unique names, weak passwords, Kontroll default Nein + audit, deactivate, reset,
groups / courses), Kontroll permission (dependency + HTTP 403 / 200 / 405, read only), the teacher roster scope (once per
student, other teacher's student 404), course progress and the timeline."""

import importlib.util
import os
import unittest
import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
HAS_HTTPX = importlib.util.find_spec("httpx") is not None
T0 = datetime(2026, 11, 23, 6, 0, tzinfo=timezone.utc)  # 11:00 in Tashkent


class TestCreditRule(unittest.TestCase):
    def test_server_clock_bounds(self):
        from app.services.activity.tracker import MAX_CREDIT, SESSION_GAP, credit

        self.assertEqual(credit(None, T0), 0)
        self.assertEqual(credit(T0, T0 + timedelta(seconds=30)), 30)
        self.assertEqual(credit(T0, T0 + timedelta(seconds=100)), MAX_CREDIT)
        self.assertEqual(credit(T0, T0 + timedelta(seconds=SESSION_GAP + 1)), 0)
        self.assertEqual(credit(T0, T0 - timedelta(seconds=5)), 0)

    def test_tashkent_day(self):
        from app.services.activity.tracker import local_day

        self.assertEqual(local_day(datetime(2026, 11, 23, 19, 30, tzinfo=timezone.utc)), date(2026, 11, 24))


class TestContract(unittest.TestCase):
    def _deps(self, router):
        return {(r.path, tuple(sorted(r.methods))): [d.call for d in r.dependant.dependencies] for r in router.routes}

    def test_every_route_states_its_dependency(self):
        from app.api.activity.router import router as activity
        from app.api.admin.team_router import router as team
        from app.api.dependencies.auth import get_current_user, require_student_control, require_super_admin, require_teacher_panel_access
        from app.api.teacher.panel_router import kontroll_router, router as panel

        for key, deps in self._deps(team).items():
            self.assertIn(require_super_admin, deps, key)
        for key, deps in self._deps(panel).items():
            self.assertIn(require_teacher_panel_access, deps, key)
        for key, deps in self._deps(kontroll_router).items():
            self.assertIn(require_student_control, deps, key)
            self.assertEqual(key[1], ("GET",), f"Kontroll is read only: {key}")
        for key, deps in self._deps(activity).items():
            self.assertIn(get_current_user, deps, key)

    @unittest.skipUnless(HAS_HTTPX, "needs httpx (TestClient)")
    def test_anonymous_401(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        for method, path in (("get", "/api/v1/admin/team/overview"), ("post", "/api/v1/admin/team/teachers"), ("get", "/api/v1/teacher/dashboard"),
                             ("get", "/api/v1/teacher/roster"), ("get", "/api/v1/teacher/kontroll/students"), ("get", "/api/v1/medien/stats"),
                             ("post", "/api/v1/activity/heartbeat")):
            self.assertEqual(getattr(client, method)(path).status_code, 401, path)


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.models.course import Course
        from app.models.language import Language
        from app.models.lesson import Lesson
        from app.models.medien import Film, MediaBook, Song
        from app.models.module import Module

        cls.Session = sessionmaker(bind=create_engine(DB_URL))
        db = cls.Session()
        tag = cls.tag = uuid.uuid4().hex[:6]
        lang = Language(code=f"k{tag}", locale=f"k-{tag}", name=f"Kontroll {tag}")
        db.add(lang)
        db.flush()
        course = Course(language_id=lang.id, level="A2", title=f"A2 kontroll {tag}", order_index=1, is_active=True)
        db.add(course)
        db.flush()
        module = Module(course_id=course.id, number=1, title="Modul", order_index=1, is_active=True)
        db.add(module)
        db.flush()
        lessons = [Lesson(module_id=module.id, number=n, title=f"Lektion {n}", duration=10, is_published=True) for n in (1, 2, 3, 4)]
        song = Song(title=f"Lied {tag}", artist="Band", status="PUBLISHED", access_type="FREE", duration_ms=200_000)
        hidden = Song(title=f"Entwurf {tag}", status="DRAFT", access_type="FREE", duration_ms=200_000)
        paid_film = Film(title=f"Film {tag}", status="PUBLISHED", access_type="PAID", price=10000, video_duration_ms=3_600_000)
        free_film = Film(title=f"Freier Film {tag}", status="PUBLISHED", access_type="FREE", video_duration_ms=3_600_000)
        book = MediaBook(title=f"Buch {tag}", status="PUBLISHED", access_type="FREE", page_count=50)
        db.add_all([*lessons, song, hidden, paid_film, free_film, book])
        db.commit()
        cls.course_id, cls.lesson_ids = course.id, [lesson.id for lesson in lessons]
        cls.song_id, cls.hidden_id, cls.paid_film_id, cls.film_id, cls.book_id = song.id, hidden.id, paid_film.id, free_film.id, book.id
        db.close()

    def setUp(self):
        self.db = self.Session()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def _user(self, role="STUDENT", **extra):
        from app.models.user import User

        u = User(email=f"k-{uuid.uuid4().hex[:10]}@test.local", username=f"k_{uuid.uuid4().hex[:10]}", password_hash="x", is_active=True,
                 is_verified=True, is_superuser=False, role=role, is_banned=False, preferred_language="uz", first_name="Kontroll", **extra)
        self.db.add(u)
        self.db.commit()
        return u

    def _beat(self, user, at, tab="tab-aaaaaa", active=True, contexts=(), final=False):
        from app.services.activity import tracker

        return tracker.heartbeat(self.db, user, tab_id=tab, active=active, contexts=list(contexts), final=final, now=at)["credited"]

    def _session_seconds(self, user):
        from sqlalchemy import func, select

        from app.models.student_activity import StudentSession

        self.db.expire_all()
        return self.db.scalar(select(func.coalesce(func.sum(StudentSession.active_seconds), 0)).where(StudentSession.user_id == user.id))

    def _area_seconds(self, user, area):
        from sqlalchemy import func, select

        from app.models.student_activity import StudentActivityEvent

        self.db.expire_all()
        return self.db.scalar(select(func.coalesce(func.sum(StudentActivityEvent.seconds), 0)).where(
            StudentActivityEvent.user_id == user.id, StudentActivityEvent.area == area))

    # ---------------- tracker ----------------

    def test_session_time_is_measured_by_the_server(self):
        s = self._user()
        self.assertEqual(self._beat(s, T0), 0)  # the first heartbeat proves nothing yet
        self.assertEqual(self._beat(s, T0 + timedelta(seconds=30)), 30)
        self.assertEqual(self._beat(s, T0 + timedelta(seconds=60)), 30)
        self.assertEqual(self._beat(s, T0 + timedelta(seconds=60 + 400)), 0)  # long pause: new session, nothing for the pause
        self.assertEqual(self._beat(s, T0 + timedelta(seconds=490)), 30)
        self.assertEqual(self._session_seconds(s), 90)

    def test_two_tabs_never_count_twice_and_duplicates_are_dropped(self):
        s = self._user()
        for i in range(5):
            at = T0 + timedelta(seconds=30 * i)
            self._beat(s, at, tab="tab-one111")
            self._beat(s, at + timedelta(seconds=4), tab="tab-two222")
            self._beat(s, at + timedelta(seconds=5), tab="tab-two222")  # same tab again within 3 s: dropped
        self.assertLessEqual(self._session_seconds(s), 4 * 30 + 4)
        self.assertGreaterEqual(self._session_seconds(s), 4 * 30)

    def test_idle_page_counts_nothing(self):
        from app.models.student_activity import AREA_COURSE

        s = self._user()
        ctx = [{"area": AREA_COURSE, "ref_id": self.lesson_ids[0], "position": None}]
        self._beat(s, T0, active=False, contexts=ctx)
        self._beat(s, T0 + timedelta(seconds=30), active=False, contexts=ctx)
        self.assertEqual(self._session_seconds(s), 0)
        self.assertEqual(self._area_seconds(s, AREA_COURSE), 0)

    def test_music_counts_only_while_playing(self):
        from app.models.student_activity import AREA_MUSIC

        s = self._user()
        play = lambda pos: [{"area": AREA_MUSIC, "ref_id": self.song_id, "position": pos}]  # noqa: E731
        self._beat(s, T0, active=False, contexts=play(10))
        self._beat(s, T0 + timedelta(seconds=30), active=False, contexts=play(40))  # playing in a hidden tab: counts
        self._beat(s, T0 + timedelta(seconds=60), active=False, contexts=play(40))  # paused: nothing
        self.assertEqual(self._area_seconds(s, AREA_MUSIC), 30)
        self.assertEqual(self._session_seconds(s), 30)
        self._beat(s, T0 + timedelta(seconds=90), active=False, contexts=[{"area": AREA_MUSIC, "ref_id": self.song_id, "position": 5000}])
        self.assertEqual(self._area_seconds(s, AREA_MUSIC), 30, "a position behind the song's end is refused")

    def test_no_access_no_credit(self):
        from app.models.student_activity import AREA_FILM, AREA_MUSIC

        s = self._user()
        for i, pos in enumerate((0, 30, 60)):
            self._beat(s, T0 + timedelta(seconds=30 * i), contexts=[{"area": AREA_FILM, "ref_id": self.paid_film_id, "position": pos},
                                                                    {"area": AREA_MUSIC, "ref_id": self.hidden_id, "position": pos}])
        self.assertEqual(self._area_seconds(s, AREA_FILM), 0)
        self.assertEqual(self._area_seconds(s, AREA_MUSIC), 0)
        for i, pos in enumerate((0, 30, 60)):
            self._beat(s, T0 + timedelta(seconds=600 + 30 * i), contexts=[{"area": AREA_FILM, "ref_id": self.film_id, "position": pos}])
        self.assertEqual(self._area_seconds(s, AREA_FILM), 60)

    def test_final_ends_the_session_and_a_new_day_starts_a_new_one(self):
        from sqlalchemy import select

        from app.models.student_activity import StudentSession

        s = self._user()
        night = datetime(2026, 11, 23, 18, 59, 30, tzinfo=timezone.utc)  # 23:59:30 Tashkent
        self._beat(s, night, tab="tab-night1")
        self._beat(s, night + timedelta(seconds=40), tab="tab-night1")  # 00:00:10 next day: new session
        self._beat(s, night + timedelta(seconds=70), tab="tab-night1", final=True)
        self.db.expire_all()
        rows = list(self.db.scalars(select(StudentSession).where(StudentSession.user_id == s.id).order_by(StudentSession.started_at)))
        self.assertEqual([r.day for r in rows], [date(2026, 11, 23), date(2026, 11, 24)])
        self.assertTrue(all(r.ended_at is not None for r in rows))
        self.assertEqual(rows[1].active_seconds, 30)

    def test_staff_is_not_tracked(self):
        t = self._user("TEACHER")
        self._beat(t, T0)
        self._beat(t, T0 + timedelta(seconds=30))
        self.assertEqual(self._session_seconds(t), 0)

    def test_own_media_statistics(self):
        from app.models.medien import MediaPlayHistory, MediaProgress
        from app.models.student_activity import AREA_BOOK, AREA_MUSIC
        from app.services.activity import stats

        s = self._user()
        self.db.add_all([MediaPlayHistory(user_id=s.id, song_id=self.song_id), MediaPlayHistory(user_id=s.id, song_id=self.song_id),
                         MediaPlayHistory(user_id=s.id, song_id=self.hidden_id),
                         MediaProgress(user_id=s.id, content_type="BOOK", content_id=self.book_id, position=3, total=50, last_opened_at=T0)])
        self.db.commit()
        for i in range(3):
            at = T0 + timedelta(seconds=30 * i)
            self._beat(s, at, contexts=[{"area": AREA_MUSIC, "ref_id": self.song_id, "position": 30 * i},
                                        {"area": AREA_BOOK, "ref_id": self.book_id, "position": None}])
        data = stats.media_overview(self.db, s, now=T0 + timedelta(minutes=2))
        self.assertEqual(data["music"]["songs_listened"], 1, "a draft song is not in the student's own list")
        self.assertEqual(data["music"]["play_count"], 2)
        self.assertEqual(data["music"]["listened_seconds"], 60)
        self.assertEqual(data["books"]["books_opened"], 1)
        self.assertEqual(data["books"]["books_completed"], 0, "opening is not reading the book")
        self.assertEqual(data["books"]["recent"][0]["page"], 3)
        self.assertEqual(data["books"]["reading_seconds"], 60)
        self.assertEqual(data["films"]["films_watched"], 0)
        self.assertEqual(data["media_seconds"], 120)
        self.assertEqual(sum(d["MUSIC"] for d in data["daily"]), 60)

    # ---------------- Team ----------------

    def _admin(self):
        return self._user("SUPER_ADMIN")

    def _create(self, admin, **extra):
        from app.services.teacher import team

        data = {"full_name": "Lehrerin Test", "username": f"teacher_{uuid.uuid4().hex[:6]}", **extra}
        return team.create(self.db, admin, data, "127.0.0.1")

    def test_create_teacher_hash_profile_and_username_login(self):
        from sqlalchemy import select

        from app.core.security import verify_password
        from app.models.audit_log import AuditLog
        from app.models.teacher_profile import TeacherProfile
        from app.models.user import User
        from app.services.auth.service import authenticate_user

        admin = self._admin()
        teacher, password = self._create(admin)
        user = self.db.get(User, teacher["id"])
        self.assertEqual(user.role, "TEACHER")
        self.assertTrue(user.must_change_password)
        self.assertNotIn(password, user.password_hash)
        self.assertTrue(verify_password(password, user.password_hash))
        self.assertGreaterEqual(len(password), 14)
        self.assertIsNone(teacher["email"], "no e-mail given: an internal placeholder, not shown")
        profile = self.db.scalar(select(TeacherProfile).where(TeacherProfile.user_id == user.id))
        self.assertFalse(profile.can_access_student_control, "Kontroll default: Nein")
        self.assertEqual(authenticate_user(self.db, user.username.upper(), password).id, user.id)
        audit = self.db.scalar(select(AuditLog).where(AuditLog.target_user_id == user.id, AuditLog.action == "team_teacher_created"))
        self.assertNotIn(password, audit.details)
        student = self._user()
        student.password_hash = user.password_hash
        self.db.commit()
        self.assertIsNone(authenticate_user(self.db, student.username, password), "a student never logs in with the username")

    def test_create_refuses_duplicates_and_weak_passwords(self):
        admin = self._admin()
        teacher, _p = self._create(admin, email=f"lehrer-{uuid.uuid4().hex[:6]}@schule.uz")
        for extra, code in (({"username": teacher["username"]}, 409), ({"username": teacher["username"].upper()}, 409),
                            ({"email": teacher["email"]}, 409), ({"password": "kurz1"}, 422), ({"password": "nurbuchstaben"}, 422),
                            ({"username": "a b"}, 422), ({"email": "x@team.vizu-deutsch.com"}, 422)):
            with self.assertRaises(HTTPException) as ctx:
                self._create(admin, **extra)
            self.assertEqual(ctx.exception.status_code, code, extra)
        own, password = self._create(admin, password="Sicher2026x", can_access_student_control=True)
        self.assertEqual(password, "Sicher2026x")
        self.assertTrue(own["can_access_student_control"])

    def test_control_status_reset_with_audit(self):
        from sqlalchemy import select

        from app.models.audit_log import AuditLog
        from app.models.user import User
        from app.services.teacher import team

        admin = self._admin()
        teacher, _p = self._create(admin)
        tid = teacher["id"]
        self.assertTrue(team.set_control(self.db, admin, tid, True, None)["can_access_student_control"])
        self.assertTrue(team.can_access_control(self.db, self.db.get(User, tid)))
        team.set_control(self.db, admin, tid, True, None)  # no change -> no second row
        self.assertFalse(team.set_control(self.db, admin, tid, False, None)["can_access_student_control"])
        actions = [r.details for r in self.db.scalars(select(AuditLog).where(AuditLog.target_user_id == tid, AuditLog.action == "team_control_changed")
                                                      .order_by(AuditLog.created_at))]
        self.assertEqual(actions, ["kontroll: Nein → Ja", "kontroll: Ja → Nein"])
        self.assertEqual(team.set_status(self.db, admin, tid, False, None)["status"], "inactive")
        self.assertIsNotNone(self.db.get(User, tid).tokens_valid_after)
        detail, new_password = team.reset_password(self.db, admin, tid, None, None)
        self.assertTrue(detail["must_change_password"])
        self.assertTrue(len(detail["history"]) >= 4)
        with self.assertRaises(HTTPException) as ctx:
            team.set_control(self.db, admin, self._user().id, True, None)
        self.assertEqual(ctx.exception.status_code, 404, "only teacher accounts")

    def test_groups_and_courses(self):
        from app.models.study_group import StudyGroup
        from app.services.study_groups import groups
        from app.services.teacher import team

        admin = self._admin()
        teacher, _p = self._create(admin)
        group, _code = groups.create(self.db, admin, {"name": f"Team {uuid.uuid4().hex[:4]}", "level": "A2", "course_ids": [self.course_id]})
        detail = team.assign_group(self.db, admin, teacher["id"], group["id"], None)
        self.assertEqual([g["id"] for g in detail["groups"]], [group["id"]])
        detail = team.assign_course(self.db, admin, teacher["id"], self.course_id, None)
        self.assertEqual([c["course_id"] for c in detail["courses"]], [self.course_id])
        detail = team.remove_group(self.db, admin, teacher["id"], group["id"], None)
        self.assertEqual(detail["groups"], [])
        self.assertEqual(self.db.get(StudyGroup, group["id"]).teacher_id, admin.id, "the group goes back to the administrator")
        self.assertEqual(team.remove_course(self.db, admin, teacher["id"], self.course_id, None)["courses"], [])

    # ---------------- permissions ----------------

    def test_kontroll_dependency(self):
        from app.api.dependencies.auth import require_student_control
        from app.services.teacher import team

        admin = self._admin()
        teacher, _p = self._create(admin)
        from app.models.user import User

        user = self.db.get(User, teacher["id"])
        team.set_control(self.db, admin, user.id, True, None)
        with self.assertRaises(HTTPException) as ctx:
            require_student_control(user, self.db)
        self.assertEqual(ctx.exception.detail, "PASSWORD_CHANGE_REQUIRED", "the own password comes first")
        user.must_change_password = False
        self.db.commit()
        team.set_control(self.db, admin, user.id, False, None)
        with self.assertRaises(HTTPException) as ctx:
            require_student_control(user, self.db)
        self.assertEqual((ctx.exception.status_code, ctx.exception.detail), (403, "KONTROLL_ACCESS_REQUIRED"))
        with self.assertRaises(HTTPException) as ctx:
            require_student_control(self._user(), self.db)
        self.assertEqual(ctx.exception.status_code, 403, "a student never")
        team.set_control(self.db, admin, user.id, True, None)
        self.assertEqual(require_student_control(user, self.db).id, user.id)
        self.assertEqual(require_student_control(admin, self.db).id, admin.id)

    @unittest.skipUnless(HAS_HTTPX, "needs httpx (TestClient)")
    def test_http_permissions(self):
        from fastapi.testclient import TestClient

        from app.core.security import create_user_token
        from app.main import app
        from app.models.user import User
        from app.services.teacher import team

        client = TestClient(app)
        admin = self._admin()
        teacher, _p = self._create(admin)
        tuser = self.db.get(User, teacher["id"])
        auth = lambda u: {"Authorization": f"Bearer {create_user_token(u)}"}  # noqa: E731
        r = client.get("/api/v1/teacher/dashboard", headers=auth(tuser))
        self.assertEqual((r.status_code, r.json().get("message")), (403, "PASSWORD_CHANGE_REQUIRED"))
        tuser.must_change_password = False
        self.db.commit()
        self.assertEqual(client.get("/api/v1/teacher/dashboard", headers=auth(tuser)).status_code, 200)
        self.assertEqual(client.get("/api/v1/teacher/kontroll/students", headers=auth(tuser)).status_code, 403)
        self.assertEqual(client.get("/api/v1/admin/team/overview", headers=auth(tuser)).status_code, 403)
        self.assertEqual(client.put(f"/api/v1/admin/team/teachers/{tuser.id}/control", json={"enabled": True}, headers=auth(tuser)).status_code, 403,
                         "a teacher never changes a permission")
        team.set_control(self.db, admin, tuser.id, True, None)
        r = client.get("/api/v1/teacher/kontroll/students?page_size=5", headers=auth(tuser))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["cache-control"], "private, no-store")
        student = self._user()
        self.assertEqual(client.get(f"/api/v1/teacher/kontroll/students/{student.id}", headers=auth(tuser)).status_code, 200)
        self.assertEqual(client.get(f"/api/v1/teacher/kontroll/students/{admin.id}", headers=auth(tuser)).status_code, 404, "staff are not students")
        for method in ("post", "put", "patch", "delete"):
            self.assertEqual(getattr(client, method)(f"/api/v1/teacher/kontroll/students/{student.id}", headers=auth(tuser)).status_code, 405)
        self.assertEqual(client.get("/api/v1/teacher/kontroll/students", headers=auth(student)).status_code, 403)
        self.assertEqual(client.get("/api/v1/medien/stats", headers=auth(student)).status_code, 200)
        created = client.post("/api/v1/admin/team/teachers", json={"full_name": "Neu Lehrer", "username": f"neu_{uuid.uuid4().hex[:6]}"},
                              headers=auth(admin))
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.headers["cache-control"], "private, no-store")
        self.assertTrue(created.json()["temporary_password"])

    # ---------------- teacher scope / progress / timeline ----------------

    def test_roster_scope_and_profile_idor(self):
        from app.models.study_group import MEMBER_ACTIVE, MEMBER_STUDENT, StudyGroupMember
        from app.services.study_groups import groups
        from app.services.teacher import panel

        admin = self._admin()
        a, b = self._user("TEACHER"), self._user("TEACHER")
        s1, s2, other = self._user(), self._user(), self._user()
        ga1, _ = groups.create(self.db, admin, {"name": f"A1 {uuid.uuid4().hex[:4]}", "level": "A2", "teacher_id": a.id})
        ga2, _ = groups.create(self.db, admin, {"name": f"A2 {uuid.uuid4().hex[:4]}", "level": "A2", "teacher_id": a.id})
        gb, _ = groups.create(self.db, admin, {"name": f"B {uuid.uuid4().hex[:4]}", "level": "A2", "teacher_id": b.id})
        now = datetime.now(timezone.utc)
        for gid, uid in ((ga1["id"], s1.id), (ga2["id"], s1.id), (ga2["id"], s2.id), (gb["id"], other.id)):
            self.db.add(StudyGroupMember(group_id=gid, user_id=uid, role=MEMBER_STUDENT, status=MEMBER_ACTIVE, joined_at=now))
        self.db.commit()
        roster = panel.students(self.db, a)
        self.assertEqual(sorted(r["id"] for r in roster["items"]), sorted([s1.id, s2.id]))
        row = next(r for r in roster["items"] if r["id"] == s1.id)
        self.assertEqual(len(row["groups"]), 2, "one row, both groups listed")
        self.assertEqual(panel.students(self.db, a, group_id=ga1["id"])["total"], 1)
        self.assertEqual(panel.student_profile(self.db, a, s1.id)["student"]["id"], s1.id)
        with self.assertRaises(HTTPException) as ctx:
            panel.student_profile(self.db, a, other.id)
        self.assertEqual(ctx.exception.status_code, 404)
        dash = panel.dashboard(self.db, a)
        self.assertEqual((dash["stats"]["students"], dash["stats"]["groups"]), (2, 2))
        empty = panel.dashboard(self.db, self._user("TEACHER"))
        self.assertEqual((empty["stats"]["students"], empty["has_groups"]), (0, False))

    def test_course_progress_and_timeline(self):
        from app.models.course import Course
        from app.models.lesson import Lesson
        from app.models.student_activity import AREA_COURSE, AREA_WORTSCHATZ
        from app.models.student_progress import StudentProgress
        from app.services.activity import stats

        s = self._user()
        for lid in self.lesson_ids[:3]:
            self.db.add(StudentProgress(user_id=s.id, lesson_id=lid, lesson_completed=lid != self.lesson_ids[2]))
        self.db.commit()
        structure = {"A2": (self.db.get(Course, self.course_id), [self.db.get(Lesson, lid) for lid in self.lesson_ids])}
        self._beat(s, T0, contexts=[{"area": AREA_COURSE, "ref_id": self.lesson_ids[2], "position": None}])
        self._beat(s, T0 + timedelta(seconds=30), contexts=[{"area": AREA_COURSE, "ref_id": self.lesson_ids[2], "position": None}])
        self._beat(s, T0 + timedelta(seconds=60), contexts=[{"area": AREA_WORTSCHATZ, "ref_id": None, "position": None}])
        self._beat(s, T0 + timedelta(seconds=90), contexts=[{"area": AREA_WORTSCHATZ, "ref_id": None, "position": None}])
        [course] = stats.courses(self.db, s.id, structure)
        self.assertEqual((course["lessons_completed"], course["lessons_total"], course["percent"]), (2, 4, 50))
        self.assertEqual(course["seconds"], 30)
        self.assertEqual(stats.completed_counts(self.db, [s.id], structure)[s.id], (2, 0))
        tl = stats.timeline(self.db, s.id)
        self.assertEqual(tl["day"], "2026-11-23")
        self.assertEqual([(i["time"], i["area"], i["seconds"]) for i in tl["items"]], [("11:00", "COURSE", 30), ("11:01", "WORTSCHATZ", 30)])
        self.assertEqual(tl["items"][0]["title"], "A2 Kurs — Lektion 3")
        listing = stats.kontroll_list(self.db, search=s.username, page_size=5)
        self.assertEqual(listing["total"], 1)
        self.assertEqual(listing["items"][0]["usage_seconds"], 90)
        self.assertEqual(listing["items"][0]["vocabulary_seconds"], 30)
        detail = stats.kontroll_detail(self.db, s.id, now=T0 + timedelta(minutes=5))
        self.assertEqual((detail["general"]["total_seconds"], detail["general"]["today_seconds"], detail["general"]["active_days"]), (90, 90, 1))
        self.assertEqual(detail["vocabulary"]["seconds"], 30)

    def test_library_script_plan_apply(self):
        import tempfile
        from pathlib import Path

        from sqlalchemy import select

        from app.models.medien import MediaBook, MediaCategory
        from app.scripts import medien_library_categories as script

        exam = self.db.scalar(select(MediaCategory).where(MediaCategory.kind == "BOOK", MediaCategory.slug == "pruefungsvorbereitung"))
        verbs = MediaBook(title="Starke Verben - Kuchli Fe`llar", status="DRAFT", access_type="FREE", category_id=exam.id)
        loose = MediaBook(title=f"Ohne Kategorie {uuid.uuid4().hex[:6]}", status="DRAFT", access_type="FREE")
        self.db.add_all([verbs, loose])
        self.db.commit()
        plan = script.build_plan(self.db)
        mine = {i["book_id"]: i for i in plan["items"] if i["book_id"] in (str(verbs.id), str(loose.id))}
        self.assertEqual((mine[str(verbs.id)]["to"], mine[str(verbs.id)]["change"]), ("Wortschatz", True))
        self.assertEqual(mine[str(loose.id)]["to"], "Sonstige")
        with self.assertRaises(RuntimeError):
            script.apply_plan(self.db, "000000000000", Path(tempfile.mkdtemp()))
        out = script.apply_plan(self.db, plan["plan_id"], Path(tempfile.mkdtemp()))
        self.assertTrue(Path(out["backup"]).exists())
        self.db.expire_all()
        self.assertEqual(self.db.get(MediaCategory, self.db.get(MediaBook, verbs.id).category_id).slug, "wortschatz")
        again = script.build_plan(self.db)
        self.assertFalse(any(i["change"] for i in again["items"]), "a second run changes nothing")
        self.db.delete(self.db.get(MediaBook, verbs.id))
        self.db.delete(self.db.get(MediaBook, loose.id))
        self.db.commit()

    def test_library_has_the_six_categories(self):
        from sqlalchemy import select

        from app.models.medien import MediaCategory

        names = [c.name for c in self.db.scalars(select(MediaCategory).where(MediaCategory.kind == "BOOK", MediaCategory.is_active.is_(True))
                                                 .order_by(MediaCategory.sort_order))]
        wanted = ["Literatur", "Historisch", "Beruflich", "Sonstige", "Prüfungsvorbereitung", "Wortschatz"]
        self.assertEqual([n for n in names if n in wanted], wanted)
        self.assertFalse({"Grammatik", "Zertifikatsbücher", "Lektüren", "Sonstige Bücher"} & set(names))


if __name__ == "__main__":
    unittest.main()
