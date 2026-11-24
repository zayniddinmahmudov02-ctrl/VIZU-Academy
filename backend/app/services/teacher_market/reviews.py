"""Teacher reviews ("Bewertungen und Erfahrungen") and the 5-star rating.

* Only a STUDENT with an ACTIVE / COMPLETED enrollment in one of the teacher's courses writes a review, and only once the course
  has started (start date reached, or LAUFEND / ABGESCHLOSSEN) — a real lesson, not a sign-up. One review per student and course
  (unique); the student may change own rating / text later (edited_at). 1–5 stars, text ≤ 2000 characters.
* Nobody else writes, changes or deletes a review: the teacher can only read and report one; a SUPER_ADMIN moderates (hide /
  show again / close reports) — the row and its text always stay, every step is in audit_logs.
* The rating is computed by the server from VISIBLE reviews after every change and stored on teacher_profiles
  (rating_avg, rating_count); no request can set it.
* Under a review only the student's first name + initial of the last name and "Verified Enrollment" are shown."""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.security.roles import UserRole
from app.models.teacher_market import (
    EN_ACTIVE,
    EN_COMPLETED,
    REPORT_OPEN,
    REPORT_RESOLVED,
    REVIEW_HIDDEN,
    REVIEW_VISIBLE,
    ST_ABGESCHLOSSEN,
    ST_LAUFEND,
    TeacherCourse,
    TeacherCourseEnrollment,
    TeacherReview,
    TeacherReviewReport,
)
from app.models.teacher_profile import TeacherProfile
from app.models.user import User
from app.services.teacher_market import common as c

MAX_BODY = 2000


def recompute(db: Session, teacher_id) -> None:
    avg, n = db.execute(select(func.avg(TeacherReview.rating), func.count()).where(TeacherReview.teacher_id == teacher_id,
                                                                                    TeacherReview.status == REVIEW_VISIBLE)).one()
    p = c.profile_of(db, teacher_id, create=True)
    p.rating_count = int(n or 0)
    p.rating_avg = round(float(avg), 2) if n else 0


def summary(db: Session, teacher_id, profile: TeacherProfile | None) -> dict:
    dist = dict(db.execute(select(TeacherReview.rating, func.count()).where(TeacherReview.teacher_id == teacher_id,
                                                                             TeacherReview.status == REVIEW_VISIBLE).group_by(TeacherReview.rating)).all())
    return {"avg": float(profile.rating_avg) if profile else 0.0, "count": profile.rating_count if profile else 0,
            "distribution": {str(k): int(dist.get(k, 0)) for k in range(1, 6)}}


def _started(course: TeacherCourse) -> bool:
    today = c.now().astimezone(c.TASHKENT).date()
    return (course.start_date is not None and course.start_date <= today) or course.status in (ST_LAUFEND, ST_ABGESCHLOSSEN)


def _eligible_courses(db: Session, student: User, teacher_id) -> list[TeacherCourse]:
    rows = db.scalars(select(TeacherCourse).join(TeacherCourseEnrollment, TeacherCourseEnrollment.course_id == TeacherCourse.id).where(
        TeacherCourse.teacher_id == teacher_id, TeacherCourseEnrollment.student_id == student.id,
        TeacherCourseEnrollment.status.in_((EN_ACTIVE, EN_COMPLETED)))).unique()
    return [r for r in rows if _started(r)]


def _out(r: TeacherReview, course_title: str | None = None, mine: bool = False) -> dict:
    item = {"id": r.id, "rating": r.rating, "body": r.body, "created_at": r.created_at, "edited_at": r.edited_at, "author": c.short_name(r.student),
            "verified_enrollment": True, "course": {"id": r.course_id, "title": course_title}}
    if mine:
        item["status"] = r.status
    return item


def viewer_options(db: Session, viewer: User, teacher_id) -> dict | None:
    if viewer.role != UserRole.STUDENT:
        return None
    mine = list(db.scalars(select(TeacherReview).where(TeacherReview.teacher_id == teacher_id, TeacherReview.student_id == viewer.id)))
    done = {r.course_id for r in mine}
    titles = dict(db.execute(select(TeacherCourse.id, TeacherCourse.title).where(TeacherCourse.teacher_id == teacher_id)).all())
    return {"can_review": [{"course_id": x.id, "title": x.title} for x in _eligible_courses(db, viewer, teacher_id) if x.id not in done],
            "my_reviews": [_out(r, titles.get(r.course_id), mine=True) for r in mine]}


