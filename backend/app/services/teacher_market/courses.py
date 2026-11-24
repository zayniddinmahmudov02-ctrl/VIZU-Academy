"""Teacher courses ("Meine Kurse") and their admin approval.

Life cycle: DRAFT → (submit) PENDING → APPROVED / REJECTED; APPROVED → UNPUBLISHED (admin). If the admin setting
`course_auto_publish` is on, submit approves at once. Students only ever see APPROVED courses of a bookable teacher.
Changing title, description, level, language, type or price of an APPROVED course sends it back to PENDING (hidden until
approved again) unless auto-publish is on; enrollments and payments already made keep their own price snapshot.

Public status (`status`, set by the teacher): ANMELDUNG, BALD, VORBEREITUNG, LAUFEND, ABGESCHLOSSEN, ABGESAGT. AUSGEBUCHT is
derived: ANMELDUNG with no free place. ANMELDUNG after the enrollment deadline shows LAUFEND (started) or VORBEREITUNG.
An UPCOMING course is BALD / VORBEREITUNG / ABGESAGT only and takes "Interesse", never an enrollment.

On the first approval the course gets a study group (teacher = the course teacher): every ACTIVE enrollment is a member, so
the group chat and group video lessons are the classroom; attendance = held group video lessons the student joined."""

import re
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.models.study_group import GROUP_ACTIVE, MEMBER_ACTIVE, MEMBER_STUDENT, StudyGroup, StudyGroupMember
from app.models.subscription_order import SubscriptionOrder
from app.models.teacher_market import (
    APPROVAL_APPROVED,
    APPROVAL_DRAFT,
    APPROVAL_PENDING,
    APPROVAL_REJECTED,
    APPROVAL_UNPUBLISHED,
    COURSE_FREE,
    COURSE_PAID,
    COURSE_STATUSES,
    COURSE_TYPES,
    COURSE_UPCOMING,
    EN_ACTIVE,
    EN_LIVE,
    EN_PENDING_PAYMENT,
    ST_ABGESAGT,
    ST_ABGESCHLOSSEN,
    ST_ANMELDUNG,
    ST_AUSGEBUCHT,
    ST_BALD,
    ST_LAUFEND,
    ST_VORBEREITUNG,
    TeacherCourse,
    TeacherCourseEnrollment,
    TeacherCourseInterest,
)
from app.models.user import User
from app.models.video_room import ROOM_ENDED, VideoRoom, VideoRoomParticipant
from app.services.teacher_market import common as c
from app.services.teacher_market import media

WEEKDAYS = ("MO", "DI", "MI", "DO", "FR", "SA", "SO")
SENSITIVE = ("title", "description", "level", "language", "course_type", "price")
MAX_PRICE = 100_000_000
MIN_PAID_PRICE = 1_000
MAX_COURSES_PER_TEACHER = 100
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


# ---------- validation ----------

def _int(data: dict, key: str, lo: int, hi: int) -> int | None:
    v = data.get(key)
    if v is None:
        return None
    if not isinstance(v, int) or isinstance(v, bool) or not lo <= v <= hi:
        raise c.err(422, f"{key.upper()}_INVALID")
    return v


def _day(data: dict, key: str) -> date | None:
    v = data.get(key)
    if v in (None, ""):
        return None
    if isinstance(v, date):
        d = v
    else:
        try:
            d = date.fromisoformat(str(v))
        except ValueError:
            raise c.err(422, f"{key.upper()}_INVALID") from None
    if d.year < 2020 or d > c.now().date() + timedelta(days=730):
        raise c.err(422, f"{key.upper()}_INVALID")
    return d


