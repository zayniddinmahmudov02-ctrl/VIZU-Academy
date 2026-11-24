"""My Teacher marketplace API. Thin: validation here, rules in app.services.teacher_market.

Auth per router:
* `/my-teacher/*` and `/special-lessons/*`: `get_current_user` (every logged-in role may look; enrolling, paying and
  reviewing are for STUDENT accounts only — checked in the services, 403 STUDENT_ONLY). Hidden / disabled teachers and
  unapproved courses / lessons are 404.
* `/teacher/market/*`: `require_teacher_panel_access` (TEACHER or SUPER_ADMIN; must have changed the temporary password).
  A teacher only ever reaches own profile, courses, students, reviews and lessons (others → 404). No endpoint lets a teacher
  change a rating or a review.
* `/admin/teacher-market/*`: reads `require_admin_panel_access`, every change `require_super_admin` (audited).
Bodies never carry the caller's id, role, a price paid or a rating total."""

import math
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access, require_super_admin, require_teacher_panel_access
from app.core.client_ip import client_ip
from app.db.session import get_db
from app.models.teacher_market import TeacherReview
from app.models.user import User
from app.services.teacher_market import certificates, common, courses, enrollments, profiles, reviews, special_lessons

router = APIRouter(prefix="/my-teacher", tags=["My Teacher"])
special_router = APIRouter(prefix="/special-lessons", tags=["Special lessons"])
teacher_router = APIRouter(prefix="/teacher/market", tags=["Teacher marketplace"])
admin_router = APIRouter(prefix="/admin/teacher-market", tags=["Admin teacher marketplace"])


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProfileIn(_In):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    headline: str | None = Field(None, max_length=200)
    bio: str | None = Field(None, max_length=5000)
    specialization: str | None = Field(None, max_length=400)
    methodology: str | None = Field(None, max_length=5000)
    experience_years: int | None = None
    teaching_since: int | None = None
    exam_prep: list[str] | None = None
    languages: list[str] | None = None
    levels: list[str] | None = None


class CourseIn(_In):
    title: str | None = Field(None, max_length=250)
    description: str | None = Field(None, max_length=7000)
    language: str | None = None
    level: str | None = None
    course_type: Literal["PAID", "FREE", "UPCOMING"] | None = None
    price: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    duration_weeks: int | None = None
    lessons_per_week: int | None = None
    weekdays: list[str] | None = None
    lesson_time: str | None = Field(None, max_length=5)
    lesson_minutes: int | None = None
    max_students: int | None = None
    enrollment_deadline: date | None = None
    status: Literal["ANMELDUNG", "BALD", "VORBEREITUNG", "LAUFEND", "ABGESCHLOSSEN", "ABGESAGT"] | None = None


class LessonIn(_In):
    title: str | None = Field(None, max_length=250)
    topic: str | None = Field(None, max_length=250)
    description: str | None = Field(None, max_length=5000)
    objectives: str | None = Field(None, max_length=3000)
    language: str | None = None
    level: str | None = None
    starts_at: datetime | None = None
    duration_minutes: int | None = None
    max_participants: int | None = None


class ReviewIn(_In):
    course_id: UUID
    rating: int
    body: str | None = Field(None, max_length=2100)


class ReviewUpdate(_In):
    rating: int | None = None
    body: str | None = Field(None, max_length=2100)


class ReasonIn(_In):
    reason: str | None = Field(None, max_length=600)


class DecisionIn(_In):
    decision: Literal["approve", "reject", "unpublish", "verify"]
    reason: str | None = Field(None, max_length=600)
    starts_at: datetime | None = None


class ModerateIn(_In):
    action: Literal["hide", "show", "dismiss"]
    reason: str | None = Field(None, max_length=600)


class FlagsIn(_In):
    catalog_hidden: bool | None = None
    profile_disabled: bool | None = None
    verified: bool | None = None


class SettingsIn(_In):
    course_auto_publish: bool


class InterestIn(_In):
    on: bool = True


