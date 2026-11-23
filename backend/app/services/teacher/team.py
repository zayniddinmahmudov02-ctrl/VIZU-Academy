"""Team: teacher accounts made and managed by a SUPER_ADMIN (Admin → Team).

* A teacher is a `users` row with role TEACHER plus its `teacher_profiles` row (made here, or on first use for an account
  that got the role on the Users page). Login: the username (teacher accounts only, app.services.auth.service) or the e-mail.
* Create: full name, username (3–50 of a–z 0–9 _ . -, unique without regard to case), optional e-mail (otherwise an
  internal address on TEAM_EMAIL_DOMAIN that nobody can register), a password the admin types (at least 10 characters with
  letters and digits) or a generated one (14 characters from `secrets`), Kontroll Ja / Nein (default Nein). The password is
  stored only as a hash, returned once in the create / reset answer and has to be changed at the first login
  (`users.must_change_password`).
* Kontroll permission, status (active / inactive), password reset, groups and courses: SUPER_ADMIN only (the router), every
  change is one audit_logs row (action `team_*`, never a password) and the permission history is read back from there.
  Deactivating or resetting ends the teacher's sessions at once.
* Groups: a group always has exactly one teacher (study_groups.teacher_id, changed through the groups service so the
  teacher's member row and the group audit stay right); "remove" hands the group to the acting administrator.
  Courses: teacher_assignments (the existing table, scoping of homework / Schreiben / Sprechen).
"""

import re
import secrets
import string
from datetime import datetime, timedelta, timezone
from uuid import UUID

from email_validator import EmailNotValidError, validate_email
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.security.roles import UserRole
from app.models.audit_log import AuditLog
from app.models.course import Course
from app.models.study_group import GROUP_ARCHIVED, StudyGroup
from app.models.teacher_assignment import TeacherAssignment
from app.models.teacher_profile import TeacherProfile
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.services.auth.identifier import TEAM_EMAIL_DOMAIN, is_reserved_email
from app.services.study_groups import groups as group_service

USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,50}$")
PASSWORD_MIN = 10
GENERATED_LENGTH = 14
ALPHABET = "".join(c for c in string.ascii_letters + string.digits if c not in "0OIl1")
NEW_DAYS = 30
HISTORY_ACTIONS = ("team_teacher_created", "team_teacher_updated", "team_control_changed", "team_status_changed", "team_password_reset",
                   "team_group_assigned", "team_group_removed", "team_course_assigned", "team_course_removed")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _bad(code: str, status: int = 422) -> HTTPException:
    return HTTPException(status_code=status, detail=code)


def _aware(dt):
    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def display_name(user: User) -> str:
    parts = [p for p in (user.first_name, user.last_name) if p]
    return " ".join(parts) if parts else user.username


def generate_password() -> str:
    while True:
        value = "".join(secrets.choice(ALPHABET) for _ in range(GENERATED_LENGTH))
        if any(c.isdigit() for c in value) and any(c.isalpha() for c in value):
            return value


def check_password(value: str) -> str:
    if len(value) < PASSWORD_MIN or len(value) > 128 or not any(c.isdigit() for c in value) or not any(c.isalpha() for c in value):
        raise _bad("PASSWORD_TOO_WEAK: mindestens 10 Zeichen mit Buchstaben und Ziffern")
    return value


def _username(db: Session, value: str, exclude: UUID | None = None) -> str:
    name = (value or "").strip().lower()
    if not USERNAME_RE.match(name):
        raise _bad("USERNAME_INVALID: 3–50 Zeichen, nur a–z, 0–9, _ . -")
    stmt = select(User.id).where(func.lower(User.username) == name)
    if exclude is not None:
        stmt = stmt.where(User.id != exclude)
    if db.scalar(stmt) is not None:
        raise _bad("USERNAME_TAKEN", 409)
    return name


def _email(db: Session, value: str | None, username: str, exclude: UUID | None = None) -> str:
    if not value or not value.strip():
        return f"{username}@{TEAM_EMAIL_DOMAIN}"
    try:
        email = validate_email(value.strip(), check_deliverability=False).normalized.lower()
    except EmailNotValidError:
        raise _bad("EMAIL_INVALID")
    if is_reserved_email(email):
        raise _bad("EMAIL_INVALID")
    stmt = select(User.id).where(func.lower(User.email) == email)
    if exclude is not None:
        stmt = stmt.where(User.id != exclude)
    if db.scalar(stmt) is not None:
        raise _bad("EMAIL_TAKEN", 409)
    return email


