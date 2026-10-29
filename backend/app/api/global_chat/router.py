"""Global Chat API — one chat for every logged-in user, separate from the
group chats (/groups/{id}/messages). Authors edit (PATCH) and delete (DELETE)
their own messages under /global-chat/messages/{id}.

User routes need a logged-in user; the caller is always the token's user,
request bodies never carry a user id or role for the caller (extra fields
are rejected). Admin routes (/admin/global-chat) need a chat moderator
(SUPER_ADMIN or ADMIN), checked on the server for every request; a
permanent ban needs a SUPER_ADMIN. Mute and ban only affect writing in this
chat — see app.services.global_chat.restrictions."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.app_setting import AppSetting
from app.models.user import User
from app.services.global_chat import messages, restrictions, word_filter
from app.services.global_chat.access import audit, require_moderator

router = APIRouter(prefix="/global-chat", tags=["Global Chat"])


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MessageIn(_In):
    body: str = Field(min_length=1, max_length=messages.MAX_LENGTH)


class ReadIn(_In):
    until_id: UUID | None = None


@router.get("/messages")
def history(before: UUID | None = None, limit: int = Query(messages.PAGE, ge=1, le=messages.MAX_PAGE),
            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The newest page, or the page before message `before` (scrolling up)."""
    return messages.page(db, user, before=before, limit=limit)