def _apply(course: TeacherCourse, data: dict) -> list[str]:
    """Validate the given fields and set them; returns the names that changed."""
    changed = []

    def put(name, value):
        if getattr(course, name) != value:
            setattr(course, name, value)
            changed.append(name)

    if "title" in data:
        put("title", c.one_line(data["title"], "title", 200, min_len=3, required=True))
    if "description" in data:
        put("description", c.block(data["description"], 6000))
    if "level" in data:
        put("level", c.level(data["level"]))
    if "language" in data:
        put("language", c.language(data["language"]))
    if "course_type" in data:
        if data["course_type"] not in COURSE_TYPES:
            raise c.err(422, "COURSE_TYPE_INVALID")
        put("course_type", data["course_type"])
    if "price" in data:
        put("price", _int(data, "price", 0, MAX_PRICE) or 0)
    for key, lo, hi in (("duration_weeks", 1, 104), ("lessons_per_week", 1, 14), ("lesson_minutes", 15, 300)):
        if key in data:
            put(key, _int(data, key, lo, hi))
    if "max_students" in data:
        put("max_students", _int(data, "max_students", 1, 500) or course.max_students)
    for key in ("start_date", "end_date", "enrollment_deadline"):
        if key in data:
            put(key, _day(data, key))
    if "weekdays" in data:
        days = c.choices(data["weekdays"], WEEKDAYS, "weekdays", 7)
        put("weekdays", sorted(days, key=WEEKDAYS.index) or None)
    if "lesson_time" in data:
        v = (data["lesson_time"] or "").strip()
        if v and not TIME_RE.match(v):
            raise c.err(422, "LESSON_TIME_INVALID")
        put("lesson_time", v or None)
    if "status" in data:
        if data["status"] not in COURSE_STATUSES:
            raise c.err(422, "STATUS_INVALID")
        put("status", data["status"])
    # combined rules
    if course.course_type == COURSE_FREE:
        course.price = 0
    elif course.course_type == COURSE_PAID and not MIN_PAID_PRICE <= course.price <= MAX_PRICE:
        raise c.err(422, "PRICE_INVALID")
    if course.course_type == COURSE_UPCOMING and course.status not in (ST_BALD, ST_VORBEREITUNG, ST_ABGESAGT):
        raise c.err(422, "UPCOMING_STATUS_INVALID")
    if course.start_date and course.end_date and course.end_date < course.start_date:
        raise c.err(422, "END_BEFORE_START")
    return changed


# ---------- state ----------

def seats_taken(db: Session, course_id) -> int:
    return int(db.scalar(select(func.count()).select_from(TeacherCourseEnrollment).where(
        TeacherCourseEnrollment.course_id == course_id, TeacherCourseEnrollment.status.in_((EN_PENDING_PAYMENT, EN_ACTIVE)))) or 0)


def effective_status(course: TeacherCourse, taken: int, today: date | None = None) -> str:
    today = today or c.now().astimezone(c.TASHKENT).date()
    if course.status != ST_ANMELDUNG or course.course_type == COURSE_UPCOMING:
        return course.status
    if course.enrollment_deadline and course.enrollment_deadline < today:
        return ST_LAUFEND if course.start_date and course.start_date <= today else ST_VORBEREITUNG
    if taken >= course.max_students:
        return ST_AUSGEBUCHT
    return ST_ANMELDUNG


def enrollable(db: Session, course: TeacherCourse, taken: int | None = None) -> bool:
    if course.approval_status != APPROVAL_APPROVED or course.course_type not in (COURSE_PAID, COURSE_FREE):
        return False
    if not c.bookable(course.teacher, c.profile_of(db, course.teacher_id)):
        return False
    return effective_status(course, seats_taken(db, course.id) if taken is None else taken) == ST_ANMELDUNG


def _base_out(course: TeacherCourse, taken: int) -> dict:
    return {
        "id": course.id, "title": course.title, "description": course.description, "language": course.language, "level": course.level,
        "course_type": course.course_type, "price": course.price, "currency": "UZS", "start_date": course.start_date, "end_date": course.end_date,
        "duration_weeks": course.duration_weeks, "lessons_per_week": course.lessons_per_week, "weekdays": course.weekdays or [],
        "lesson_time": course.lesson_time, "lesson_minutes": course.lesson_minutes, "max_students": course.max_students, "enrolled": taken,
        "seats_left": max(0, course.max_students - taken), "enrollment_deadline": course.enrollment_deadline, "image_url": course.image_path,
        "status": effective_status(course, taken), "teacher": {"id": course.teacher_id, "name": c.display_name(course.teacher)},
    }