def _split_name(full_name: str) -> tuple[str, str | None]:
    parts = " ".join((full_name or "").split()).split(" ")
    if not parts or not parts[0]:
        raise _bad("NAME_REQUIRED")
    return parts[0][:100], (" ".join(parts[1:])[:100] or None)


def _audit(db: Session, actor: User, action: str, target: User, details: str, ip: str | None) -> None:
    db.add(AuditLog(actor_id=actor.id, target_user_id=target.id, action=action, details=details[:1000], ip_address=ip))


def profile(db: Session, user: User, *, create: bool = True) -> TeacherProfile | None:
    row = db.scalar(select(TeacherProfile).where(TeacherProfile.user_id == user.id))
    if row is None and create and user.role == UserRole.TEACHER:
        row = TeacherProfile(user_id=user.id, can_access_student_control=False)
        db.add(row)
        try:
            db.commit()
        except IntegrityError:  # made by a parallel request
            db.rollback()
            row = db.scalar(select(TeacherProfile).where(TeacherProfile.user_id == user.id))
    return row


def can_access_control(db: Session, user: User) -> bool:
    if user.role == UserRole.SUPER_ADMIN:
        return True
    if user.role != UserRole.TEACHER:
        return False
    return bool(db.scalar(select(TeacherProfile.can_access_student_control).where(TeacherProfile.user_id == user.id)))


def _teacher_or_404(db: Session, teacher_id: UUID) -> User:
    user = db.get(User, teacher_id)
    if user is None or user.role != UserRole.TEACHER:
        raise _bad("TEACHER_NOT_FOUND", 404)
    return user


def _status(user: User) -> str:
    if user.is_banned:
        return "blocked"
    return "active" if user.is_active else "inactive"


def _counts(db: Session, ids: list) -> tuple[dict, dict]:
    if not ids:
        return {}, {}
    groups = dict(db.execute(select(StudyGroup.teacher_id, func.count()).where(StudyGroup.teacher_id.in_(ids), StudyGroup.status != GROUP_ARCHIVED)
                             .group_by(StudyGroup.teacher_id)).all())
    courses = dict(db.execute(select(TeacherAssignment.teacher_id, func.count()).where(TeacherAssignment.teacher_id.in_(ids))
                              .group_by(TeacherAssignment.teacher_id)).all())
    return groups, courses


def _item(user: User, prof: TeacherProfile | None, groups: int, courses: int) -> dict:
    return {"id": user.id, "name": display_name(user), "first_name": user.first_name, "last_name": user.last_name, "username": user.username,
            "email": None if user.email.endswith("@" + TEAM_EMAIL_DOMAIN) else user.email, "status": _status(user),
            "can_access_student_control": bool(prof and prof.can_access_student_control), "group_count": groups, "course_count": courses,
            "created_at": _aware(user.created_at), "last_login_at": _aware(user.last_login), "must_change_password": user.must_change_password}


def overview(db: Session, now: datetime | None = None) -> dict:
    now = now or _now()
    teacher = User.role == UserRole.TEACHER
    total, active, new = db.execute(select(func.count(), func.count().filter(User.is_active.is_(True), User.is_banned.is_(False)),
                                           func.count().filter(User.created_at >= now - timedelta(days=NEW_DAYS))).where(teacher)).one()
    control = db.scalar(select(func.count()).select_from(User).join(TeacherProfile, TeacherProfile.user_id == User.id)
                        .where(teacher, TeacherProfile.can_access_student_control.is_(True))) or 0
    return {"total": total, "active": active, "inactive": total - active, "with_control": control, "without_control": total - control,
            "new": new, "new_days": NEW_DAYS}


def list_teachers(db: Session, *, search: str | None = None, status: str | None = None, control: str | None = None,
                  page: int = 1, page_size: int = 25) -> dict:
    page, page_size = max(1, page), max(1, min(page_size, 100))
    stmt = select(User, TeacherProfile).outerjoin(TeacherProfile, TeacherProfile.user_id == User.id).where(User.role == UserRole.TEACHER)
    if search and search.strip():
        q = "%" + search.strip().lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        stmt = stmt.where(or_(func.lower(User.username).like(q, escape="\\"), func.lower(User.email).like(q, escape="\\"),
                              func.lower(func.concat_ws(" ", User.first_name, User.last_name)).like(q, escape="\\")))
    if status == "active":
        stmt = stmt.where(User.is_active.is_(True), User.is_banned.is_(False))
    elif status == "inactive":
        stmt = stmt.where(or_(User.is_active.is_(False), User.is_banned.is_(True)))
    if control == "yes":
        stmt = stmt.where(TeacherProfile.can_access_student_control.is_(True))
    elif control == "no":
        stmt = stmt.where(or_(TeacherProfile.id.is_(None), TeacherProfile.can_access_student_control.is_(False)))
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.execute(stmt.order_by(User.created_at.desc()).limit(page_size).offset((page - 1) * page_size)).all()
    groups, courses = _counts(db, [u.id for u, _p in rows])
    return {"items": [_item(u, p, groups.get(u.id, 0), courses.get(u.id, 0)) for u, p in rows], "total": total, "page": page,
            "page_size": page_size}


