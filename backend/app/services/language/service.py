from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.core.pagination import clamp_page_params, paginated_response
from app.models.certificate import Certificate
from app.models.course import Course
from app.models.grammar import Grammar
from app.models.homework import Homework
from app.models.language import Language
from app.models.language_settings import LanguageSettings
from app.models.lesson import Lesson
from app.models.listening import Listening
from app.models.model_test import ModelTest
from app.models.module import Module
from app.models.quiz import Quiz
from app.models.reading import Reading
from app.models.speaking import Speaking
from app.models.user import User
from app.models.user_language import UserLanguage
from app.models.video import Video
from app.models.vocabulary import Vocabulary
from app.models.writing import Writing
from app.schemas.language import LanguageCreate, LanguageSettingsUpdate, LanguageUpdate

ACTIVE_WINDOW_DAYS = 30

# Content models scoped to a language via lesson -> module -> course, all
# sharing the identical lesson_id FK shape — one join helper covers all of
# them instead of writing the same 4-way join nine times.
_LESSON_SCOPED_MODELS = {
    "videos": Video,
    "vocabulary": Vocabulary,
    "grammar": Grammar,
    "reading": Reading,
    "listening": Listening,
    "writing": Writing,
    "speaking": Speaking,
    "homework": Homework,
    "quiz": Quiz,
}


def _not_deleted(query):
    return query.where(Language.deleted_at.is_(None))


def _learners_count(db: Session, language_id: UUID) -> int:
    return db.scalar(
        select(func.count(func.distinct(UserLanguage.user_id))).where(
            UserLanguage.language_id == language_id
        )
    ) or 0


def _levels_count(db: Session, language_id: UUID) -> int:
    return db.scalar(select(func.count(Course.id)).where(Course.language_id == language_id)) or 0


def _modules_count(db: Session, language_id: UUID) -> int:
    return (
        db.scalar(
            select(func.count(Module.id))
            .join(Course, Module.course_id == Course.id)
            .where(Course.language_id == language_id)
        )
        or 0
    )


def _lessons_count(db: Session, language_id: UUID) -> int:
    return (
        db.scalar(
            select(func.count(Lesson.id))
            .join(Module, Lesson.module_id == Module.id)
            .join(Course, Module.course_id == Course.id)
            .where(Course.language_id == language_id)
        )
        or 0
    )


def _lesson_scoped_count(db: Session, model, language_id: UUID) -> int:
    return (
        db.scalar(
            select(func.count(model.id))
            .join(Lesson, model.lesson_id == Lesson.id)
            .join(Module, Lesson.module_id == Module.id)
            .join(Course, Module.course_id == Course.id)
            .where(Course.language_id == language_id)
        )
        or 0
    )


def _attach_table_counts(db: Session, language: Language) -> Language:
    """Sets the denormalized *_count attributes LanguageResponse expects —
    plain Python attributes on the ORM instance, not mapped columns; safe
    since Pydantic's from_attributes reads via getattr either way."""
    language.learners_count = _learners_count(db, language.id)
    language.levels_count = _levels_count(db, language.id)
    language.modules_count = _modules_count(db, language.id)
    language.lessons_count = _lessons_count(db, language.id)
    return language


# ============================================================
# CRUD
# ============================================================


def get_languages(db: Session) -> list[Language]:
    languages = db.scalars(
        _not_deleted(select(Language)).order_by(Language.sort_order, Language.name)
    ).all()
    return [_attach_table_counts(db, lang) for lang in languages]


def get_language(db: Session, language_id: UUID) -> Language | None:
    language = db.scalar(_not_deleted(select(Language).where(Language.id == language_id)))
    if language is None:
        return None
    return _attach_table_counts(db, language)


def _check_code_locale_unique(db: Session, code: str, locale: str, exclude_id: UUID | None = None) -> None:
    code_query = _not_deleted(select(Language).where(Language.code == code))
    locale_query = _not_deleted(select(Language).where(Language.locale == locale))
    if exclude_id is not None:
        code_query = code_query.where(Language.id != exclude_id)
        locale_query = locale_query.where(Language.id != exclude_id)

    if db.scalar(code_query):
        raise HTTPException(status_code=409, detail="A language with this code already exists.")
    if db.scalar(locale_query):
        raise HTTPException(status_code=409, detail="A language with this locale already exists.")


def _unset_other_defaults(db: Session, exclude_id: UUID) -> None:
    db.execute(
        update(Language)
        .where(Language.id != exclude_id, Language.is_default.is_(True))
        .values(is_default=False)
    )


def create_language(db: Session, data: LanguageCreate) -> Language:
    _check_code_locale_unique(db, data.code, data.locale)

    language = Language(**data.model_dump())
    db.add(language)
    db.flush()

    if language.is_default:
        _unset_other_defaults(db, exclude_id=language.id)

    # Every language gets a settings row immediately (all toggles default
    # to enabled) — avoids a nullable "has this language been configured
    # yet" state on first visit to the Settings page.
    db.add(LanguageSettings(language_id=language.id))

    db.commit()
    db.refresh(language)
    return _attach_table_counts(db, language)