def public_list(db: Session, viewer: User, teacher_id, page: int, page_size: int) -> dict:
    from app.services.teacher_market import profiles

    profiles.public_profile(db, viewer, teacher_id)  # same visibility as the profile (404 otherwise)
    tid = c.parse_uuid(teacher_id)
    page, page_size = max(1, page), max(1, min(50, page_size))
    base = select(TeacherReview).where(TeacherReview.teacher_id == tid, TeacherReview.status == REVIEW_VISIBLE)
    total = int(db.scalar(select(func.count()).select_from(base.subquery())) or 0)
    rows = list(db.scalars(base.order_by(TeacherReview.created_at.desc()).offset((page - 1) * page_size).limit(page_size)))
    titles = dict(db.execute(select(TeacherCourse.id, TeacherCourse.title).where(TeacherCourse.id.in_([r.course_id for r in rows] or [None]))).all())
    return {"items": [_out(r, titles.get(r.course_id)) for r in rows], "total": total, "page": page, "page_size": page_size}


def _body(value) -> str | None:
    text = c.block(value, MAX_BODY + 1)
    if text and len(text) > MAX_BODY:
        raise c.err(422, "REVIEW_TOO_LONG")
    return text


def _rating(value) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
        raise c.err(422, "RATING_INVALID")
    return value


def create(db: Session, student: User, data: dict) -> dict:
    c.require_student(student)
    course = db.get(TeacherCourse, c.parse_uuid(data.get("course_id")))
    if course is None or course.id not in {x.id for x in _eligible_courses(db, student, course.teacher_id)}:
        raise c.err(403, "REVIEW_NOT_ALLOWED")
    review = TeacherReview(teacher_id=course.teacher_id, student_id=student.id, course_id=course.id, rating=_rating(data.get("rating")),
                           body=_body(data.get("body")), status=REVIEW_VISIBLE)
    review.student = student
    db.add(review)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise c.err(409, "ALREADY_REVIEWED") from None
    recompute(db, course.teacher_id)
    c.notify(db, course.teacher_id, "Yangi baho / Neue Bewertung", f"«{course.title}»: {review.rating}★", "/teacher/bewertungen")
    db.commit()
    return _out(review, course.title, mine=True)


def update_own(db: Session, student: User, review_id, data: dict) -> dict:
    c.require_student(student)
    review = db.scalar(select(TeacherReview).where(TeacherReview.id == c.parse_uuid(review_id)).with_for_update(of=TeacherReview))
    if review is None or review.student_id != student.id:
        raise c.err(404, "REVIEW_NOT_FOUND")
    if review.status == REVIEW_HIDDEN:
        raise c.err(409, "REVIEW_HIDDEN")
    if "rating" in data:
        review.rating = _rating(data["rating"])
    if "body" in data:
        review.body = _body(data["body"])
    review.edited_at = c.now()
    recompute(db, review.teacher_id)
    db.commit()
    course = db.get(TeacherCourse, review.course_id)
    return _out(review, course.title if course else None, mine=True)


def report(db: Session, user: User, review_id, reason: str) -> dict:
    review = db.get(TeacherReview, c.parse_uuid(review_id))
    if review is None or (review.status != REVIEW_VISIBLE and user.id != review.teacher_id):
        raise c.err(404, "REVIEW_NOT_FOUND")
    if user.id == review.student_id:
        raise c.err(409, "OWN_REVIEW")
    text = c.one_line(reason, "reason", 500, min_len=3, required=True)
    db.add(TeacherReviewReport(review_id=review.id, reporter_id=user.id, reason=text, status=REPORT_OPEN))
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise c.err(409, "ALREADY_REPORTED") from None
    c.notify_admins(db, "Sharh shikoyati / Bewertung gemeldet", f"{c.display_name(user)}: {text}", "/admin/lehrer-marktplatz?tab=bewertungen")
    db.commit()
    return {"reported": True}