@router.get("/updates")
def updates(since: datetime, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Polling: messages changed after `since` (the `sync` of the previous response)."""
    return messages.updates(db, user, since)


@router.post("/messages", status_code=201)
def send(data: MessageIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return messages.post(db, user, data.body)


@router.patch("/messages/{message_id}")
def edit_message(message_id: UUID, data: MessageIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The author edits their own message (404 if not visible to the caller, 403 if someone else's)."""
    return messages.edit_own(db, user, message_id, data.body)


@router.delete("/messages/{message_id}", status_code=204)
def delete_message(message_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The author deletes their own message: it disappears for users, moderators keep it (and the log)."""
    messages.delete_own(db, user, message_id)


@router.get("/pinned")
def pinned(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return messages.pinned(db, user)


@router.get("/unread-count")
def unread(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"unread": messages.unread_count(db, user)}


@router.get("/me")
def me(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """May I write? If not: mute or ban, until when, the note for me."""
    return restrictions.viewer_status(db, user)


@router.post("/read", status_code=204)
def read(data: ReadIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    messages.mark_read(db, user, data.until_id)


# ============================================================
# Admin / moderation
# ============================================================

admin_router = APIRouter(prefix="/admin/global-chat", tags=["Admin - Global Chat"])


def moderator(current_user: User = Depends(get_current_user)) -> User:
    return require_moderator(current_user)


class ModerateIn(_In):
    action: str = Field(pattern=f"^({'|'.join(messages.ACTIONS)})$")
    reason: str | None = Field(None, max_length=500)


class RestrictionIn(_In):
    user_id: UUID
    kind: str = Field(pattern="^(mute|ban)$")
    duration: str = Field(max_length=12)  # mute: 10m 1h 24h 3d 7d 30d custom · ban: 1y 2y 3y 5y permanent
    ends_at: datetime | None = None  # only for a custom mute
    reason: str = Field(min_length=3, max_length=2000)
    public_note: str | None = Field(None, max_length=300)
    message_id: UUID | None = None  # the message that led to it (for the log)


class RestrictionUpdate(_In):
    ends_at: datetime | None = None
    ban_years: int | None = Field(None, ge=1, le=5)
    permanent: bool = False
    reason: str | None = Field(None, max_length=2000)
    public_note: str | None = Field(None, max_length=300)


class RevokeIn(_In):
    reason: str | None = Field(None, max_length=500)


class WordFilterIn(_In):
    enabled: bool = True
    words: list[str] = Field(default_factory=list, max_length=word_filter.MAX_WORDS)


@admin_router.get("/stats")
def stats(db: Session = Depends(get_db), user: User = Depends(moderator)):
    return messages.stats(db, user)


@admin_router.get("/messages")
def admin_messages(filter: str = Query("all", pattern=f"^({'|'.join(messages.FILTERS)})$"), user_id: UUID | None = None,
                   q: str | None = Query(None, max_length=100), page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100),
                   db: Session = Depends(get_db), user: User = Depends(moderator)):
    return messages.admin_list(db, user, filter, user_id, q, page, page_size)


@admin_router.patch("/messages/{message_id}")
def moderate(message_id: UUID, data: ModerateIn, db: Session = Depends(get_db), user: User = Depends(moderator)):
    """pin · unpin · hide (with reason) · unhide · approve (a message the word filter held)."""
    return messages.moderate(db, user, message_id, data.action, data.reason)


@admin_router.get("/messages/{message_id}/edits")
def message_edits(message_id: UUID, db: Session = Depends(get_db), user: User = Depends(moderator)):
    """Earlier versions of an edited message."""
    return messages.edit_history(db, user, message_id)


@admin_router.get("/restrictions")
def list_restrictions(state: str = Query("active", pattern="^(active|expired|revoked|all)$"), kind: str | None = Query(None, pattern="^(mute|ban)$"),
                      user_id: UUID | None = None, q: str | None = Query(None, max_length=100), page: int = Query(1, ge=1),
                      page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(moderator)):
    return restrictions.list_restrictions(db, user, state, kind, user_id, q, page, page_size)


@admin_router.post("/restrictions", status_code=201)
def create_restriction(data: RestrictionIn, db: Session = Depends(get_db), user: User = Depends(moderator)):
    return restrictions.create(db, user, data.model_dump())


@admin_router.patch("/restrictions/{restriction_id}")
def update_restriction(restriction_id: UUID, data: RestrictionUpdate, db: Session = Depends(get_db), user: User = Depends(moderator)):
    return restrictions.update(db, user, restriction_id, data.model_dump(exclude_unset=True))


@admin_router.post("/restrictions/{restriction_id}/revoke")
def revoke_restriction(restriction_id: UUID, data: RevokeIn, db: Session = Depends(get_db), user: User = Depends(moderator)):
    return restrictions.revoke(db, user, restriction_id, data.reason)


@admin_router.get("/actions")
def actions(user_id: UUID | None = None, action: str | None = Query(None, max_length=40), page: int = Query(1, ge=1),
            page_size: int = Query(50, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(moderator)):
    return restrictions.list_actions(db, user, user_id, action, page, page_size)


@admin_router.get("/users")
def search_users(q: str = Query(min_length=2, max_length=100), db: Session = Depends(get_db), user: User = Depends(moderator)):
    return messages.search_users(db, user, q)


@admin_router.get("/users/{user_id}")
def user_history(user_id: UUID, db: Session = Depends(get_db), user: User = Depends(moderator)):
    return messages.user_history(db, user, user_id)


@admin_router.get("/word-filter")
def get_word_filter(db: Session = Depends(get_db), user: User = Depends(moderator)):
    return word_filter.current(db)


@admin_router.put("/word-filter")
def put_word_filter(data: WordFilterIn, db: Session = Depends(get_db), user: User = Depends(moderator)):
    words = word_filter.clean_list(data.words)
    row = word_filter.settings_row(db)
    if row is None:
        row = AppSetting(key=word_filter.SETTING_KEY, value={})
        db.add(row)
    row.value, row.updated_by = {"enabled": data.enabled, "words": words}, user.id
    audit(db, user.id, "filter.update", meta={"enabled": data.enabled, "words": len(words)})
    db.commit()
    return word_filter.current(db)


@admin_router.delete("/word-filter")
def reset_word_filter(db: Session = Depends(get_db), user: User = Depends(moderator)):
    """Back to the built-in default list."""
    row = word_filter.settings_row(db)
    if row is not None:
        db.delete(row)
        audit(db, user.id, "filter.reset")
        db.commit()
    return word_filter.current(db)
