"""My Teacher marketplace.

No DB: every route states its dependency (students / teachers / admin read / admin write), anonymous 401, the 9:16 crop, the
certificate PDF check, the derived course status.
PostgreSQL (VIZU_WB_TEST_DB_URL at head): catalog visibility + search + filters + card fields, profile edit and student numbers
(each student once), course life cycle (draft invisible, approval, study group, free enrollment, duplicate / full refused,
sensitive edit → review again, other teacher 404), paid course through VIZU Pay (pending order holds the place, approval
activates, refund ends it, rejection frees the place), reviews (only after a real enrollment and the course start, once per
course, author shown as short name, rating recomputed, hidden reviews leave the rating), special lessons (pending invisible,
approval announces, 15-minute open window, students join muted and without camera, the teacher grants mic / camera, a student
cannot moderate, the server closes the room at the time limit and ends the lesson). LiveKit is a fake gateway."""

import asyncio
import importlib.util
import os
import unittest
import uuid
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import HTTPException

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
HAS_HTTPX = importlib.util.find_spec("httpx") is not None
LK = {"LIVEKIT_URL": "ws://127.0.0.1:7880", "LIVEKIT_API_URL": "", "LIVEKIT_API_KEY": "vizutestkey",
      "LIVEKIT_API_SECRET": "vizu-test-secret-not-real-0123456789abcdef"}