def _viewer_part(db: Session, course: TeacherCourse, viewer: User | None, taken: int) -> dict:
    mine = interested = None
    if viewer is not None:
        mine = db.scalar(select(TeacherCourseEnrollment).where(TeacherCourseEnrollment.course_id == course.id,
                                                               TeacherCourseEnrollment.student_id == viewer.id)
                         .order_by(TeacherCourseEnrollment.created_at.desc()).limit(1))
        interested = db.scalar(select(TeacherCourseInterest.id).where(TeacherCourseInterest.course_id == course.id,
                                                                      TeacherCourseInterest.student_id == viewer.id)) is not None
    can = enrollable(db, course, taken) and (mine is None or mine.status not in EN_LIVE)
    return {
        "can_enroll": can and (viewer is None or viewer.role == "STUDENT"),
        "can_interest": course.approval_status == APPROVAL_APPROVED and course.course_type == COURSE_UPCOMING
        and course.status in (ST_BALD, ST_VORBEREITUNG),
        "interested": bool(interested),
        "my_enrollment": {"id": mine.id, "status": mine.status, "created_at": mine.created_at, "activated_at": mine.activated_at,
                          "group_id": course.group_id if mine.status == EN_ACTIVE else None} if mine else None,
    }


def public_courses(db: Session, teacher_id, viewer: User | None) -> list[dict]:
    rows = list(db.scalars(select(TeacherCourse).where(TeacherCourse.teacher_id == teacher_id, TeacherCourse.approval_status == APPROVAL_APPROVED)
                           .order_by(TeacherCourse.start_date.asc().nulls_last(), TeacherCourse.created_at.desc())))
    out = []
    for r in rows:
        taken = seats_taken(db, r.id)
        out.append({**_base_out(r, taken), **_viewer_part(db, r, viewer, taken)})
    order = {ST_ANMELDUNG: 0, ST_AUSGEBUCHT: 1, ST_BALD: 2, ST_VORBEREITUNG: 3, ST_LAUFEND: 4, ST_ABGESCHLOSSEN: 5, ST_ABGESAGT: 6}
    return sorted(out, key=lambda x: order.get(x["status"], 9))


def public_course(db: Session, viewer: User, course_id) -> dict:
    course = db.get(TeacherCourse, c.parse_uuid(course_id))
    if course is None or course.approval_status != APPROVAL_APPROVED:
        raise c.err(404, "COURSE_NOT_FOUND")
    profile = c.profile_of(db, course.teacher_id)
    if not (c.listed(course.teacher, profile) or viewer.id == course.teacher_id or viewer.role in ("SUPER_ADMIN", "ADMIN")):
        raise c.err(404, "COURSE_NOT_FOUND")
    taken = seats_taken(db, course.id)
    body = {**_base_out(course, taken), **_viewer_part(db, course, viewer, taken)}
    body["teacher"]["photo_url"] = profile.photo_path if profile else None
    body["teacher"]["verified"] = bool(profile and profile.verified)
    return body


# ---------- teacher ----------

def _own(db: Session, teacher: User, course_id, lock: bool = False) -> TeacherCourse:
    q = select(TeacherCourse).where(TeacherCourse.id == c.parse_uuid(course_id))
    if lock:
        q = q.with_for_update(of=TeacherCourse)
    course = db.scalar(q)
    if course is None or course.teacher_id != teacher.id:
        raise c.err(404, "COURSE_NOT_FOUND")
    return course


def _teacher_out(db: Session, course: TeacherCourse) -> dict:
    taken = seats_taken(db, course.id)
    counts = dict(db.execute(select(TeacherCourseEnrollment.status, func.count()).where(TeacherCourseEnrollment.course_id == course.id)
                             .group_by(TeacherCourseEnrollment.status)).all())
    interests = db.scalar(select(func.count()).select_from(TeacherCourseInterest).where(TeacherCourseInterest.course_id == course.id)) or 0
    return {**_base_out(course, taken), "teacher_status": course.status, "approval_status": course.approval_status,
            "reject_reason": course.reject_reason, "submitted_at": course.submitted_at, "reviewed_at": course.reviewed_at,
            "group_id": course.group_id, "enrollment_counts": {k: int(v) for k, v in counts.items()}, "interests": int(interests),
            "created_at": course.created_at, "updated_at": course.updated_at}


def teacher_list(db: Session, teacher: User) -> list[dict]:
    rows = db.scalars(select(TeacherCourse).where(TeacherCourse.teacher_id == teacher.id).order_by(TeacherCourse.created_at.desc()))
    return [_teacher_out(db, r) for r in rows]


def teacher_get(db: Session, teacher: User, course_id) -> dict:
    return _teacher_out(db, _own(db, teacher, course_id))


