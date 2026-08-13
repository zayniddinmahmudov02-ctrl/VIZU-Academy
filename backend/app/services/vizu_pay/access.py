from datetime import datetime, timezone

from app.core.security.roles import UserRole
from app.models.user import User


def is_user_premium(user: User | None) -> bool:
    """Single source of truth for "does this user currently have Premium".
    Used everywhere access is gated (mock tests, level content, /vizu-pay
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


# Every level (A1-C1) gives its first 3 lessons free; Lesson.number is the
# existing canonical per-module ordering field (already used to sort
# lessons everywhere else) — no new position field needed.
LESSON_FREE_NUMBER_THRESHOLD = 3


def is_free_lesson(lesson) -> bool:
    """Position-based rule: Lesson.number <= 3 is free. Combined with the
    pre-existing per-lesson Lesson.is_free override (currently used to
    mark each level's very first lesson) via OR, so nothing free before
    this rule existed becomes locked."""
    return lesson.number <= LESSON_FREE_NUMBER_THRESHOLD or bool(lesson.is_free)


def can_access_lesson(user: User | None, lesson) -> bool:
    return is_free_lesson(lesson) or is_user_premium(user) or has_premium_bypass(user)