def detail(db: Session, teacher_id: UUID) -> dict:
    user = _teacher_or_404(db, teacher_id)
    prof = profile(db, user)
    groups = [{"id": g.id, "name": g.name, "level": g.level, "status": g.status}
              for g in db.scalars(select(StudyGroup).where(StudyGroup.teacher_id == user.id).order_by(StudyGroup.name))]
    courses = [{"assignment_id": a.id, "course_id": c.id, "title": c.title, "level": c.level}
               for a, c in db.execute(select(TeacherAssignment, Course).join(Course, Course.id == TeacherAssignment.course_id)
                                      .where(TeacherAssignment.teacher_id == user.id).order_by(Course.level, Course.title))]
    actors = {}
    history = []
    for row in db.scalars(select(AuditLog).where(AuditLog.target_user_id == user.id, AuditLog.action.in_(HISTORY_ACTIONS))
                          .order_by(AuditLog.created_at.desc()).limit(50)):
        if row.actor_id not in actors:
            actor = db.get(User, row.actor_id) if row.actor_id else None
            actors[row.actor_id] = display_name(actor) if actor else None
        history.append({"id": row.id, "action": row.action, "details": row.details, "actor": actors[row.actor_id], "at": _aware(row.created_at)})
    return {**_item(user, prof, len([g for g in groups if g["status"] != GROUP_ARCHIVED]), len(courses)), "groups": groups, "courses": courses,
            "history": history, "control_changed_at": _aware(prof.control_changed_at) if prof else None}


def create(db: Session, actor: User, data: dict, ip: str | None) -> tuple[dict, str]:
    first, last = _split_name(data.get("full_name", ""))
    username = _username(db, data.get("username", ""))
    email = _email(db, data.get("email"), username)
    password = check_password(data["password"]) if data.get("password") else generate_password()
    control = bool(data.get("can_access_student_control", False))
    user = User(email=email, username=username, first_name=first, last_name=last, password_hash=hash_password(password),
                role=UserRole.TEACHER, is_active=True, is_verified=True, must_change_password=True, preferred_language="de")
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise _bad("USERNAME_TAKEN", 409)
    db.add(TeacherProfile(user_id=user.id, can_access_student_control=control, created_by=actor.id,
                          control_changed_at=_now() if control else None, control_changed_by=actor.id if control else None))
    _audit(db, actor, "team_teacher_created", user, f"username={username}; kontroll={'Ja' if control else 'Nein'}; "
                                                    f"password={'set by admin' if data.get('password') else 'generated'}", ip)
    db.commit()
    return detail(db, user.id), password


def update(db: Session, actor: User, teacher_id: UUID, data: dict, ip: str | None) -> dict:
    user = _teacher_or_404(db, teacher_id)
    changed = []
    if data.get("full_name") is not None:
        first, last = _split_name(data["full_name"])
        if (first, last) != (user.first_name, user.last_name):
            user.first_name, user.last_name = first, last
            changed.append("name")
    if data.get("username") is not None:
        name = _username(db, data["username"], exclude=user.id)
        if name != user.username:
            placeholder = user.email.endswith("@" + TEAM_EMAIL_DOMAIN)
            user.username = name
            if placeholder:
                user.email = f"{name}@{TEAM_EMAIL_DOMAIN}"
            changed.append("username")
    if "email" in data:
        email = _email(db, data["email"], user.username, exclude=user.id)
        if email != user.email:
            user.email = email
            changed.append("email")
    if changed:
        _audit(db, actor, "team_teacher_updated", user, "changed=" + ",".join(changed), ip)
        db.commit()
    return detail(db, user.id)


def set_control(db: Session, actor: User, teacher_id: UUID, enabled: bool, ip: str | None) -> dict:
    user = _teacher_or_404(db, teacher_id)
    prof = profile(db, user)
    if prof.can_access_student_control != enabled:
        prof.can_access_student_control = enabled
        prof.control_changed_at, prof.control_changed_by = _now(), actor.id
        _audit(db, actor, "team_control_changed", user, f"kontroll: {'Nein → Ja' if enabled else 'Ja → Nein'}", ip)
        db.commit()
    return detail(db, user.id)