def create(db: Session, teacher: User, data: dict) -> dict:
    n = db.scalar(select(func.count()).select_from(TeacherCourse).where(TeacherCourse.teacher_id == teacher.id)) or 0
    if n >= MAX_COURSES_PER_TEACHER:
        raise c.err(409, "TOO_MANY_COURSES")
    for key in ("title", "level", "course_type"):
        if key not in data:
            raise c.err(422, f"{key.upper()}_REQUIRED")
    course = TeacherCourse(teacher_id=teacher.id, title="", level=data["level"], course_type=data["course_type"], language="Deutsch",
                           status=data.get("status") or (ST_BALD if data["course_type"] == COURSE_UPCOMING else ST_VORBEREITUNG),
                           approval_status=APPROVAL_DRAFT, max_students=12, price=0)
    course.teacher = teacher
    _apply(course, data)
    db.add(course)
    db.commit()
    db.refresh(course)
    return _teacher_out(db, course)


def update(db: Session, teacher: User, course_id, data: dict) -> dict:
    course = _own(db, teacher, course_id, lock=True)
    taken = seats_taken(db, course.id)
    if "max_students" in data and isinstance(data["max_students"], int) and data["max_students"] < taken:
        raise c.err(409, "MAX_BELOW_ENROLLED")
    if "course_type" in data and data["course_type"] != course.course_type and taken:
        raise c.err(409, "TYPE_LOCKED_WITH_ENROLLMENTS")
    old_status = course.status
    changed = _apply(course, data)
    re_review = course.approval_status == APPROVAL_APPROVED and any(f in changed for f in SENSITIVE) and not c.get_settings(db)["course_auto_publish"]
    if re_review:
        course.approval_status, course.submitted_at, course.reject_reason = APPROVAL_PENDING, c.now(), None
        c.notify_admins(db, "Kurs qayta tekshiruvda / Kurs geändert", f"{c.display_name(teacher)}: «{course.title}» o'zgartirildi.",
                        "/admin/lehrer-marktplatz?tab=kurse")
    if course.status != old_status:
        _status_changed(db, course, old_status)
    db.commit()
    db.refresh(course)
    out = _teacher_out(db, course)
    out["needs_review"] = re_review
    return out


def submit(db: Session, teacher: User, course_id) -> dict:
    course = _own(db, teacher, course_id, lock=True)
    if course.approval_status not in (APPROVAL_DRAFT, APPROVAL_REJECTED, APPROVAL_UNPUBLISHED):
        raise c.err(409, "COURSE_NOT_SUBMITTABLE")
    profile = c.profile_of(db, teacher.id)
    if not c.is_teacher(teacher, profile):  # a Super Admin who is not (yet) listed as a teacher in Admin → Team
        raise c.err(409, "NOT_A_TEACHER")
    if not c.bookable(teacher, profile):
        raise c.err(409, "PROFILE_DISABLED")
    course.submitted_at, course.reject_reason = c.now(), None
    if c.get_settings(db)["course_auto_publish"]:
        _approve(db, course, None)
    else:
        course.approval_status = APPROVAL_PENDING
        c.notify_admins(db, "Yangi kurs tasdiqlash / Neuer Kurs", f"{c.display_name(teacher)}: «{course.title}» ({course.level}).",
                        "/admin/lehrer-marktplatz?tab=kurse")
    db.commit()
    db.refresh(course)
    return _teacher_out(db, course)


async def upload_image(db: Session, teacher: User, course_id, file, x, y, w) -> dict:
    course = _own(db, teacher, course_id)
    data = await file.read()
    url = media.save_course_image(data, file.filename, file.content_type, x, y, w)
    old, course.image_path = course.image_path, url
    db.commit()
    media.remove_public(old)
    return {"image_url": url}


def _status_changed(db: Session, course: TeacherCourse, old: str) -> None:
    if course.approval_status != APPROVAL_APPROVED:
        return
    if course.status == ST_ABGESAGT:
        for e in db.scalars(select(TeacherCourseEnrollment).where(TeacherCourseEnrollment.course_id == course.id,
                                                                  TeacherCourseEnrollment.status.in_((EN_ACTIVE, EN_PENDING_PAYMENT)))):
            c.notify(db, e.student_id, "Kurs bekor qilindi / Kurs abgesagt", f"«{course.title}» bekor qilindi. To'lov bo'yicha administrator bog'lanadi.",
                     f"/my-teacher/{course.teacher_id}", course=True)
    elif course.status == ST_ANMELDUNG and old != ST_ANMELDUNG:
        _announce_open(db, course)


