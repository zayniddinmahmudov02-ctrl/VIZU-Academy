"""Shared rules of the My Teacher marketplace.

* A teacher is listed / has a profile only while the account is role TEACHER, active, not banned and the profile is not
  disabled by a SUPER_ADMIN; `catalog_hidden` keeps the teacher out of the catalog AND the public profile (students get 404).
* Text fields are trimmed, whitespace-normalised where they are one line, and length-capped; list fields only take values
  from the fixed choices below. Errors are UPPER_SNAKE codes (HTTPException detail).
* Notifications are rows of the existing notifications table, written in the caller's transaction (`notify`)."""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.security.roles import UserRole
from app.models.app_setting import AppSetting
from app.models.notification import TYPE_COURSE, TYPE_INFORMATION, Notification
from app.models.teacher_market import LEVELS
from app.models.teacher_profile import TeacherProfile
from app.models.user import User

TASHKENT = timezone(timedelta(hours=5))
LANGUAGES = ("Deutsch", "Usbekisch", "Russisch", "Englisch")
EXAMS = ("Goethe-Zertifikat", "telc", "TestDaF", "ÖSD", "DSH", "DTZ", "VIZU-Multilevel", "CEFR")
SETTINGS_KEY = "teacher_market"
DEFAULT_SETTINGS = {"course_auto_publish": False}


def now() -> datetime:
    return datetime.now(timezone.utc)


def err(code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def display_name(user: User | None) -> str:
    if user is None:
        return "—"
    parts = [p.strip() for p in (user.first_name, user.last_name) if p and p.strip()]
    return " ".join(parts) if parts else user.username


def short_name(user: User | None) -> str:
    """How a student appears under a review: first name + initial of the last name — never e-mail, phone or username."""
    if user is None:
        return "—"
    first = (user.first_name or "").strip()
    last = (user.last_name or "").strip()
    if first:
        return f"{first} {last[0]}." if last else first
    return "VIZU Schüler"


def is_super_admin(user: User) -> bool:
    return user.role == UserRole.SUPER_ADMIN


def require_student(user: User) -> None:
    if user.role != UserRole.STUDENT:
        raise err(403, "STUDENT_ONLY")


def teacher_account_ok(user: User | None) -> bool:
    return user is not None and user.role == UserRole.TEACHER and bool(user.is_active) and not user.is_banned


def profile_of(db: Session, teacher_id, create: bool = False) -> TeacherProfile | None:
    p = db.scalar(select(TeacherProfile).where(TeacherProfile.user_id == teacher_id))
    if p is None and create:
        # The first visit often fires two requests at once (profile + another panel): INSERT … ON CONFLICT DO NOTHING keeps it
        # to one row without a unique-violation 500; the loser of the race then reads the winner's row.
        db.execute(pg_insert(TeacherProfile).values(
            id=uuid4(), user_id=teacher_id, can_access_student_control=False, catalog_hidden=False, profile_disabled=False, verified=False,
            rating_avg=0, rating_count=0).on_conflict_do_nothing(index_elements=["user_id"]))
        p = db.scalar(select(TeacherProfile).where(TeacherProfile.user_id == teacher_id).execution_options(populate_existing=True))
    return p


def listed(user: User | None, profile: TeacherProfile | None) -> bool:
    """Visible to students: an active teacher account whose profile is neither disabled nor hidden."""
    return teacher_account_ok(user) and not (profile is not None and (profile.profile_disabled or profile.catalog_hidden))


def bookable(user: User | None, profile: TeacherProfile | None) -> bool:
    """New enrollments / special lessons need an active account and a profile that is not disabled (hidden still teaches)."""
    return teacher_account_ok(user) and not (profile is not None and profile.profile_disabled)


def one_line(value, field: str, max_len: int, min_len: int = 0, required: bool = False) -> str | None:
    text = " ".join(str(value or "").split())
    if not text:
        if required:
            raise err(422, f"{field.upper()}_REQUIRED")
        return None
    if len(text) < min_len:
        raise err(422, f"{field.upper()}_TOO_SHORT")
    return text[:max_len]


def block(value, max_len: int) -> str | None:
    text = str(value or "").replace("\r\n", "\n").strip()
    return text[:max_len] or None


def choices(values, allowed: tuple[str, ...], field: str, max_items: int = 10) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise err(422, f"{field.upper()}_INVALID")
    out = []
    for v in values:
        if v not in allowed:
            raise err(422, f"{field.upper()}_INVALID")
        if v not in out:
            out.append(v)
    return out[:max_items]


def level(value) -> str:
    if value not in LEVELS:
        raise err(422, "LEVEL_INVALID")
    return value


def language(value) -> str:
    if value not in LANGUAGES:
        raise err(422, "LANGUAGE_INVALID")
    return value


def parse_uuid(value) -> UUID:
    try:
        return value if isinstance(value, UUID) else UUID(str(value))
    except (TypeError, ValueError):
        raise err(404, "NOT_FOUND") from None


def notify(db: Session, user_id, title: str, message: str, link: str | None = None, course: bool = False) -> None:
    """A notification row in the CURRENT transaction (create_notification commits on its own, which would break the row locks
    of the payment approval and turn a broadcast into hundreds of commits)."""
    db.add(Notification(user_id=user_id, title=title[:255], message=message[:2000], type=TYPE_COURSE if course else TYPE_INFORMATION,
                        link_path=link[:300] if link else None))


def super_admin_ids(db: Session) -> list:
    return list(db.scalars(select(User.id).where(User.role == UserRole.SUPER_ADMIN, User.is_active.is_(True))))


def notify_admins(db: Session, title: str, message: str, link: str) -> None:
    for uid in super_admin_ids(db):
        notify(db, uid, title, message, link)


def get_settings(db: Session) -> dict:
    row = db.scalar(select(AppSetting).where(AppSetting.key == SETTINGS_KEY))
    value = dict(DEFAULT_SETTINGS)
    if row is not None and isinstance(row.value, dict):
        value.update({k: v for k, v in row.value.items() if k in DEFAULT_SETTINGS and isinstance(v, bool)})
    return value


def set_settings(db: Session, actor: User, data: dict) -> dict:
    value = get_settings(db)
    for k in DEFAULT_SETTINGS:
        if k in data and isinstance(data[k], bool):
            value[k] = data[k]
    row = db.scalar(select(AppSetting).where(AppSetting.key == SETTINGS_KEY))
    if row is None:
        db.add(AppSetting(key=SETTINGS_KEY, value=value, updated_by=actor.id))
    else:
        row.value, row.updated_by = value, actor.id
    return value


def when(at: datetime | None) -> str:
    return at.astimezone(TASHKENT).strftime("%d.%m.%Y %H:%M") if at else "—"