def _crop(x: float | None, y: float | None, w: float | None):
    """Fractions of the image; browser float noise (-1e-16, 1.0000000000000002) is clamped, anything really outside is refused."""
    out = []
    for v in (x, y, w):
        if v is not None:
            if not math.isfinite(v) or not -1e-6 <= v <= 1 + 1e-6:
                raise common.err(422, "CROP_INVALID")
            v = min(1.0, max(0.0, v))
        out.append(v)
    return tuple(out)


# ================= student / everyone =================

@router.get("/teachers")
def catalog(q: str | None = Query(None, max_length=100), language: str | None = None, level: str | None = None,
            courses: Literal["open", "any"] | None = None, activity: Literal["teaching"] | None = None,
            page: int = Query(1, ge=1, le=1000), page_size: int = Query(24, ge=1, le=48),
            db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return profiles.catalog(db, q, language, level, courses, activity, page, page_size)


@router.get("/teachers/{teacher_id}")
def teacher_profile(teacher_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return profiles.public_profile(db, user, teacher_id)


@router.get("/teachers/{teacher_id}/reviews")
def teacher_reviews(teacher_id: UUID, page: int = Query(1, ge=1, le=1000), page_size: int = Query(10, ge=1, le=50),
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return reviews.public_list(db, user, teacher_id, page, page_size)


@router.get("/courses/{course_id}")
def course_detail(course_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return courses.public_course(db, user, course_id)


@router.post("/courses/{course_id}/enroll")
def enroll(course_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return enrollments.enroll_free(db, user, course_id)


@router.post("/courses/{course_id}/interest")
def interest(course_id: UUID, data: InterestIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return enrollments.interest(db, user, course_id, data.on)


@router.get("/courses/{course_id}/checkout")
def checkout(course_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return enrollments.checkout(db, user, course_id)


@router.post("/courses/{course_id}/order", status_code=201)
async def create_order(course_id: UUID, request: Request, no_receipt: bool = Form(False), paid_date: str | None = Form(None),
                       paid_time: str | None = Form(None), note: str | None = Form(None), proof: UploadFile | None = File(None),
                       db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return await enrollments.create_order(db, user, course_id, no_receipt=no_receipt, paid_date=paid_date, paid_time=paid_time, note=note,
                                          proof=proof, ip=client_ip(request))


@router.get("/my-courses")
def my_courses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return enrollments.my_courses(db, user)


@router.post("/reviews", status_code=201)
def create_review(data: ReviewIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return reviews.create(db, user, data.model_dump())


@router.patch("/reviews/{review_id}")
def update_review(review_id: UUID, data: ReviewUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return reviews.update_own(db, user, review_id, data.model_dump(exclude_unset=True))


@router.post("/reviews/{review_id}/report")
def report_review(review_id: UUID, data: ReasonIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return reviews.report(db, user, review_id, data.reason or "")


@router.get("/certificates/{cert_id}/file")
def certificate_file(cert_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    path, media_type, name = certificates.file_for(db, user, cert_id)
    return FileResponse(path, media_type=media_type, filename=name, content_disposition_type="inline",
                        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


# ================= special lessons (everyone) =================

@special_router.get("/board")
def lesson_board(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return special_lessons.board(db, user)


@special_router.get("/{lesson_id}")
def lesson_detail(lesson_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return special_lessons.get(db, user, lesson_id)


@special_router.post("/{lesson_id}/signup")
def lesson_signup(lesson_id: UUID, data: InterestIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return special_lessons.signup(db, user, lesson_id, data.on)


# ================= teacher panel =================

@teacher_router.get("/profile")
def own_profile(db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return profiles.own_profile(db, teacher)


@teacher_router.put("/profile")
def update_profile(data: ProfileIn, db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return profiles.update_own(db, teacher, data.model_dump(exclude_unset=True))


@teacher_router.post("/profile/photo")
async def upload_photo(file: UploadFile = File(...), x: float | None = Form(None), y: float | None = Form(None), w: float | None = Form(None),
                       db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return await profiles.upload_photo(db, teacher, file, *_crop(x, y, w))


@teacher_router.delete("/profile/photo")
def delete_photo(db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return profiles.remove_photo(db, teacher)


@teacher_router.post("/certificates", status_code=201)
async def upload_certificate(title: str = Form(..., max_length=250), issuer: str = Form(..., max_length=250), issued_on: str | None = Form(None),
                             level: str | None = Form(None, max_length=60), file: UploadFile = File(...),
                             db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return await certificates.upload(db, teacher, title=title, issuer=issuer, issued_on=issued_on, level=level, file=file)


@teacher_router.delete("/certificates/{cert_id}")
def delete_certificate(cert_id: UUID, db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return certificates.delete_own(db, teacher, cert_id)


@teacher_router.get("/courses")
def own_courses(db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return courses.teacher_list(db, teacher)


@teacher_router.post("/courses", status_code=201)
def create_course(data: CourseIn, db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return courses.create(db, teacher, data.model_dump(exclude_unset=True))


@teacher_router.get("/courses/{course_id}")
def own_course(course_id: UUID, db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return courses.teacher_get(db, teacher, course_id)


@teacher_router.patch("/courses/{course_id}")
def update_course(course_id: UUID, data: CourseIn, db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return courses.update(db, teacher, course_id, data.model_dump(exclude_unset=True))


@teacher_router.post("/courses/{course_id}/submit")
def submit_course(course_id: UUID, db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return courses.submit(db, teacher, course_id)


@teacher_router.post("/courses/{course_id}/image")
async def course_image(course_id: UUID, file: UploadFile = File(...), x: float | None = Form(None), y: float | None = Form(None),
                       w: float | None = Form(None), db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return await courses.upload_image(db, teacher, course_id, file, *_crop(x, y, w))


@teacher_router.get("/courses/{course_id}/students")
def course_students(course_id: UUID, db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return courses.students(db, teacher, course_id)


@teacher_router.get("/reviews")
def own_reviews(db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return reviews.teacher_list(db, teacher)


@teacher_router.post("/reviews/{review_id}/report")
def teacher_report(review_id: UUID, data: ReasonIn, db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    row = db.get(TeacherReview, review_id)
    if row is None or row.teacher_id != teacher.id:
        raise common.err(404, "REVIEW_NOT_FOUND")
    return reviews.report(db, teacher, review_id, data.reason or "")


@teacher_router.get("/special-lessons")
def own_lessons(db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return special_lessons.teacher_list(db, teacher)


@teacher_router.post("/special-lessons", status_code=201)
def request_lesson(data: LessonIn, db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return special_lessons.teacher_create(db, teacher, data.model_dump(exclude_unset=True))


@teacher_router.patch("/special-lessons/{lesson_id}")
def update_lesson(lesson_id: UUID, data: LessonIn, db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    return special_lessons.teacher_update(db, teacher, lesson_id, data.model_dump(exclude_unset=True))


@teacher_router.post("/special-lessons/{lesson_id}/cancel")
def cancel_lesson(lesson_id: UUID, data: ReasonIn, request: Request, db: Session = Depends(get_db),
                  teacher: User = Depends(require_teacher_panel_access)):
    return special_lessons.cancel(db, teacher, lesson_id, data.reason, client_ip(request))


@teacher_router.post("/special-lessons/{lesson_id}/open")
def open_lesson_room(lesson_id: UUID, response: Response, db: Session = Depends(get_db), teacher: User = Depends(require_teacher_panel_access)):
    response.headers["Cache-Control"] = "no-store"
    return special_lessons.open_room(db, teacher, lesson_id)


# ================= admin =================

@admin_router.get("/overview")
def admin_overview(db: Session = Depends(get_db), _admin: User = Depends(require_admin_panel_access)):
    return {"teachers": profiles.admin_counts(db), "courses": courses.admin_counts(db), "special_lessons": special_lessons.admin_counts(db),
            "reviews": reviews.admin_counts(db), "settings": common.get_settings(db)}


@admin_router.get("/teachers")
def admin_teachers(q: str | None = Query(None, max_length=100), flag: Literal["hidden", "disabled", "verified", "unverified"] | None = None,
                   page: int = Query(1, ge=1, le=1000), page_size: int = Query(50, ge=1, le=100),
                   db: Session = Depends(get_db), _admin: User = Depends(require_admin_panel_access)):
    return profiles.admin_teachers(db, q, flag, page, page_size)


@admin_router.patch("/teachers/{teacher_id}")
def admin_update_teacher(teacher_id: UUID, data: FlagsIn, request: Request, db: Session = Depends(get_db),
                         admin: User = Depends(require_super_admin)):
    return profiles.admin_update_teacher(db, admin, teacher_id, data.model_dump(exclude_unset=True), client_ip(request))


@admin_router.get("/certificates")
def admin_certificates(status: Literal["pending", "verified", "rejected"] | None = None, db: Session = Depends(get_db),
                       _admin: User = Depends(require_admin_panel_access)):
    return certificates.admin_list(db, status)


@admin_router.post("/certificates/{cert_id}/review")
def admin_certificate_review(cert_id: UUID, data: DecisionIn, request: Request, db: Session = Depends(get_db),
                             admin: User = Depends(require_super_admin)):
    decision = "verify" if data.decision in ("verify", "approve") else data.decision
    return certificates.admin_review(db, admin, cert_id, decision, data.reason, client_ip(request))


@admin_router.get("/courses")
def admin_courses(approval: Literal["DRAFT", "PENDING", "APPROVED", "REJECTED", "UNPUBLISHED"] | None = None, db: Session = Depends(get_db),
                  _admin: User = Depends(require_admin_panel_access)):
    return courses.admin_list(db, approval)


@admin_router.post("/courses/{course_id}/review")
def admin_course_review(course_id: UUID, data: DecisionIn, request: Request, db: Session = Depends(get_db),
                        admin: User = Depends(require_super_admin)):
    return courses.admin_review(db, admin, course_id, data.decision, data.reason, client_ip(request))


@admin_router.get("/special-lessons")
def admin_lessons(status: Literal["PENDING", "APPROVED", "REJECTED", "CANCELLED", "ENDED"] | None = None, db: Session = Depends(get_db),
                  _admin: User = Depends(require_admin_panel_access)):
    return special_lessons.admin_list(db, status)


@admin_router.post("/special-lessons/{lesson_id}/review")
def admin_lesson_review(lesson_id: UUID, data: DecisionIn, request: Request, db: Session = Depends(get_db),
                        admin: User = Depends(require_super_admin)):
    return special_lessons.admin_review(db, admin, lesson_id, data.decision, data.reason, data.starts_at, client_ip(request))


@admin_router.post("/special-lessons/{lesson_id}/cancel")
def admin_lesson_cancel(lesson_id: UUID, data: ReasonIn, request: Request, db: Session = Depends(get_db),
                        admin: User = Depends(require_super_admin)):
    return special_lessons.cancel(db, admin, lesson_id, data.reason, client_ip(request))


@admin_router.get("/reviews")
def admin_reviews(view: Literal["reported", "hidden", "all"] | None = "reported", db: Session = Depends(get_db),
                  _admin: User = Depends(require_admin_panel_access)):
    return reviews.admin_list(db, view)


@admin_router.post("/reviews/{review_id}/moderate")
def admin_review_moderate(review_id: UUID, data: ModerateIn, request: Request, db: Session = Depends(get_db),
                          admin: User = Depends(require_super_admin)):
    return reviews.admin_moderate(db, admin, review_id, data.action, data.reason, client_ip(request))


@admin_router.put("/settings")
def admin_settings(data: SettingsIn, request: Request, db: Session = Depends(get_db), admin: User = Depends(require_super_admin)):
    from app.core.audit import write_audit

    value = common.set_settings(db, admin, data.model_dump())
    db.commit()
    write_audit(db, actor_id=admin.id, action="teacher_market_settings", details=f"course_auto_publish={value['course_auto_publish']}",
                ip_address=client_ip(request))
    return value