def _announce_open(db: Session, course: TeacherCourse) -> None:
    """Interested students + current students of this teacher: the course takes enrollments now (each once)."""
    t = c.now()
    targets = set()
    for i in db.scalars(select(TeacherCourseInterest).where(TeacherCourseInterest.course_id == course.id, TeacherCourseInterest.notified_at.is_(None))):
        i.notified_at = t
        targets.add(i.student_id)
    other = select(TeacherCourse.id).where(TeacherCourse.teacher_id == course.teacher_id, TeacherCourse.id != course.id)
    targets.update(db.scalars(select(TeacherCourseEnrollment.student_id).where(TeacherCourseEnrollment.course_id.in_(other),
                                                                               TeacherCourseEnrollment.status == EN_ACTIVE)))
    for uid in targets:
        c.notify(db, uid, "Yangi kurs ochildi / Neuer Kurs", f"{c.display_name(course.teacher)}: «{course.title}» ({course.level}) — yozilish ochiq.",
                 f"/my-teacher/{course.teacher_id}?course={course.id}", course=True)


# ---------- group (classroom) ----------

def ensure_group(db: Session, course: TeacherCourse, actor_id) -> StudyGroup:
    from app.services.study_groups.access import audit
    from app.services.study_groups.groups import _set_teacher_member

    group = db.get(StudyGroup, course.group_id) if course.group_id else None
    if group is not None:
        return group
    level = course.level if course.level in ("A1", "A2", "B1", "B2", "C1") else "C1"
    group = StudyGroup(name=course.title[:120], description=(course.description or "")[:2000] or None, teacher_id=course.teacher_id, level=level,
                       mode="online", status=GROUP_ACTIVE, start_date=course.start_date, end_date=course.end_date, capacity=course.max_students,
                       created_by=actor_id, last_activity_at=c.now())
    db.add(group)
    db.flush()
    _set_teacher_member(db, group)
    audit(db, group.id, actor_id, "group.create", "group", group.id, {"teacher_course_id": str(course.id), "name": group.name})
    course.group_id = group.id
    for e in db.scalars(select(TeacherCourseEnrollment).where(TeacherCourseEnrollment.course_id == course.id, TeacherCourseEnrollment.status == EN_ACTIVE)):
        join_group(db, course, e.student_id)
    return group


def join_group(db: Session, course: TeacherCourse, student_id) -> None:
    if not course.group_id:
        return
    m = db.scalar(select(StudyGroupMember).where(StudyGroupMember.group_id == course.group_id, StudyGroupMember.user_id == student_id))
    if m is None:
        db.add(StudyGroupMember(group_id=course.group_id, user_id=student_id, role=MEMBER_STUDENT, status=MEMBER_ACTIVE, joined_at=c.now(),
                                last_read_at=c.now()))
    elif m.status != MEMBER_ACTIVE:
        m.status, m.left_at, m.joined_at = MEMBER_ACTIVE, None, c.now()


def leave_group(db: Session, course: TeacherCourse, student_id) -> None:
    if not course.group_id:
        return
    m = db.scalar(select(StudyGroupMember).where(StudyGroupMember.group_id == course.group_id, StudyGroupMember.user_id == student_id,
                                                 StudyGroupMember.role == MEMBER_STUDENT))
    if m is not None and m.status == MEMBER_ACTIVE:
        m.status, m.left_at = "removed", c.now()


# ---------- roster ----------

