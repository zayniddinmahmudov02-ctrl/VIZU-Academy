"""Teacher catalog, public profile, own profile, admin teacher management.

Catalog (every logged-in user): teachers that are `common.listed` — card = photo + name only; search by first / last name,
filters language, level, courses (teachers with an open course), activity (teaching now); page size ≤ 48; order: verified,
rated, rating, name.

Student numbers on the profile (real data only, every student counted once even with several courses / groups):
* current = students with an ACTIVE enrollment in one of the teacher's courses ∪ active student members of the teacher's
  active study groups;
* total = students ever enrolled (ACTIVE / COMPLETED; not cancelled, rejected or refunded) ∪ every student who was ever a
  member of one of the teacher's groups. Only accounts with role STUDENT count.

Career figure (2026-11-25, owner): the teacher may enter `students_taught_total` (whole career, before VIZU too, 0 … 1 000 000);
the profile shows it as teacher-reported "students so far" — never below the VIZU total — next to the computed VIZU numbers.

Own profile: the teacher edits photo, name, headline, bio, experience, methodology, exam preparation, languages, levels.
Verification, catalog visibility, disabling and the rating are never editable by the teacher (admin / server only)."""

from sqlalchemy import case, exists, func, literal, or_, select, union
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.security.roles import UserRole
from app.models.study_group import GROUP_ACTIVE, MEMBER_ACTIVE, MEMBER_STUDENT, StudyGroup, StudyGroupMember
from app.models.teacher_market import (
    APPROVAL_APPROVED,
    APPROVAL_PENDING,
    CERT_PENDING,
    CERT_VERIFIED,
    EN_ACTIVE,
    EN_COMPLETED,
    ST_ANMELDUNG,
    ST_LAUFEND,
    TeacherCertificate,
    TeacherCourse,
    TeacherCourseEnrollment,
)
from app.models.teacher_profile import TeacherProfile
from app.models.user import User
from app.services.teacher_market import common as c
from app.services.teacher_market import media

MAX_PAGE = 48


def student_stats(db: Session, teacher_id) -> dict:
    courses = select(TeacherCourse.id).where(TeacherCourse.teacher_id == teacher_id)
    groups_all = select(StudyGroup.id).where(StudyGroup.teacher_id == teacher_id)
    groups_active = groups_all.where(StudyGroup.status == GROUP_ACTIVE)

    def count(*parts) -> int:
        u = union(*parts).subquery()
        return int(db.scalar(select(func.count()).select_from(u).join(User, User.id == u.c.uid).where(User.role == UserRole.STUDENT)) or 0)

    current = count(
        select(TeacherCourseEnrollment.student_id.label("uid")).where(TeacherCourseEnrollment.course_id.in_(courses),
                                                                      TeacherCourseEnrollment.status == EN_ACTIVE),
        select(StudyGroupMember.user_id.label("uid")).where(StudyGroupMember.group_id.in_(groups_active), StudyGroupMember.role == MEMBER_STUDENT,
                                                            StudyGroupMember.status == MEMBER_ACTIVE),
    )
    total = count(
        select(TeacherCourseEnrollment.student_id.label("uid")).where(TeacherCourseEnrollment.course_id.in_(courses),
                                                                      TeacherCourseEnrollment.status.in_((EN_ACTIVE, EN_COMPLETED))),
        select(StudyGroupMember.user_id.label("uid")).where(StudyGroupMember.group_id.in_(groups_all), StudyGroupMember.role == MEMBER_STUDENT),
    )
    return {"current_students": current, "total_students": total}


def _stats_with_career(stats: dict, profile: TeacherProfile | None) -> dict:
    """+ the career figure: the teacher's own `students_taught_total` (before VIZU too), never shown below the VIZU total;
    `career_reported` tells the UI whether the figure comes from the teacher (labelled so) or only from VIZU."""
    reported = profile.students_taught_total if profile is not None else None
    career = max(reported, stats["total_students"]) if reported is not None else stats["total_students"]
    return {**stats, "career_students": career, "career_reported": reported is not None}


def card(user: User, profile: TeacherProfile | None) -> dict:
    return {"id": user.id, "name": c.display_name(user), "photo_url": profile.photo_path if profile else None}


def _open_course_exists(teacher_col, statuses: tuple[str, ...] | None = None):
    cond = [TeacherCourse.teacher_id == teacher_col, TeacherCourse.approval_status == APPROVAL_APPROVED]
    if statuses:
        cond.append(TeacherCourse.status.in_(statuses))
    return exists(select(TeacherCourse.id).where(*cond))


