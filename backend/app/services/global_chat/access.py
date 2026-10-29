"""Who may moderate the Global Chat — decided here, on the server, for every
moderation endpoint (the frontend only hides buttons).

* every logged-in user reads and (unless muted / banned) writes;
* SUPER_ADMIN and ADMIN moderate (pin, hide, approve, mute, ban);
* only a SUPER_ADMIN gives a permanent ban;
* a moderator can never be muted / banned through the chat."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security.roles import UserRole
from app.models.global_chat import GlobalChatModerationAction
from app.models.user import User

MODERATOR_ROLES = (UserRole.SUPER_ADMIN, UserRole.ADMIN)


def now() -> datetime:
    return datetime.now(timezone.utc)


def is_moderator(user: User | None) -> bool:
    return user is not None and user.role in MODERATOR_ROLES


def require_moderator(user: User) -> User:
    if not is_moderator(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Global chat moderator access required")
    return user


def can_ban_permanently(user: User) -> bool:
    return user.role == UserRole.SUPER_ADMIN


def display_name(user: User | None) -> str:
    if user is None:
        return "—"
    parts = [p for p in (user.first_name, user.last_name) if p]
    return " ".join(parts) if parts else user.username


def badge(user: User | None) -> str | None:
    """Shown next to the author's name: admin / teacher, nothing for students."""
    if user is None:
        return None
    if user.role in MODERATOR_ROLES:
        return "admin"
    if user.role == UserRole.TEACHER:
        return "teacher"
    return None


def audit(db: Session, actor_id, action: str, target_user_id=None, message_id=None, restriction_id=None,
          reason: str | None = None, meta: dict | None = None) -> None:
    db.add(GlobalChatModerationAction(actor_id=actor_id, action=action, target_user_id=target_user_id, message_id=message_id,
                                      restriction_id=restriction_id, reason=(reason or None) and reason[:2000], meta=meta))
