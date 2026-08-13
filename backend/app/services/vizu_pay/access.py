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