def catalog(db: Session, q: str | None, language: str | None, level: str | None, courses: str | None, activity: str | None,
            page: int, page_size: int) -> dict:
    page, page_size = max(1, page), max(1, min(MAX_PAGE, page_size))
    stmt = (select(User, TeacherProfile).outerjoin(TeacherProfile, TeacherProfile.user_id == User.id)
            .where(c.teaching_clause(), User.is_active.is_(True), User.is_banned.is_(False),
                   func.coalesce(TeacherProfile.profile_disabled, False).is_(False), func.coalesce(TeacherProfile.catalog_hidden, False).is_(False)))
    if q and q.strip():
        like = "%" + q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        full = func.concat(func.coalesce(User.first_name, ""), literal(" "), func.coalesce(User.last_name, ""))
        stmt = stmt.where(or_(User.first_name.ilike(like), User.last_name.ilike(like), full.ilike(like)))
    if language:
        stmt = stmt.where(TeacherProfile.languages.contains([c.language(language)]))
    if level:
        stmt = stmt.where(TeacherProfile.levels.contains([c.level(level)]))
    if courses == "open":
        stmt = stmt.where(_open_course_exists(User.id, (ST_ANMELDUNG,)))
    elif courses == "any":
        stmt = stmt.where(_open_course_exists(User.id))
    if activity == "teaching":
        stmt = stmt.where(_open_course_exists(User.id, (ST_ANMELDUNG, ST_LAUFEND)))
    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = db.execute(stmt.order_by(func.coalesce(TeacherProfile.verified, False).desc(),
                                    case((func.coalesce(TeacherProfile.rating_count, 0) > 0, 0), else_=1),
                                    func.coalesce(TeacherProfile.rating_avg, 0).desc(),
                                    func.lower(func.coalesce(User.first_name, User.username)))
                      .offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [card(u, p) for u, p in rows], "total": total, "page": page, "page_size": page_size}


def _certificates(db: Session, teacher_id, include_all: bool) -> list[dict]:
    q = select(TeacherCertificate).where(TeacherCertificate.teacher_id == teacher_id)
    if not include_all:
        q = q.where(TeacherCertificate.status == CERT_VERIFIED)
    rows = db.scalars(q.order_by(TeacherCertificate.issued_on.desc().nulls_last(), TeacherCertificate.created_at.desc()))
    out = []
    for r in rows:
        item = {"id": r.id, "title": r.title, "issuer": r.issuer, "issued_on": r.issued_on, "level": r.level, "file_type": r.file_type,
                "file_url": f"/api/v1/my-teacher/certificates/{r.id}/file", "verified": r.status == CERT_VERIFIED}
        if include_all:
            item.update({"status": r.status, "reject_reason": r.reject_reason, "reviewed_at": r.reviewed_at})
        out.append(item)
    return out


def _profile_body(db: Session, user: User, profile: TeacherProfile | None, viewer: User | None, own: bool) -> dict:
    from app.services.teacher_market import courses as courses_svc
    from app.services.teacher_market import reviews as reviews_svc

    p = profile
    return {
        "id": user.id, "name": c.display_name(user), "first_name": user.first_name, "last_name": user.last_name,
        "photo_url": p.photo_path if p else None, "headline": p.headline if p else None,
        "languages": (p.languages or []) if p else [], "levels": (p.levels or []) if p else [], "verified": bool(p and p.verified),
        "experience": {
            "years": p.experience_years if p else None, "teaching_since": p.teaching_since if p else None,
            "students_taught_total": p.students_taught_total if p else None,
            "specialization": p.specialization if p else None, "methodology": p.methodology if p else None,
            "exam_prep": (p.exam_prep or []) if p else [], "bio": p.bio if p else None,
        },
        "stats": _stats_with_career(student_stats(db, user.id), p),
        "certificates": _certificates(db, user.id, include_all=own),
        "rating": reviews_svc.summary(db, user.id, p),
        "courses": courses_svc.public_courses(db, user.id, viewer),
        "review": reviews_svc.viewer_options(db, viewer, user.id) if viewer is not None and not own else None,
    }