def _end_sessions(db: Session, user: User) -> None:
    user.tokens_valid_after = _now()
    RefreshTokenRepository(db).delete_all_for_user(str(user.id))


def set_status(db: Session, actor: User, teacher_id: UUID, active: bool, ip: str | None) -> dict:
    user = _teacher_or_404(db, teacher_id)
    if user.is_active != active:
        user.is_active = active
        if not active:
            _end_sessions(db, user)
        _audit(db, actor, "team_status_changed", user, "status: " + ("inaktiv → aktiv" if active else "aktiv → inaktiv"), ip)
        db.commit()
    return detail(db, user.id)


def reset_password(db: Session, actor: User, teacher_id: UUID, password: str | None, ip: str | None) -> tuple[dict, str]:
    user = _teacher_or_404(db, teacher_id)
    value = check_password(password) if password else generate_password()
    user.password_hash = hash_password(value)
    user.must_change_password = True
    _end_sessions(db, user)
    _audit(db, actor, "team_password_reset", user, "password=" + ("set by admin" if password else "generated"), ip)
    db.commit()
    return detail(db, user.id), value


def assign_group(db: Session, actor: User, teacher_id: UUID, group_id: UUID, ip: str | None) -> dict:
    user = _teacher_or_404(db, teacher_id)
    group = db.get(StudyGroup, group_id)
    if group is None:
        raise _bad("GROUP_NOT_FOUND", 404)
    if group.teacher_id != user.id:
        group_service.update(db, actor, group.id, {"teacher_id": user.id})
        _audit(db, actor, "team_group_assigned", user, f"group={group.id} ({group.name})", ip)
        db.commit()
    return detail(db, user.id)


def remove_group(db: Session, actor: User, teacher_id: UUID, group_id: UUID, ip: str | None) -> dict:
    user = _teacher_or_404(db, teacher_id)
    group = db.get(StudyGroup, group_id)
    if group is None or group.teacher_id != user.id:
        raise _bad("GROUP_NOT_FOUND", 404)
    group_service.update(db, actor, group.id, {"teacher_id": actor.id})
    _audit(db, actor, "team_group_removed", user, f"group={group.id} ({group.name}) -> {actor.username}", ip)
    db.commit()
    return detail(db, user.id)


def assign_course(db: Session, actor: User, teacher_id: UUID, course_id: UUID, ip: str | None) -> dict:
    user = _teacher_or_404(db, teacher_id)
    course = db.get(Course, course_id)
    if course is None:
        raise _bad("COURSE_NOT_FOUND", 404)
    exists = db.scalar(select(TeacherAssignment.id).where(TeacherAssignment.teacher_id == user.id, TeacherAssignment.course_id == course.id))
    if exists is None:
        db.add(TeacherAssignment(teacher_id=user.id, course_id=course.id))
        _audit(db, actor, "team_course_assigned", user, f"course={course.id} ({course.level} {course.title})", ip)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
    return detail(db, user.id)


def remove_course(db: Session, actor: User, teacher_id: UUID, course_id: UUID, ip: str | None) -> dict:
    user = _teacher_or_404(db, teacher_id)
    row = db.scalar(select(TeacherAssignment).where(TeacherAssignment.teacher_id == user.id, TeacherAssignment.course_id == course_id))
    if row is None:
        raise _bad("COURSE_NOT_FOUND", 404)
    course = db.get(Course, course_id)
    db.delete(row)
    _audit(db, actor, "team_course_removed", user, f"course={course_id} ({course.level} {course.title})" if course else f"course={course_id}", ip)
    db.commit()
    return detail(db, user.id)


def choices(db: Session) -> dict:
    """Groups (with their current teacher) and courses for the assignment pickers."""
    teachers = {u.id: display_name(u) for u in db.scalars(select(User).where(User.role.in_((UserRole.TEACHER, UserRole.SUPER_ADMIN))))}
    groups = [{"id": g.id, "name": g.name, "level": g.level, "status": g.status, "teacher_id": g.teacher_id, "teacher": teachers.get(g.teacher_id)}
              for g in db.scalars(select(StudyGroup).where(StudyGroup.status != GROUP_ARCHIVED).order_by(StudyGroup.level, StudyGroup.name))]
    courses = [{"id": c.id, "title": c.title, "level": c.level} for c in db.scalars(select(Course).order_by(Course.level, Course.order_index))]
    return {"groups": groups, "courses": courses}