class TestContract(unittest.TestCase):
    def test_every_route_states_its_dependency(self):
        from app.api.dependencies.auth import get_current_user, require_admin_panel_access, require_super_admin, require_teacher_panel_access
        from app.api.teacher_market.router import admin_router, router, special_router, teacher_router

        for r in [*router.routes, *special_router.routes]:
            self.assertIn(get_current_user, [d.call for d in r.dependant.dependencies], r.path)
        for r in teacher_router.routes:
            self.assertIn(require_teacher_panel_access, [d.call for d in r.dependant.dependencies], r.path)
        for r in admin_router.routes:
            deps = [d.call for d in r.dependant.dependencies]
            self.assertIn(require_admin_panel_access if r.methods == {"GET"} else require_super_admin, deps, f"{r.methods} {r.path}")

    def test_no_route_writes_a_rating(self):
        from app.api.teacher_market.router import ProfileIn, teacher_router

        self.assertFalse({"rating_avg", "rating_count", "verified", "catalog_hidden"} & set(ProfileIn.model_fields))
        self.assertFalse([r.path for r in teacher_router.routes if "rating" in r.path])

    @unittest.skipUnless(HAS_HTTPX, "needs httpx (TestClient)")
    def test_anonymous_401(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        for method, path in (("get", "/api/v1/my-teacher/teachers"), ("get", f"/api/v1/my-teacher/teachers/{uuid.uuid4()}"),
                             ("post", f"/api/v1/my-teacher/courses/{uuid.uuid4()}/enroll"), ("get", "/api/v1/special-lessons/board"),
                             ("get", "/api/v1/teacher/market/profile"), ("post", "/api/v1/teacher/market/courses"),
                             ("get", "/api/v1/admin/teacher-market/overview"), ("put", "/api/v1/admin/teacher-market/settings"),
                             ("post", f"/api/v1/video-rooms/{uuid.uuid4()}/camera-permission")):
            self.assertEqual(getattr(client, method)(path).status_code, 401, path)

    def test_crop_keeps_the_ratio_inside_the_image(self):
        from app.services.teacher_market.media import crop_box

        for w, h in ((1000, 1000), (3000, 1000), (800, 2400)):
            left, top, right, bottom = crop_box(w, h, 9 / 16, None, None, None)
            self.assertAlmostEqual((right - left) / (bottom - top), 9 / 16, delta=0.01)
            self.assertTrue(0 <= left and right <= w and 0 <= top and bottom <= h)
        left, top, right, bottom = crop_box(2000, 2000, 16 / 9, 0.9, 0.9, 0.5)
        self.assertTrue(right <= 2000 and bottom <= 2000)

    def test_crop_fractions_tolerate_float_noise_only(self):
        # a 1000 x 1500 image at 9:16 gives h = 1.0000000000000002 in the browser, so y = (1 - h) / 2 is a tiny negative number
        from app.api.teacher_market.router import _crop

        self.assertEqual(_crop(0.078125, -1.1102230246251565e-16, 0.84375), (0.078125, 0.0, 0.84375))
        self.assertEqual(_crop(1.0000000000000002, 0.5, None), (1.0, 0.5, None))
        for bad in (-0.1, 1.2, float("nan"), float("inf")):
            with self.assertRaises(HTTPException) as e:
                _crop(bad, 0.0, 0.5)
            self.assertEqual(e.exception.detail, "CROP_INVALID")

    def test_certificate_pdf_must_be_a_pdf(self):
        from app.services.teacher_market.media import save_certificate

        with self.assertRaises(HTTPException) as e:
            save_certificate(b"<html>not a pdf</html>", "zertifikat.pdf", "application/pdf")
        self.assertEqual(e.exception.detail, "PDF_INVALID")

    def test_derived_course_status(self):
        from app.models.teacher_market import TeacherCourse
        from app.services.teacher_market.courses import effective_status

        today = date(2026, 12, 1)
        course = TeacherCourse(status="ANMELDUNG", course_type="PAID", max_students=2, start_date=date(2026, 12, 10))
        self.assertEqual(effective_status(course, 1, today), "ANMELDUNG")
        self.assertEqual(effective_status(course, 2, today), "AUSGEBUCHT")
        course.enrollment_deadline = date(2026, 11, 30)
        self.assertEqual(effective_status(course, 0, today), "VORBEREITUNG")
        course.start_date = date(2026, 11, 20)
        self.assertEqual(effective_status(course, 0, today), "LAUFEND")


class FakeGateway:
    def __init__(self):
        self.calls = []

    def _rec(self, *call):
        self.calls.append(call)

    def ensure_room(self, name, max_participants, metadata):
        self._rec("ensure", name, max_participants, metadata)

    def set_room_metadata(self, name, metadata):
        self._rec("meta", name, metadata)
        return True

    def delete_room(self, name):
        self._rec("delete", name)
        return True

    def participants(self, name):
        return []

    def update_permission(self, name, identity, sources, can_data):
        self._rec("perm", name, identity, tuple(sources), can_data)
        return True

    def set_attributes(self, name, identity, attributes):
        return True

    def mute(self, name, identities, sources=("microphone",)):
        self._rec("mute", name, tuple(sorted(identities)), tuple(sources))
        return len(identities)

    def remove(self, name, identity):
        return True

    def status(self):
        return "available"


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        cls.Session = sessionmaker(bind=create_engine(DB_URL))

    def setUp(self):
        from app.core.config import settings
        from app.services.video_rooms import livekit_service as lk

        self.db = self.Session()
        self.tag = uuid.uuid4().hex[:6]
        self.fake = FakeGateway()
        self._patches = [patch.object(lk, "gateway", self.fake), patch.multiple(settings, **LK)]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        self.db.rollback()
        self.db.close()

    # ---------- helpers ----------

    def _user(self, role="STUDENT", first="Max", last="Muster", **extra):
        from app.models.user import User

        u = User(email=f"tm-{uuid.uuid4().hex[:10]}@test.local", username=f"tm_{uuid.uuid4().hex[:10]}", password_hash="x", is_active=True,
                 is_verified=True, is_superuser=False, role=role, is_banned=False, preferred_language="uz", first_name=first, last_name=last, **extra)
        self.db.add(u)
        self.db.commit()
        return u

    def _teacher(self, first=None):
        return self._user("TEACHER", first=first or f"Lehrer{self.tag}", last="Schmidt")

    def _course(self, teacher, admin, **data):
        from app.services.teacher_market import courses

        body = {"title": f"Kurs {self.tag}", "level": "A2", "course_type": "FREE", "status": "ANMELDUNG", "max_students": 2,
                "start_date": (date.today() + timedelta(days=7)).isoformat()}
        body.update(data)
        c = courses.create(self.db, teacher, body)
        courses.submit(self.db, teacher, c["id"])
        return courses.admin_review(self.db, admin, c["id"], "approve", None, None)

    def _err(self, fn, *args, **kwargs) -> HTTPException:
        with self.assertRaises(HTTPException) as e:
            fn(*args, **kwargs)
        self.db.rollback()
        return e.exception

    # ---------- catalog / profile ----------

    def test_catalog_visibility_search_and_card(self):
        from app.services.teacher_market import profiles

        admin = self._user("SUPER_ADMIN")
        t1, t2, t3 = self._teacher(f"Anna{self.tag}"), self._teacher(f"Bert{self.tag}"), self._teacher(f"Cleo{self.tag}")
        profiles.update_own(self.db, t1, {"languages": ["Deutsch", "Usbekisch"], "levels": ["A1", "A2"], "headline": "DaF"})
        profiles.admin_update_teacher(self.db, admin, t2.id, {"catalog_hidden": True}, None)
        profiles.admin_update_teacher(self.db, admin, t3.id, {"profile_disabled": True}, None)
        res = profiles.catalog(self.db, self.tag, None, None, None, None, 1, 48)
        ids = {i["id"] for i in res["items"]}
        self.assertIn(t1.id, ids)
        self.assertNotIn(t2.id, ids)
        self.assertNotIn(t3.id, ids)
        self.assertEqual(set(res["items"][0]), {"id", "name", "photo_url"})  # the card shows photo + name only
        self.assertEqual(profiles.catalog(self.db, self.tag, "Usbekisch", "A2", None, None, 1, 48)["total"], 1)
        self.assertEqual(profiles.catalog(self.db, self.tag, "Russisch", None, None, None, 1, 48)["total"], 0)
        student = self._user()
        self.assertEqual(self._err(profiles.public_profile, self.db, student, t2.id).status_code, 404)
        self.assertEqual(profiles.public_profile(self.db, student, t1.id)["headline"], "DaF")

    def test_first_profile_requests_at_the_same_moment_create_one_row(self):
        # regression: two parallel GETs /teacher/market/profile both inserted the row → unique violation → 500
        import threading

        from sqlalchemy import func, select

        from app.models.teacher_profile import TeacherProfile
        from app.services.teacher_market.common import profile_of

        teacher = self._teacher()
        first = self.Session()
        first_id = profile_of(first, teacher.id, create=True).id  # inserted, not committed: the second insert has to wait
        result = {}

        def second():
            s = self.Session()
            try:
                result["row"] = profile_of(s, teacher.id, create=True)
                result["id"] = result["row"].id
                s.commit()
            except Exception as exc:  # noqa: BLE001 - the test reports it
                result["error"] = exc
                s.rollback()
            finally:
                s.close()

        thread = threading.Thread(target=second)
        thread.start()
        thread.join(1.0)
        self.assertTrue(thread.is_alive(), "the second insert waits for the first transaction")
        first.commit()
        thread.join(10)
        first.close()
        self.assertNotIn("error", result)
        self.assertEqual(result["id"], first_id)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(TeacherProfile).where(TeacherProfile.user_id == teacher.id)), 1)

    def test_profile_validation_and_rating_is_not_writable(self):
        from app.services.teacher_market import profiles

        t = self._teacher()
        self.assertEqual(self._err(profiles.update_own, self.db, t, {"languages": ["Klingonisch"]}).detail, "LANGUAGES_INVALID")
        self.assertEqual(self._err(profiles.update_own, self.db, t, {"experience_years": 99}).detail, "EXPERIENCE_INVALID")
        out = profiles.update_own(self.db, t, {"rating_avg": 5, "verified": True, "bio": "Hallo"})
        self.assertEqual(out["rating"]["count"], 0)
        self.assertFalse(out["verified"])

    def test_student_numbers_count_each_student_once(self):
        from app.services.teacher_market import enrollments, profiles

        admin, t = self._user("SUPER_ADMIN"), self._teacher()
        c1 = self._course(t, admin, max_students=5)
        c2 = self._course(t, admin, title=f"Zweiter {self.tag}", max_students=5)
        s1, s2 = self._user(), self._user()
        for course, student in ((c1, s1), (c2, s1), (c1, s2)):
            enrollments.enroll_free(self.db, student, course["id"])
        stats = profiles.student_stats(self.db, t.id)
        self.assertEqual(stats, {"current_students": 2, "total_students": 2})

    # ---------- courses ----------

    def test_course_life_cycle_and_free_enrollment(self):
        from sqlalchemy import select

        from app.models.study_group import StudyGroupMember
        from app.services.teacher_market import courses, enrollments, profiles

        admin, t, other = self._user("SUPER_ADMIN"), self._teacher(), self._teacher()
        student, s2, s3 = self._user(), self._user(), self._user()
        draft = courses.create(self.db, t, {"title": f"Entwurf {self.tag}", "level": "A1", "course_type": "FREE", "status": "ANMELDUNG"})
        self.assertEqual(profiles.public_profile(self.db, student, t.id)["courses"], [])  # a draft is invisible
        self.assertEqual(self._err(courses.public_course, self.db, student, draft["id"]).status_code, 404)
        self.assertEqual(self._err(courses.teacher_get, self.db, other, draft["id"]).status_code, 404)
        self.assertEqual(self._err(enrollments.enroll_free, self.db, student, draft["id"]).status_code, 404)

        course = self._course(t, admin)
        self.assertEqual(course["approval_status"], "APPROVED")
        self.assertIsNotNone(course["group_id"])
        self.assertEqual(self._err(enrollments.enroll_free, self.db, t, course["id"]).detail, "STUDENT_ONLY")
        res = enrollments.enroll_free(self.db, student, course["id"])
        self.assertEqual(res["status"], "ACTIVE")
        member = self.db.scalar(select(StudyGroupMember).where(StudyGroupMember.group_id == course["group_id"], StudyGroupMember.user_id == student.id))
        self.assertEqual(member.status, "active")
        self.assertEqual(self._err(enrollments.enroll_free, self.db, student, course["id"]).detail, "ALREADY_ENROLLED")
        enrollments.enroll_free(self.db, s2, course["id"])
        self.assertEqual(self._err(enrollments.enroll_free, self.db, s3, course["id"]).detail, "COURSE_FULL")
        self.assertEqual(courses.public_course(self.db, s3, course["id"])["status"], "AUSGEBUCHT")
        roster = courses.students(self.db, t, course["id"])
        self.assertEqual(len(roster["items"]), 2)
        self.assertEqual(self._err(courses.students, self.db, other, course["id"]).status_code, 404)

        changed = courses.update(self.db, t, course["id"], {"title": f"Neuer Titel {self.tag}"})
        self.assertTrue(changed["needs_review"])
        self.assertEqual(changed["approval_status"], "PENDING")
        self.assertEqual(self._err(courses.update, self.db, t, course["id"], {"max_students": 1}).detail, "MAX_BELOW_ENROLLED")

    def test_paid_course_goes_through_vizu_pay(self):
        from app.models.subscription_order import SubscriptionOrder
        from app.models.teacher_market import TeacherCourseEnrollment
        from app.services.teacher_market import enrollments
        from app.services.vizu_pay.admin_service import AdminVizuPayService

        admin, t = self._user("SUPER_ADMIN"), self._teacher()
        course = self._course(t, admin, course_type="PAID", price=250_000, max_students=1)
        s1, s2 = self._user(), self._user()
        paid = (datetime.now(timezone(timedelta(hours=5))) - timedelta(minutes=10))
        out = asyncio.run(enrollments.create_order(self.db, s1, course["id"], no_receipt=True, paid_date=paid.date().isoformat(),
                                                   paid_time=paid.strftime("%H:%M"), note=None, proof=None, ip=None))
        order = self.db.get(SubscriptionOrder, uuid.UUID(out["order"]["id"]))
        self.assertEqual((order.plan, order.final_amount, order.status), ("TEACHER_COURSE", 250_000, "PENDING"))
        # regression: the order lists (student + admin) have extra="forbid" response models; the teacher_course key broke them (500)
        from app.schemas.vizu_pay import AdminOrderItem, OrderItem, OrderListResponse

        self.assertEqual(str(OrderItem.model_validate(out["order"]).teacher_course.id), str(course["id"]))
        admin_list = AdminVizuPayService(self.db).list_orders(status="PENDING", user_id=str(s1.id), page_size=50)
        self.assertEqual([AdminOrderItem.model_validate(i).plan for i in admin_list["items"]], ["TEACHER_COURSE"])
        from app.services.vizu_pay.service import VizuPayService

        OrderListResponse.model_validate(VizuPayService(self.db).get_my_orders(s1))
        self.assertEqual(self._err(enrollments.enroll_free, self.db, s2, course["id"]).detail, "COURSE_TYPE_MISMATCH")
        with self.assertRaises(HTTPException) as e:  # the pending order holds the only place
            asyncio.run(enrollments.create_order(self.db, s2, course["id"], no_receipt=True, paid_date=paid.date().isoformat(),
                                                 paid_time=paid.strftime("%H:%M"), note=None, proof=None, ip=None))
        self.assertEqual(e.exception.detail, "COURSE_FULL")
        self.db.rollback()

        AdminVizuPayService(self.db).approve_order(str(order.id), admin, None)
        e1 = self.db.get(TeacherCourseEnrollment, out["enrollment_id"])
        self.db.refresh(e1)
        self.assertEqual(e1.status, "ACTIVE")
        AdminVizuPayService(self.db).refund_order(str(order.id), "Test", admin, None)
        self.db.refresh(e1)
        self.assertEqual(e1.status, "REFUNDED")

        out2 = asyncio.run(enrollments.create_order(self.db, s2, course["id"], no_receipt=True, paid_date=paid.date().isoformat(),
                                                    paid_time=paid.strftime("%H:%M"), note=None, proof=None, ip=None))
        AdminVizuPayService(self.db).reject_order(out2["order"]["id"], "Chek yo'q", admin, None)
        e2 = self.db.get(TeacherCourseEnrollment, out2["enrollment_id"])
        self.db.refresh(e2)
        self.assertEqual(e2.status, "REJECTED")

    # ---------- reviews ----------

    def test_reviews_need_a_real_started_course(self):
        from sqlalchemy import update

        from app.models.teacher_market import TeacherCourse
        from app.services.teacher_market import enrollments, profiles, reviews

        admin, t = self._user("SUPER_ADMIN"), self._teacher()
        course = self._course(t, admin, max_students=5)
        s1, s2, outsider = self._user(first="Aziza", last="Karimova"), self._user(), self._user()
        enrollments.enroll_free(self.db, s1, course["id"])
        enrollments.enroll_free(self.db, s2, course["id"])
        self.assertEqual(self._err(reviews.create, self.db, s1, {"course_id": course["id"], "rating": 5}).detail, "REVIEW_NOT_ALLOWED")  # not started
        self.db.execute(update(TeacherCourse).where(TeacherCourse.id == course["id"]).values(start_date=date.today() - timedelta(days=1)))
        self.db.commit()
        self.assertEqual(self._err(reviews.create, self.db, outsider, {"course_id": course["id"], "rating": 5}).detail, "REVIEW_NOT_ALLOWED")
        self.assertEqual(self._err(reviews.create, self.db, t, {"course_id": course["id"], "rating": 5}).detail, "STUDENT_ONLY")
        self.assertEqual(self._err(reviews.create, self.db, s1, {"course_id": course["id"], "rating": 6}).detail, "RATING_INVALID")
        r1 = reviews.create(self.db, s1, {"course_id": course["id"], "rating": 5, "body": "Sehr gut"})
        self.assertEqual(r1["author"], "Aziza K.")
        self.assertEqual(self._err(reviews.create, self.db, s1, {"course_id": course["id"], "rating": 1}).detail, "ALREADY_REVIEWED")
        r2 = reviews.create(self.db, s2, {"course_id": course["id"], "rating": 3})
        self.assertEqual(profiles.public_profile(self.db, outsider, t.id)["rating"]["avg"], 4.0)
        reviews.update_own(self.db, s2, r2["id"], {"rating": 4})
        self.assertEqual(profiles.public_profile(self.db, outsider, t.id)["rating"]["avg"], 4.5)
        self.assertEqual(self._err(reviews.update_own, self.db, s1, r2["id"], {"rating": 1}).status_code, 404)  # not the author
        reviews.report(self.db, t, r2["id"], "unfair")
        reviews.admin_moderate(self.db, admin, r2["id"], "hide", "Regelverstoß", None)
        rating = profiles.public_profile(self.db, outsider, t.id)["rating"]
        self.assertEqual((rating["avg"], rating["count"]), (5.0, 1))
        self.assertEqual(reviews.public_list(self.db, outsider, t.id, 1, 10)["total"], 1)

    # ---------- special lessons ----------

    def _lesson(self, teacher, admin, start_in=timedelta(hours=3), **data):
        from app.services.teacher_market import special_lessons as sl

        body = {"title": f"Spezial {self.tag}", "topic": "Perfekt", "level": "A2", "language": "Deutsch", "duration_minutes": 60,
                "max_participants": 50, "starts_at": datetime.now(timezone.utc) + start_in}
        body.update(data)
        lesson = sl.teacher_create(self.db, teacher, body)
        return lesson

    def test_special_lesson_approval_window_room_and_time_limit(self):
        from sqlalchemy import select, update

        from app.models.global_chat import GlobalChatMessage
        from app.models.teacher_market import SpecialLesson
        from app.models.video_room import VideoRoom, VideoRoomParticipant
        from app.services.teacher_market import special_lessons as sl
        from app.services.video_rooms import moderation, permissions, service as rooms

        admin, t, other = self._user("SUPER_ADMIN"), self._teacher(), self._teacher()
        student = self._user()
        self.assertEqual(self._err(sl.teacher_create, self.db, t, {"title": "Lang", "topic": "Thema", "level": "A1", "duration_minutes": 120,
                                                                     "max_participants": 10, "starts_at": datetime.now(timezone.utc) + timedelta(hours=3)}).detail,
                         "DURATION_INVALID")
        lesson = self._lesson(t, admin)
        board = sl.board(self.db, student)
        self.assertNotIn(lesson["id"], [x["id"] for x in board["upcoming"] + board["live"]])  # pending = invisible
        self.assertEqual(self._err(sl.get, self.db, student, lesson["id"]).status_code, 404)
        self.assertEqual(self._err(sl.open_room, self.db, t, lesson["id"]).detail, "SPECIAL_LESSON_NOT_APPROVED")

        approved = sl.admin_review(self.db, admin, lesson["id"], "approve", None, None, None)
        self.assertEqual(approved["status"], "APPROVED")
        row = self.db.get(SpecialLesson, lesson["id"])
        msg = self.db.get(GlobalChatMessage, row.announcement_message_id)
        self.assertIn(f"Spezial {self.tag}", msg.body)
        self.assertIn(lesson["id"], [x["id"] for x in sl.board(self.db, student)["upcoming"]])
        self.assertEqual(self._err(sl.open_room, self.db, t, lesson["id"]).detail, "OPEN_WINDOW_NOT_REACHED")
        self.assertEqual(self._err(sl.open_room, self.db, other, lesson["id"]).status_code, 404)

        start = datetime.now(timezone.utc) + timedelta(minutes=10)
        self.db.execute(update(SpecialLesson).where(SpecialLesson.id == lesson["id"]).values(starts_at=start))
        self.db.commit()
        opened = sl.open_room(self.db, t, lesson["id"])
        room = self.db.get(VideoRoom, opened["room_id"])
        self.assertEqual(room.status, "live")
        self.assertAlmostEqual(room.hard_end_at.timestamp(), (start + timedelta(minutes=60)).timestamp(), delta=2)
        self.assertEqual(sl.open_room(self.db, t, lesson["id"])["room_id"], room.id)  # idempotent

        joined = rooms.join(self.db, student, room.id, "10.0.0.1")
        self.assertEqual(joined["permissions"]["role"], "student")
        self.assertFalse(joined["permissions"]["microphone"])
        self.assertFalse(joined["permissions"]["camera"])
        p = self.db.scalar(select(VideoRoomParticipant).where(VideoRoomParticipant.room_id == room.id, VideoRoomParticipant.user_id == student.id))
        self.assertEqual(permissions.sources(p), [])
        self.assertEqual(self._err(moderation.mic_permission, self.db, student, room.id, True, t.id).status_code, 403)
        moderation.mic_permission(self.db, t, room.id, True, student.id)
        moderation.camera_permission(self.db, t, room.id, True, student.id)
        self.db.refresh(p)
        self.assertEqual(set(permissions.sources(p)), {"camera", "microphone"})
        moderation.camera_permission(self.db, t, room.id, False, student.id)
        self.db.refresh(p)
        self.assertEqual(permissions.sources(p), ["microphone"])

        self.db.execute(update(VideoRoom).where(VideoRoom.id == room.id).values(hard_end_at=datetime.now(timezone.utc) - timedelta(seconds=1)))
        self.db.commit()
        result = sl.tick(self.db)
        self.assertGreaterEqual(result["closed_rooms"], 1)
        self.db.refresh(room)
        row = self.db.get(SpecialLesson, lesson["id"])
        self.db.refresh(row)
        self.assertEqual((room.status, room.end_reason, row.status), ("ended", "time_limit", "ENDED"))
        self.db.refresh(msg)
        self.assertIsNone(msg.pinned_at)
        self.assertIn(("delete", room.room_name), self.fake.calls)
        self.assertEqual(self._err(rooms.join, self.db, student, room.id, "10.0.0.1").detail, "VIDEO_ROOM_NOT_LIVE")

    def test_group_room_api_refuses_lesson_rooms_and_unapproved_lessons_are_hidden(self):
        from sqlalchemy import update

        from app.models.teacher_market import SpecialLesson
        from app.services.teacher_market import special_lessons as sl
        from app.services.video_rooms import service as rooms

        admin, t, student = self._user("SUPER_ADMIN"), self._teacher(), self._user()
        lesson = self._lesson(t, admin)
        sl.admin_review(self.db, admin, lesson["id"], "approve", None, None, None)
        self.db.execute(update(SpecialLesson).where(SpecialLesson.id == lesson["id"]).values(starts_at=datetime.now(timezone.utc) + timedelta(minutes=5)))
        self.db.commit()
        room_id = sl.open_room(self.db, t, lesson["id"])["room_id"]
        self.assertEqual(self._err(rooms.cancel, self.db, t, room_id).detail, "SPECIAL_LESSON_ROOM")
        info = rooms.get_room(self.db, student, room_id)
        self.assertIsNone(info["group"])
        self.assertEqual(info["lesson"]["title"], f"Spezial {self.tag}")
        sl.cancel(self.db, admin, lesson["id"], "Krank", None)
        self.assertEqual(self._err(rooms.get_room, self.db, student, room_id).status_code, 404)  # cancelled = gone for students


if __name__ == "__main__":
    unittest.main()