def public_profile(db: Session, viewer: User, teacher_id) -> dict:
    teacher = db.get(User, c.parse_uuid(teacher_id))
    profile = c.profile_of(db, teacher.id) if teacher is not None else None
    staff = viewer.role in (UserRole.SUPER_ADMIN, UserRole.ADMIN)
    if teacher is None or not (c.listed(teacher, profile) or (staff and c.teacher_account_ok(teacher, profile))
                               or (viewer.id == teacher.id and c.is_teacher(teacher, profile))):
        raise c.err(404, "TEACHER_NOT_FOUND")
    return _profile_body(db, teacher, profile, viewer, own=False)


# ---------- own profile (teacher panel) ----------

def own_profile(db: Session, teacher: User) -> dict:
    profile = c.profile_of(db, teacher.id, create=True)
    db.commit()
    body = _profile_body(db, teacher, profile, None, own=True)
    body["admin"] = {"catalog_hidden": profile.catalog_hidden, "profile_disabled": profile.profile_disabled, "verified": profile.verified,
                     "listed": c.listed(teacher, profile)}
    body["choices"] = {"languages": list(c.LANGUAGES), "levels": ["A1", "A2", "B1", "B2", "C1", "C2"], "exams": list(c.EXAMS)}
    return body


def update_own(db: Session, teacher: User, data: dict) -> dict:
    p = c.profile_of(db, teacher.id, create=True)
    if "first_name" in data:
        teacher.first_name = c.one_line(data["first_name"], "first_name", 100, min_len=1, required=True)
    if "last_name" in data:
        teacher.last_name = c.one_line(data["last_name"], "last_name", 100)
    if "headline" in data:
        p.headline = c.one_line(data["headline"], "headline", 160)
    if "bio" in data:
        p.bio = c.block(data["bio"], 4000)
    if "specialization" in data:
        p.specialization = c.one_line(data["specialization"], "specialization", 300)
    if "methodology" in data:
        p.methodology = c.block(data["methodology"], 4000)
    if "experience_years" in data:
        v = data["experience_years"]
        if v is not None and (not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 70):
            raise c.err(422, "EXPERIENCE_INVALID")
        p.experience_years = v
    if "teaching_since" in data:
        v = data["teaching_since"]
        if v is not None and (not isinstance(v, int) or isinstance(v, bool) or not 1950 <= v <= c.now().year):
            raise c.err(422, "TEACHING_SINCE_INVALID")
        p.teaching_since = v
    if "students_taught_total" in data:
        v = data["students_taught_total"]
        if v is not None and (not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 1_000_000):
            raise c.err(422, "STUDENTS_TAUGHT_INVALID")
        p.students_taught_total = v
    if "exam_prep" in data:
        p.exam_prep = c.choices(data["exam_prep"], c.EXAMS, "exam_prep")
    if "languages" in data:
        p.languages = c.choices(data["languages"], c.LANGUAGES, "languages")
    if "levels" in data:
        p.levels = c.choices(data["levels"], ("A1", "A2", "B1", "B2", "C1", "C2"), "levels")
    p.profile_updated_at = c.now()
    db.commit()
    return own_profile(db, teacher)


async def upload_photo(db: Session, teacher: User, file, x, y, w) -> dict:
    data = await file.read()
    url = media.save_photo(data, file.filename, file.content_type, x, y, w)
    p = c.profile_of(db, teacher.id, create=True)
    old, p.photo_path, p.profile_updated_at = p.photo_path, url, c.now()
    db.commit()
    media.remove_public(old)
    return {"photo_url": url}


def remove_photo(db: Session, teacher: User) -> dict:
    p = c.profile_of(db, teacher.id, create=True)
    old, p.photo_path = p.photo_path, None
    db.commit()
    media.remove_public(old)
    return {"photo_url": None}


# ---------- admin ----------

