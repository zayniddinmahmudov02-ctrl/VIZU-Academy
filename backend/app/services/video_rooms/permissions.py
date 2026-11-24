"""Who may see, join and moderate a group video room — decided only here, on the server.

* view / join: the group's managers (its teacher, a SUPER_ADMIN — the existing
  study-group policy in study_groups.access) and its ACTIVE members. Anyone
  else gets 404 VIDEO_ROOM_NOT_FOUND, never 403: a guessed room or group id
  must not even confirm that it exists. A blocked group is hidden from members.
* moderate: managers only; a member student gets 403 VIDEO_MODERATOR_REQUIRED.
* A room id only ever resolves inside its own group, so sending another
  group's id gains nothing.

Special-lesson rooms (no group, special_lessons.id): view / join = any active
logged-in user while the lesson is APPROVED (or ENDED, for the history); host =
the lesson's teacher or a SUPER_ADMIN; anything else 404.

The LiveKit grants of a participant are derived from the stored moderation
state, never from the request. Camera, microphone and screen share are separate."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.study_group import GROUP_ACTIVE, StudyGroup
from app.models.user import User
from app.models.video_room import ROLE_HOST, ROLE_STUDENT, VideoRoom, VideoRoomParticipant
from app.services.study_groups.access import is_manager, is_super_admin, require_manage, require_view
from app.services.video_rooms import livekit_service as lk


def room_not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VIDEO_ROOM_NOT_FOUND")


def _group_or_404(fn, *args):
    try:
        return fn(*args)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            raise room_not_found() from None
        raise


def view_group(db: Session, user: User, group_id: UUID) -> tuple[StudyGroup, bool]:
    """(group, viewer is manager). Outsiders: 404 (the group module's own 404)."""
    group, _member = require_view(db, user, group_id)
    return group, is_manager(user, group)


def manage_group(db: Session, user: User, group_id: UUID) -> StudyGroup:
    """Teacher of this group / SUPER_ADMIN, group not blocked (409) — the group module's rule."""
    group, manager = view_group(db, user, group_id)
    if not manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="VIDEO_MODERATOR_REQUIRED")
    return require_manage(db, user, group.id, write=True)


def require_group_active(group: StudyGroup) -> None:
    if group.status != GROUP_ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="GROUP_NOT_ACTIVE")


def lesson_manager(db: Session, user: User, room: VideoRoom) -> bool:
    """Special-lesson room: 404 unless the lesson is approved / ended and the account active; True = host."""
    from app.models.teacher_market import SL_APPROVED, SL_ENDED, SpecialLesson

    lesson = db.get(SpecialLesson, room.special_lesson_id)
    if lesson is None or lesson.status not in (SL_APPROVED, SL_ENDED) or not user.is_active or user.is_banned:
        raise room_not_found()
    return is_super_admin(user) or lesson.teacher_id == user.id


def view_room(db: Session, user: User, room_id: UUID) -> tuple[VideoRoom, StudyGroup | None, bool]:
    """(room, group or None for a special lesson, viewer is host)."""
    room = db.get(VideoRoom, room_id)
    if room is None:
        raise room_not_found()
    if room.special_lesson_id is not None:
        return room, None, lesson_manager(db, user, room)
    group, manager = _group_or_404(view_group, db, user, room.group_id)
    return room, group, manager


def moderate_room(db: Session, user: User, room_id: UUID) -> tuple[VideoRoom, StudyGroup | None]:
    room, group, manager = view_room(db, user, room_id)
    if not manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="VIDEO_MODERATOR_REQUIRED")
    if group is not None:
        require_manage(db, user, group.id, write=True)
    return room, group


def role_for(manager: bool) -> str:
    return ROLE_HOST if manager else ROLE_STUDENT


def sources(p: VideoRoomParticipant) -> list[str]:
    if p.role == ROLE_HOST:
        return [lk.CAMERA, lk.MICROPHONE, lk.SCREEN_SHARE, lk.SCREEN_SHARE_AUDIO]
    out = []
    if p.can_video is not False:  # None = a row not flushed yet = the column default (allowed)
        out.append(lk.CAMERA)
    if p.can_speak:
        out.append(lk.MICROPHONE)
    if p.can_share_screen:
        out += [lk.SCREEN_SHARE, lk.SCREEN_SHARE_AUDIO]
    return out


def can_chat(room: VideoRoom, p: VideoRoomParticipant) -> bool:
    return p.role == ROLE_HOST or (room.chat_enabled and p.can_chat)


def described(room: VideoRoom, p: VideoRoomParticipant | None, manager: bool) -> dict:
    """What the viewer may do — the UI shows it; LiveKit and the API enforce it."""
    if p is None:
        host = manager
        return {"role": role_for(manager), "camera": host or room.students_camera_allowed, "microphone": host or room.students_mic_allowed,
                "screen_share": host or room.students_can_share_screen, "chat": host or room.chat_enabled, "moderate": manager}
    src = sources(p)
    return {"role": p.role, "camera": lk.CAMERA in src, "microphone": lk.MICROPHONE in src, "screen_share": lk.SCREEN_SHARE in src,
            "chat": can_chat(room, p), "moderate": p.role == ROLE_HOST}
