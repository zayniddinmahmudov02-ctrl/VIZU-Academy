"""Teacher moderation, raised hands, client connection reports and the LiveKit webhook.

* Every moderation action is for hosts of THIS room's group only (permissions.moderate_room), works on a live room,
  is rate limited, changes the stored state first and then pushes it to LiveKit:
  - mute = server-mute the microphone track (the student may unmute again);
  - mic / screen share / chat permission = LiveKit publish permissions (a revoked source is muted first, then the
    permission is taken away; a new join token is built from the stored state, so a reload does not undo it);
  - room-wide switches also set the room default for students who join later and the room metadata the clients read.
* A host is never moderated (CANNOT_MODERATE_HOST).
* Raised hand: a participant raises / lowers their own hand; a host may only lower someone else's. Shown live through
  the LiveKit participant attribute "vizu.hand", which clients cannot set themselves.
* Webhook: accepted only with a valid LiveKit signature. It keeps connection status in sync and removes from LiveKit
  anyone who may not be in the room (not a participant, removed, blocked, group access lost, room not live)."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.video_room import (
    CONN_CONNECTED,
    CONN_DISCONNECTED,
    CONN_JOINING,
    CONN_LEFT,
    CONN_RECONNECTING,
    CONN_REMOVED,
    ONLINE,
    ROLE_HOST,
    ROLE_STUDENT,
    ROOM_LIVE,
    VideoRoom,
    VideoRoomParticipant,
)
from app.services.study_groups.access import audit, now, require_view
from app.services.video_rooms import livekit_service as lk
from app.services.video_rooms.permissions import can_chat, moderate_room, sources, view_room
from app.services.video_rooms.service import error, event, finish, limit, participant, room_metadata

PRESENT = (*ONLINE, CONN_JOINING)


def _live(room: VideoRoom) -> None:
    if room.status != ROOM_LIVE:
        raise error(409, "VIDEO_ROOM_NOT_LIVE")


def _target(db: Session, room: VideoRoom, user_id: UUID) -> VideoRoomParticipant:
    p = participant(db, room.id, user_id)
    if p is None:
        raise error(404, "PARTICIPANT_NOT_FOUND")
    if p.role == ROLE_HOST:
        raise error(409, "CANNOT_MODERATE_HOST")
    return p


def _students(db: Session, room: VideoRoom) -> list[VideoRoomParticipant]:
    return list(db.scalars(select(VideoRoomParticipant).where(VideoRoomParticipant.room_id == room.id, VideoRoomParticipant.role == ROLE_STUDENT)))


def _push(room: VideoRoom, people: list[VideoRoomParticipant]) -> bool:
    """Send the stored permissions of the present participants to LiveKit. False = LiveKit not reached."""
    ok = True
    for p in people:
        if p.connection_status not in PRESENT:
            continue
        try:
            lk.gateway.update_permission(room.room_name, str(p.user_id), sources(p), can_chat(room, p))
        except lk.LiveKitUnavailable:
            ok = False
    return ok


def _mute(room: VideoRoom, people: list[VideoRoomParticipant], what: tuple[str, ...]) -> int:
    present = [str(p.user_id) for p in people if p.connection_status in PRESENT]
    if not present:
        return 0
    try:
        return lk.gateway.mute(room.room_name, present, what)
    except lk.LiveKitUnavailable:
        raise error(503, "VIDEO_SERVICE_UNAVAILABLE") from None


def _room_meta(room: VideoRoom) -> None:
    try:
        lk.gateway.set_room_metadata(room.room_name, room_metadata(room))
    except lk.LiveKitUnavailable:
        pass


def _setup(db: Session, user: User, room_id: UUID) -> VideoRoom:
    room, _group = moderate_room(db, user, room_id)
    _live(room)
    limit(db, user, "moderate")
    return room


def mute_participant(db: Session, user: User, room_id: UUID, target_id: UUID) -> dict:
    room = _setup(db, user, room_id)
    p = _target(db, room, target_id)
    muted = _mute(room, [p], (lk.MICROPHONE,))
    event(db, room, user.id, "muted", {"target": str(p.user_id), "tracks": muted})
    db.commit()
    return {"muted_tracks": muted}


def mic_permission(db: Session, user: User, room_id: UUID, allowed: bool, target_id: UUID | None = None) -> dict:
    room = _setup(db, user, room_id)
    people = [_target(db, room, target_id)] if target_id else _students(db, room)
    if target_id is None:
        room.students_mic_allowed = allowed
    for p in people:
        p.can_speak = allowed
    muted = 0 if allowed else _mute(room, people, (lk.MICROPHONE,))
    applied = _push(room, people)
    if target_id is None:
        _room_meta(room)
    event(db, room, user.id, "mic_permission", {"target": str(target_id) if target_id else "all", "allowed": allowed})
    db.commit()
    return {"allowed": allowed, "muted_tracks": muted, "live_applied": applied}


def mute_all(db: Session, user: User, room_id: UUID, lock: bool) -> dict:
    room = _setup(db, user, room_id)
    people = _students(db, room)
    muted = _mute(room, people, (lk.MICROPHONE,))
    applied = True
    if lock:
        room.students_mic_allowed = False
        for p in people:
            p.can_speak = False
        applied = _push(room, people)
        _room_meta(room)
    event(db, room, user.id, "mute_all", {"lock": lock, "tracks": muted})
    db.commit()
    return {"muted_tracks": muted, "locked": lock, "live_applied": applied}


def screen_share_permission(db: Session, user: User, room_id: UUID, allowed: bool, target_id: UUID | None = None) -> dict:
    room = _setup(db, user, room_id)
    people = [_target(db, room, target_id)] if target_id else _students(db, room)
    if target_id is None:
        room.students_can_share_screen = allowed
    for p in people:
        p.can_share_screen = allowed
    if not allowed:
        _mute(room, people, (lk.SCREEN_SHARE, lk.SCREEN_SHARE_AUDIO))
    applied = _push(room, people)
    if target_id is None:
        _room_meta(room)
    event(db, room, user.id, "screen_share_permission", {"target": str(target_id) if target_id else "all", "allowed": allowed})
    db.commit()
    return {"allowed": allowed, "live_applied": applied}


def chat_permission(db: Session, user: User, room_id: UUID, allowed: bool, target_id: UUID | None = None) -> dict:
    room = _setup(db, user, room_id)
    if target_id:
        people = [_target(db, room, target_id)]
        people[0].can_chat = allowed
    else:
        room.chat_enabled = allowed
        people = _students(db, room)
    applied = _push(room, people)
    if target_id is None:
        _room_meta(room)
    event(db, room, user.id, "chat_permission", {"target": str(target_id) if target_id else "all", "allowed": allowed})
    db.commit()
    return {"allowed": allowed, "live_applied": applied}


def remove_participant(db: Session, user: User, room_id: UUID, target_id: UUID, block: bool) -> dict:
    room = _setup(db, user, room_id)
    p = _target(db, room, target_id)
    p.connection_status, p.removed_at, p.removed_by, p.left_at, p.hand_raised_at = CONN_REMOVED, now(), user.id, now(), None
    p.blocked = block
    try:
        lk.gateway.remove(room.room_name, str(p.user_id))
        applied = True
    except lk.LiveKitUnavailable:
        applied = False
    event(db, room, user.id, "participant_removed", {"target": str(p.user_id), "block": block})
    audit(db, room.group_id, user.id, "video_participant_removed", "user", p.user_id, {"room_id": str(room.id), "block": block})
    db.commit()
    return {"removed": True, "blocked": block, "live_applied": applied}


def raise_hand(db: Session, user: User, room_id: UUID, raised: bool, target_id: UUID | None = None) -> dict:
    room, _group, manager = view_room(db, user, room_id)
    _live(room)
    if target_id is not None and target_id != user.id:
        if not manager:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="VIDEO_MODERATOR_REQUIRED")
        if raised:
            raise error(400, "ONLY_LOWER_OTHERS_HAND")
        p = participant(db, room.id, target_id)
        if p is None:
            raise error(404, "PARTICIPANT_NOT_FOUND")
    else:
        p = participant(db, room.id, user.id)
        if p is None or p.connection_status not in PRESENT:
            raise error(409, "NOT_IN_ROOM")
    limit(db, user, "hand")
    if raised:
        p.hand_raised_at = p.hand_raised_at or now()
    else:
        p.hand_raised_at = None
    try:
        lk.gateway.set_attributes(room.room_name, str(p.user_id), {"vizu.hand": p.hand_raised_at.isoformat() if p.hand_raised_at else ""})
        applied = True
    except lk.LiveKitUnavailable:
        applied = False
    event(db, room, user.id, "hand_raised" if raised else "hand_lowered", {"target": str(p.user_id)} if p.user_id != user.id else None)
    db.commit()
    return {"user_id": p.user_id, "hand_raised_at": p.hand_raised_at, "live_applied": applied}


CLIENT_STATES = {"connected": CONN_CONNECTED, "reconnecting": CONN_RECONNECTING, "disconnected": CONN_DISCONNECTED, "failed": CONN_DISCONNECTED}


def connection_report(db: Session, user: User, room_id: UUID, state: str, quality: str | None) -> dict:
    """The browser reports its own connection state (also works where no webhook is configured)."""
    room, _group, _manager = view_room(db, user, room_id)
    p = participant(db, room.id, user.id)
    if p is None or p.connection_status in (CONN_REMOVED, CONN_LEFT) or room.status != ROOM_LIVE:
        return {"ok": False}
    limit(db, user, "connection")
    new = CLIENT_STATES[state]
    if new != p.connection_status:
        if new == CONN_CONNECTED and p.joined_at is None:
            p.joined_at = now()
        if new == CONN_DISCONNECTED:
            p.left_at = now()
        p.connection_status = new
        event(db, room, user.id, f"client_{state}", {"quality": quality} if quality else None)
    db.commit()
    return {"ok": True}


# ---------- LiveKit webhook (signed) ----------

def _parse_uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except (ValueError, TypeError):
        return None


def _may_stay(db: Session, room: VideoRoom, p: VideoRoomParticipant | None) -> bool:
    if room.status != ROOM_LIVE or p is None or p.blocked or p.connection_status == CONN_REMOVED:
        return False
    user = db.get(User, p.user_id)
    if user is None or user.is_banned or not user.is_active:
        return False
    try:
        require_view(db, user, room.group_id)
    except HTTPException:
        return False
    return True


def webhook(db: Session, body: str, authorization: str | None) -> dict:
    try:
        ev = lk.verify_webhook(body, authorization)
    except Exception:  # noqa: BLE001 — any bad signature / body is the same answer
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_WEBHOOK") from None
    name = ev.room.name if ev.HasField("room") else ""
    room = db.scalar(select(VideoRoom).where(VideoRoom.room_name == name)) if name else None
    if room is None:
        return {"ok": True}
    t = now()
    if ev.event == "room_finished":
        if room.status == ROOM_LIVE:
            finish(db, room, None, "empty", close_livekit=False)
            event(db, room, None, "ended", {"reason": "empty"})
    elif ev.event in ("participant_joined", "participant_left", "participant_connection_aborted") and ev.HasField("participant"):
        identity = ev.participant.identity
        uid = _parse_uuid(identity)
        p = participant(db, room.id, uid) if uid else None
        if ev.event == "participant_joined":
            if not _may_stay(db, room, p):
                try:
                    lk.gateway.remove(room.room_name, identity)
                except lk.LiveKitUnavailable:
                    pass
                event(db, room, p.user_id if p else None, "intruder_removed", {"known": p is not None})
            else:
                p.connection_status, p.joined_at, p.left_at = CONN_CONNECTED, t, None
                p.join_count += 1
                event(db, room, p.user_id, "joined")
        elif p is not None and p.connection_status not in (CONN_REMOVED, CONN_LEFT):
            # the same user opened a second tab: LiveKit drops the older connection, the user is still there
            if ev.participant.disconnect_reason != lk.api.DUPLICATE_IDENTITY:
                p.connection_status, p.left_at, p.hand_raised_at = CONN_DISCONNECTED, t, None
                event(db, room, p.user_id, "disconnected")
    db.commit()
    return {"ok": True}
