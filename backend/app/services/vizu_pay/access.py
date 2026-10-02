from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import object_session

from app.core.security.roles import UserRole
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.subscription_order import SubscriptionOrder
from app.models.user import User

from .offers import OFFER_CODES, offer_levels
from .plans import STATUS_APPROVED


def is_user_premium(user: User | None) -> bool:
    """Single source of truth for "does this user currently have Premium".
    Legacy time-based Premium (no longer sold, see offers.py); still
    honoured everywhere access is gated (mock tests, level content,
    status) so a future change to what Premium means only happens here."""
    if user is None:
        return False
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return bool(user.premium_until and user.premium_until > now)


def has_premium_bypass(user: User | None) -> bool:
    """Admin/staff roles always get through a Premium gate — they need to
    review content regardless of subscription state."""
    return user is not None and user.role in UserRole.ADMIN_PANEL_ROLES


def is_free_model_test(model_test) -> bool:
    """Business rule: "Modelltest 1" (the lowest sort_order in its level)
    is free; every other model test in that level requires Premium."""
    return model_test.sort_order == 1


def can_access_model_test(model_test, user: User | None) -> bool:
    return is_free_model_test(model_test) or is_user_premium(user) or has_premium_bypass(user)


# ----------------------------------------------------------------------
# Lessons — Angebote model
# ----------------------------------------------------------------------
# Only the FIRST lesson of every course is free (offers.FREE_LESSONS_PER_COURSE
# = 1). "First" = the course's first lesson in the same order students see
# (Module.order_index, then Lesson.number) — not `Lesson.number == 1`, which
# repeats per module. Everything else needs one of:
#   * an APPROVED Angebote order covering the lesson's course level,
#   * legacy time-based Premium (premium_until) — existing subscribers keep
#     their full access,
#   * a staff role (content review).
# Lookups are cached in `Session.info` so a lesson list costs one query per
# course / per user, not one per lesson.


def _session_cache(obj, name: str) -> dict:
    try:
        session = object_session(obj)
    except Exception:  # not an ORM instance (e.g. a test double)
        return {}
    info = getattr(session, "info", None)
    if not isinstance(info, dict):
        return {}
    return info.setdefault(f"vizu_pay_access:{name}", {})


def _course_of(lesson) -> tuple[str | None, str | None]:
    """(course_id, course level) for a lesson, cached per module."""
    cache = _session_cache(lesson, "module_course")
    key = str(lesson.module_id)
    if key not in cache:
        module = lesson.module
        course = module.course if module is not None else None
        cache[key] = (str(course.id), course.level) if course is not None else (None, None)
    return cache[key]


def _first_lesson_id(lesson, course_id: str) -> str | None:
    cache = _session_cache(lesson, "first_lesson")
    if course_id not in cache:
        session = object_session(lesson)
        first = session.execute(
            select(Lesson.id)
            .join(Module, Lesson.module_id == Module.id)
            .where(Module.course_id == course_id)
            .order_by(Module.order_index, Module.number, Lesson.number)
            .limit(1)
        ).scalar_one_or_none()
        cache[course_id] = str(first) if first is not None else None
    return cache[course_id]


def is_free_lesson(lesson) -> bool:
    """True only for the first lesson of its course. `Lesson.is_free` is no
    longer an override — "faqat 1-dars bepul" admits no other free lesson."""
    course_id, _ = _course_of(lesson)
    if course_id is None:
        return False
    return _first_lesson_id(lesson, course_id) == str(lesson.id)


def owned_levels(user: User | None) -> set[str]:
    """CEFR levels unlocked by the user's APPROVED Angebote orders. A
    refunded/rejected/pending order unlocks nothing."""
    if user is None:
        return set()
    cache = _session_cache(user, "owned_levels")
    key = str(user.id)
    if key not in cache:
        session = object_session(user)
        if session is None:
            return set()
        plans = session.scalars(
            select(SubscriptionOrder.plan).where(
                SubscriptionOrder.user_id == user.id,
                SubscriptionOrder.status == STATUS_APPROVED,
                SubscriptionOrder.plan.in_(list(OFFER_CODES)),
            )
        ).all()
        levels: set[str] = set()
        for plan in plans:
            levels.update(offer_levels(plan))
        cache[key] = levels
    return set(cache[key])


def owns_level(user: User | None, level: str | None) -> bool:
    return bool(level) and level in owned_levels(user)


def can_access_lesson(user: User | None, lesson) -> bool:
    if has_premium_bypass(user) or is_user_premium(user):
        return True
    if is_free_lesson(lesson):
        return True
    _, level = _course_of(lesson)
    return owns_level(user, level)