def update_language(db: Session, language_id: UUID, data: LanguageUpdate) -> Language | None:
    language = db.scalar(_not_deleted(select(Language).where(Language.id == language_id)))
    if language is None:
        return None

    updates = data.model_dump(exclude_unset=True)
    new_code = updates.get("code", language.code)
    new_locale = updates.get("locale", language.locale)
    if "code" in updates or "locale" in updates:
        _check_code_locale_unique(db, new_code, new_locale, exclude_id=language_id)

    for key, value in updates.items():
        setattr(language, key, value)

    if updates.get("is_default") is True:
        _unset_other_defaults(db, exclude_id=language_id)

    db.commit()
    db.refresh(language)
    return _attach_table_counts(db, language)


def delete_language(db: Session, language_id: UUID) -> Language:
    """Soft delete — raises 404 if missing, 409 if it still has learners,
    levels, or modules, or if it's the platform's default language."""
    language = db.scalar(_not_deleted(select(Language).where(Language.id == language_id)))
    if language is None:
        raise HTTPException(status_code=404, detail="Language not found.")

    if language.is_default:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete the default language. Set another language as default first.",
        )

    learners = _learners_count(db, language_id)
    levels = _levels_count(db, language_id)
    modules = _modules_count(db, language_id)
    if learners > 0 or levels > 0 or modules > 0:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot delete a language with existing learners ({learners}), "
                f"levels ({levels}), or modules ({modules})."
            ),
        )

    language.deleted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(language)
    return language


# ============================================================
# Statistics
# ============================================================


def get_language_statistics(db: Session, language_id: UUID) -> dict | None:
    language = db.scalar(_not_deleted(select(Language).where(Language.id == language_id)))
    if language is None:
        return None

    active_since = datetime.now(timezone.utc) - timedelta(days=ACTIVE_WINDOW_DAYS)
    active_learners = (
        db.scalar(
            select(func.count(func.distinct(UserLanguage.user_id))).where(
                UserLanguage.language_id == language_id,
                UserLanguage.last_activity.isnot(None),
                UserLanguage.last_activity >= active_since,
            )
        )
        or 0
    )

    certificates = (
        db.scalar(
            select(func.count(Certificate.id))
            .join(Course, Certificate.course_id == Course.id)
            .where(Course.language_id == language_id)
        )
        or 0
    )

    # Mock exams are certificate-scoped (Goethe/ÖSD/telc/...), not
    # language-scoped — CertificationProvider has no language_id, and
    # extending it is out of this module's scope. Every mock test in the
    # system is counted here rather than silently reporting 0; this is
    # accurate today (the platform teaches exactly one language) but will
    # need real scoping the day a second language goes live.
    mock_tests = db.scalar(select(func.count(ModelTest.id))) or 0

    stats = {
        "language_id": language_id,
        "learners": _learners_count(db, language_id),
        "active_learners": active_learners,
        "levels": _levels_count(db, language_id),
        "modules": _modules_count(db, language_id),
        "lessons": _lessons_count(db, language_id),
        "mock_tests": mock_tests,
        "certificates": certificates,
    }
    for key, model in _LESSON_SCOPED_MODELS.items():
        stats[key] = _lesson_scoped_count(db, model, language_id)

    return stats


# ============================================================
# Learners
# ============================================================


def get_language_learners(
    db: Session,
    language_id: UUID,
    search: str | None,
    page: int,
    page_size: int,
) -> dict | None:
    language = db.scalar(_not_deleted(select(Language).where(Language.id == language_id)))
    if language is None:
        return None

    page, page_size = clamp_page_params(page, page_size)

    query = (
        select(UserLanguage, User)
        .join(User, UserLanguage.user_id == User.id)
        .where(UserLanguage.language_id == language_id)
    )
    if search:
        like = f"%{search}%"
        query = query.where(or_(User.username.ilike(like), User.email.ilike(like)))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    rows = db.execute(
        query.order_by(UserLanguage.joined_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()

    items = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_primary": user_language.is_primary,
            "joined_at": user_language.joined_at,
            "last_activity": user_language.last_activity,
        }
        for user_language, user in rows
    ]

    return paginated_response(items, total, page, page_size)


# ============================================================
# Settings
# ============================================================


def get_or_create_language_settings(db: Session, language_id: UUID) -> LanguageSettings | None:
    language = db.scalar(_not_deleted(select(Language).where(Language.id == language_id)))
    if language is None:
        return None

    settings = db.scalar(select(LanguageSettings).where(LanguageSettings.language_id == language_id))
    if settings is None:
        settings = LanguageSettings(language_id=language_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


def update_language_settings(
    db: Session, language_id: UUID, data: LanguageSettingsUpdate
) -> LanguageSettings | None:
    settings = get_or_create_language_settings(db, language_id)
    if settings is None:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)

    db.commit()
    db.refresh(settings)
    return settings