def admin_teachers(db: Session, q: str | None, flag: str | None, page: int, page_size: int) -> dict:
    page, page_size = max(1, page), max(1, min(100, page_size))
    stmt = select(User, TeacherProfile).outerjoin(TeacherProfile, TeacherProfile.user_id == User.id).where(c.teaching_clause())
    if q and q.strip():
        like = "%" + q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        stmt = stmt.where(or_(User.first_name.ilike(like), User.last_name.ilike(like), User.username.ilike(like)))
    if flag == "hidden":
        stmt = stmt.where(TeacherProfile.catalog_hidden.is_(True))
    elif flag == "disabled":
        stmt = stmt.where(TeacherProfile.profile_disabled.is_(True))
    elif flag == "verified":
        stmt = stmt.where(TeacherProfile.verified.is_(True))
    elif flag == "unverified":
        stmt = stmt.where(func.coalesce(TeacherProfile.verified, False).is_(False))
    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = db.execute(stmt.order_by(func.lower(func.coalesce(User.first_name, User.username))).offset((page - 1) * page_size).limit(page_size)).all()
    ids = [u.id for u, _ in rows] or [None]
    courses = dict(db.execute(select(TeacherCourse.teacher_id, func.count()).where(TeacherCourse.teacher_id.in_(ids)).group_by(TeacherCourse.teacher_id)).all())
    pending_courses = dict(db.execute(select(TeacherCourse.teacher_id, func.count()).where(
        TeacherCourse.teacher_id.in_(ids), TeacherCourse.approval_status == APPROVAL_PENDING).group_by(TeacherCourse.teacher_id)).all())
    pending_certs = dict(db.execute(select(TeacherCertificate.teacher_id, func.count()).where(
        TeacherCertificate.teacher_id.in_(ids), TeacherCertificate.status == CERT_PENDING).group_by(TeacherCertificate.teacher_id)).all())
    items = []
    for u, p in rows:
        items.append({
            "id": u.id, "name": c.display_name(u), "username": u.username, "photo_url": p.photo_path if p else None,
            "admin_account": u.role == UserRole.SUPER_ADMIN,
            "account_active": bool(u.is_active) and not u.is_banned, "catalog_hidden": bool(p and p.catalog_hidden),
            "profile_disabled": bool(p and p.profile_disabled), "verified": bool(p and p.verified),
            "listed": c.listed(u, p), "rating_avg": float(p.rating_avg) if p else 0.0, "rating_count": p.rating_count if p else 0,
            "profile_complete": bool(p and p.photo_path and p.headline and (p.languages or [])),
            "courses": int(courses.get(u.id, 0)), "pending_courses": int(pending_courses.get(u.id, 0)),
            "pending_certificates": int(pending_certs.get(u.id, 0)),
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def admin_update_teacher(db: Session, admin: User, teacher_id, data: dict, ip: str | None) -> dict:
    teacher = db.get(User, c.parse_uuid(teacher_id))
    if teacher is None or not c.is_teacher(teacher, c.profile_of(db, teacher.id)):
        raise c.err(404, "TEACHER_NOT_FOUND")
    p = c.profile_of(db, teacher.id, create=True)
    changes = []
    for key in ("catalog_hidden", "profile_disabled", "verified"):
        if key in data and isinstance(data[key], bool) and getattr(p, key) != data[key]:
            setattr(p, key, data[key])
            changes.append(f"{key}={data[key]}")
    if not changes:
        return {"changed": []}
    if "verified" in data:
        p.verified_at, p.verified_by = (c.now(), admin.id) if p.verified else (None, None)
        if p.verified:
            c.notify(db, teacher.id, "Verified Teacher", "Profilingiz tasdiqlandi: endi «Verified Teacher» belgisi ko'rinadi.", "/teacher/profil")
    if data.get("profile_disabled") is True:
        c.notify(db, teacher.id, "Profil o'chirildi / Profil deaktiviert",
                 "Administrator profilingizni vaqtincha o'chirdi: katalogda ko'rinmaydi, yangi yozilish yo'q.", "/teacher/profil")
    db.commit()
    write_audit(db, actor_id=admin.id, action="teacher_market_profile_flags", target_user_id=teacher.id, details=", ".join(changes), ip_address=ip)
    return {"changed": changes}


def admin_counts(db: Session) -> dict:
    teachers = select(User.id).outerjoin(TeacherProfile, TeacherProfile.user_id == User.id).where(c.teaching_clause())
    hidden = db.scalar(select(func.count()).select_from(TeacherProfile).where(TeacherProfile.user_id.in_(teachers), or_(
        TeacherProfile.catalog_hidden.is_(True), TeacherProfile.profile_disabled.is_(True)))) or 0
    total = db.scalar(select(func.count()).select_from(teachers.subquery())) or 0
    verified = db.scalar(select(func.count()).select_from(TeacherProfile).where(TeacherProfile.user_id.in_(teachers),
                                                                                  TeacherProfile.verified.is_(True))) or 0
    pending_certs = db.scalar(select(func.count()).select_from(TeacherCertificate).where(TeacherCertificate.status == CERT_PENDING)) or 0
    return {"teachers": int(total), "hidden_or_disabled": int(hidden), "verified": int(verified), "pending_certificates": int(pending_certs)}