def teacher_list(db: Session, teacher: User) -> dict:
    rows = list(db.scalars(select(TeacherReview).where(TeacherReview.teacher_id == teacher.id).order_by(TeacherReview.created_at.desc()).limit(500)))
    titles = dict(db.execute(select(TeacherCourse.id, TeacherCourse.title).where(TeacherCourse.teacher_id == teacher.id)).all())
    reported = set(db.scalars(select(TeacherReviewReport.review_id).where(TeacherReviewReport.reporter_id == teacher.id)))
    items = [{**_out(r, titles.get(r.course_id), mine=True), "reported_by_me": r.id in reported} for r in rows]
    return {"rating": summary(db, teacher.id, c.profile_of(db, teacher.id)), "items": items}


# ---------- admin moderation ----------

def admin_list(db: Session, view: str | None) -> list[dict]:
    open_counts = dict(db.execute(select(TeacherReviewReport.review_id, func.count()).where(TeacherReviewReport.status == REPORT_OPEN)
                                  .group_by(TeacherReviewReport.review_id)).all())
    q = select(TeacherReview)
    if view == "reported":
        q = q.where(TeacherReview.id.in_(list(open_counts) or [None]))
    elif view == "hidden":
        q = q.where(TeacherReview.status == REVIEW_HIDDEN)
    rows = list(db.scalars(q.order_by(TeacherReview.created_at.desc()).limit(300)))
    teachers = {u.id: u for u in db.scalars(select(User).where(User.id.in_([r.teacher_id for r in rows] or [None])))}
    titles = dict(db.execute(select(TeacherCourse.id, TeacherCourse.title).where(TeacherCourse.id.in_([r.course_id for r in rows] or [None]))).all())
    reports = {}
    for rep in db.scalars(select(TeacherReviewReport).where(TeacherReviewReport.review_id.in_([r.id for r in rows] or [None]))
                          .order_by(TeacherReviewReport.created_at.desc())):
        reports.setdefault(rep.review_id, []).append({"reason": rep.reason, "status": rep.status, "created_at": rep.created_at})
    return [{**_out(r, titles.get(r.course_id), mine=True), "student": {"id": r.student_id, "name": c.display_name(r.student)},
             "teacher": {"id": r.teacher_id, "name": c.display_name(teachers.get(r.teacher_id))}, "hidden_reason": r.hidden_reason,
             "open_reports": int(open_counts.get(r.id, 0)), "reports": reports.get(r.id, [])} for r in rows]


def admin_moderate(db: Session, admin: User, review_id, action: str, reason: str | None, ip: str | None) -> dict:
    review = db.scalar(select(TeacherReview).where(TeacherReview.id == c.parse_uuid(review_id)).with_for_update(of=TeacherReview))
    if review is None:
        raise c.err(404, "REVIEW_NOT_FOUND")
    if action == "hide":
        review.status, review.hidden_at, review.hidden_by = REVIEW_HIDDEN, c.now(), admin.id
        review.hidden_reason = c.one_line(reason, "reason", 500, min_len=3, required=True)
    elif action == "show":
        review.status, review.hidden_at, review.hidden_by, review.hidden_reason = REVIEW_VISIBLE, None, None, None
    elif action != "dismiss":
        raise c.err(422, "ACTION_INVALID")
    for rep in db.scalars(select(TeacherReviewReport).where(TeacherReviewReport.review_id == review.id, TeacherReviewReport.status == REPORT_OPEN)):
        rep.status, rep.resolved_by, rep.resolved_at = REPORT_RESOLVED, admin.id, c.now()
    recompute(db, review.teacher_id)
    db.commit()
    write_audit(db, actor_id=admin.id, action=f"teacher_review_{action}", target_user_id=review.teacher_id,
                details=f"review={review.id} rating={review.rating}" + (f", reason={review.hidden_reason}" if action == "hide" else ""), ip_address=ip)
    return {"id": review.id, "status": review.status}


def admin_counts(db: Session) -> dict:
    return {"open_reports": int(db.scalar(select(func.count(func.distinct(TeacherReviewReport.review_id))).where(
        TeacherReviewReport.status == REPORT_OPEN)) or 0),
            "hidden": int(db.scalar(select(func.count()).select_from(TeacherReview).where(TeacherReview.status == REVIEW_HIDDEN)) or 0),
            "total": int(db.scalar(select(func.count()).select_from(TeacherReview)) or 0)}