def students(db: Session, teacher: User, course_id) -> dict:
    course = _own(db, teacher, course_id)
    rows = list(db.scalars(select(TeacherCourseEnrollment).where(TeacherCourseEnrollment.course_id == course.id)
                           .order_by(TeacherCourseEnrollment.created_at.desc())))
    held_ids = list(db.scalars(select(VideoRoom.id).where(VideoRoom.group_id == course.group_id, VideoRoom.status == ROOM_ENDED,
                                                          VideoRoom.started_at.is_not(None)))) if course.group_id else []
    attended = dict(db.execute(select(VideoRoomParticipant.user_id, func.count()).where(
        VideoRoomParticipant.room_id.in_(held_ids or [None]), VideoRoomParticipant.joined_at.is_not(None)).group_by(VideoRoomParticipant.user_id)).all())
    orders = {o.id: o for o in db.scalars(select(SubscriptionOrder).where(SubscriptionOrder.id.in_([r.order_id for r in rows if r.order_id] or [None])))}
    items = []
    for r in rows:
        o = orders.get(r.order_id)
        items.append({
            "id": r.id, "student": {"id": r.student_id, "name": c.display_name(r.student)}, "status": r.status, "source": r.source,
            "enrolled_at": r.created_at, "activated_at": r.activated_at, "price": r.price_snapshot,
            "payment": {"status": o.status, "amount": o.final_amount} if o else ({"status": "FREE", "amount": 0} if r.source == "free" else None),
            "attendance": {"attended": int(attended.get(r.student_id, 0)), "held": len(held_ids)},
        })
    return {"course": _teacher_out(db, course), "items": items}


# ---------- admin ----------

def admin_list(db: Session, approval: str | None) -> list[dict]:
    q = select(TeacherCourse)
    if approval:
        q = q.where(TeacherCourse.approval_status == approval)
    rows = db.scalars(q.order_by(TeacherCourse.approval_status != APPROVAL_PENDING, TeacherCourse.submitted_at.desc().nulls_last(),
                                 TeacherCourse.created_at.desc()).limit(300))
    out = []
    for r in rows:
        item = _teacher_out(db, r)
        paid = db.scalar(select(func.coalesce(func.sum(SubscriptionOrder.final_amount), 0)).where(
            SubscriptionOrder.teacher_course_id == r.id, SubscriptionOrder.status == "APPROVED")) or 0
        item["revenue"] = int(paid)
        out.append(item)
    return out


def _approve(db: Session, course: TeacherCourse, admin: User | None) -> None:
    course.approval_status, course.reviewed_at, course.reject_reason = APPROVAL_APPROVED, c.now(), None
    course.reviewed_by = admin.id if admin else None
    ensure_group(db, course, admin.id if admin else course.teacher_id)
    c.notify(db, course.teacher_id, "Kurs tasdiqlandi / Kurs freigegeben", f"«{course.title}» endi talabalarga ko'rinadi.", "/teacher/meine-kurse")
    if course.status == ST_ANMELDUNG:
        _announce_open(db, course)


def admin_review(db: Session, admin: User, course_id, decision: str, reason: str | None, ip: str | None) -> dict:
    course = db.scalar(select(TeacherCourse).where(TeacherCourse.id == c.parse_uuid(course_id)).with_for_update(of=TeacherCourse))
    if course is None:
        raise c.err(404, "COURSE_NOT_FOUND")
    if decision == "approve":
        if course.approval_status not in (APPROVAL_PENDING, APPROVAL_UNPUBLISHED, APPROVAL_REJECTED):
            raise c.err(409, "COURSE_NOT_PENDING")
        _approve(db, course, admin)
    elif decision in ("reject", "unpublish"):
        text = c.one_line(reason, "reason", 500, min_len=3, required=True)
        if decision == "reject" and course.approval_status != APPROVAL_PENDING:
            raise c.err(409, "COURSE_NOT_PENDING")
        if decision == "unpublish" and course.approval_status != APPROVAL_APPROVED:
            raise c.err(409, "COURSE_NOT_APPROVED")
        course.approval_status = APPROVAL_REJECTED if decision == "reject" else APPROVAL_UNPUBLISHED
        course.reject_reason, course.reviewed_by, course.reviewed_at = text, admin.id, c.now()
        title = "Kurs rad etildi / Kurs abgelehnt" if decision == "reject" else "Kurs nashrdan olindi / Kurs zurückgezogen"
        c.notify(db, course.teacher_id, title, f"«{course.title}»: {text}", "/teacher/meine-kurse")
    else:
        raise c.err(422, "DECISION_INVALID")
    db.commit()
    write_audit(db, actor_id=admin.id, action=f"teacher_course_{decision}", target_user_id=course.teacher_id,
                details=f"course={course.id} {course.title}" + (f", reason={course.reject_reason}" if decision != "approve" else ""), ip_address=ip)
    return _teacher_out(db, course)


def admin_counts(db: Session) -> dict:
    rows = dict(db.execute(select(TeacherCourse.approval_status, func.count()).group_by(TeacherCourse.approval_status)).all())
    return {k.lower(): int(v) for k, v in rows.items()}
