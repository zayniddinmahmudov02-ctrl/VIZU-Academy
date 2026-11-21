"""Group video lessons: create / schedule / start / join / leave / end rooms, the participant list, admin monitoring.

Rules (who may do it: permissions.py):
* One live room per group (partial unique index). A room is scheduled (scheduled_at) or started at once.
* A join token is issued only for a live room, to a viewer of its group who was not blocked from that room, after a
  per-user and per-IP rate limit, and only while a student seat is free (max_participants counts students; hosts
  always get in: LiveKit's room limit is max_participants + HOST_SEATS). The token carries the
  permissions stored for the participant; the response is no-store and nothing logs it.
* A live room ends when a host ends it, a SUPER_ADMIN force-ends it, LiveKit closes it (nobody inside for 5 min,
  webhook) or after MAX_LIVE; a scheduled room nobody started is cancelled SCHEDULE_GRACE after its time.
* Teacher moderation and raised hands: moderation.py. Errors are UPPER_SNAKE codes."""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_rate_limit_event import AuthRateLimitEvent
from app.models.study_group import MEMBER_ACTIVE, MEMBER_STUDENT, StudyGroup, StudyGroupMember
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
    ROOM_CANCELLED,
    ROOM_ENDED,
    ROOM_LIVE,
    ROOM_SCHEDULED,
    VideoRoom,
    VideoRoomEvent,
    VideoRoomParticipant,
)
from app.services.auth.rate_limit import RateLimited, _check, ip_key
from app.services.study_groups import notify
from app.services.study_groups.access import audit, display_name, now
from app.services.study_groups.codes import user_key
from app.services.video_rooms import livekit_service as lk
from app.services.video_rooms.permissions import (
    can_chat,
    described,
    manage_group,
    moderate_room,
    require_group_active,
    role_for,
    room_not_found,
    sources,
    view_group,
    view_room,
)

MAX_LIVE = timedelta(hours=6)
SCHEDULE_GRACE = timedelta(hours=12)
MAX_SCHEDULE_AHEAD = timedelta(days=90)
MAX_UPCOMING_PER_GROUP = 20
JOINING_HOLDS_SEAT = timedelta(seconds=60)
HOST_SEATS = 3  # max_participants counts students; LiveKit's own limit leaves room for the hosts
TASHKENT = timezone(timedelta(hours=5))

LIMITS = {
    "create": (30, timedelta(hours=1)),
    "join": (12, timedelta(minutes=5)),
    "moderate": (120, timedelta(minutes=1)),
    "hand": (20, timedelta(minutes=1)),
    "connection": (40, timedelta(minutes=5)),
}
JOIN_PER_IP = (150, timedelta(minutes=5))  # a school network shares one IP


def error(code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def limit(db: Session, user: User, kind: str, ip: str | None = None) -> None:
    count, window = LIMITS[kind]
    action, key, ipk = f"video_{kind}", user_key(user.id), ip_key(ip) if kind == "join" else None
    try:
        _check(db, action, AuthRateLimitEvent.email_hash, key, count, window)
        if ipk:
            _check(db, action, AuthRateLimitEvent.ip_hash, ipk, *JOIN_PER_IP)
    except RateLimited as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="VIDEO_TOO_MANY_REQUESTS",
                            headers={"Retry-After": str(exc.retry_after)}) from None
    db.add(AuthRateLimitEvent(action=action, email_hash=key, ip_hash=ipk))


def event(db: Session, room: VideoRoom, user_id, event_type: str, meta: dict | None = None) -> None:
    db.add(VideoRoomEvent(room_id=room.id, user_id=user_id, event_type=event_type, meta=meta))


def room_metadata(room: VideoRoom) -> dict:
    """Room-wide state every client reads live from LiveKit room metadata."""
    return {"title": room.title, "chat": room.chat_enabled, "screen_share": room.students_can_share_screen, "mic": room.students_mic_allowed}


def participant(db: Session, room_id, user_id) -> VideoRoomParticipant | None:
    return db.scalar(select(VideoRoomParticipant).where(VideoRoomParticipant.room_id == room_id, VideoRoomParticipant.user_id == user_id))


def online_counts(db: Session, room_ids: list) -> dict:
    if not room_ids:
        return {}
    rows = db.execute(select(VideoRoomParticipant.room_id, func.count()).where(
        VideoRoomParticipant.room_id.in_(room_ids), VideoRoomParticipant.connection_status.in_(ONLINE)).group_by(VideoRoomParticipant.room_id))
    return dict(rows.all())


def room_out(room: VideoRoom, online: int = 0) -> dict:
    return {
        "id": room.id, "group_id": room.group_id, "title": room.title, "description": room.description, "status": room.status,
        "scheduled_at": room.scheduled_at, "started_at": room.started_at, "ended_at": room.ended_at, "end_reason": room.end_reason,
        "max_participants": room.max_participants, "chat_enabled": room.chat_enabled,
        "students_can_share_screen": room.students_can_share_screen, "students_mic_allowed": room.students_mic_allowed,
        "created_by": {"id": room.creator.id, "name": display_name(room.creator)} if room.creator else None,
        "online_count": online, "created_at": room.created_at,
    }


def _when(at: datetime) -> str:
    return at.astimezone(TASHKENT).strftime("%d.%m.%Y %H:%M")


def _clean_title(title: str) -> str:
    title = " ".join((title or "").split())
    if len(title) < 2:
        raise error(400, "TITLE_REQUIRED")
    return title[:200]


def _clean_description(text: str | None) -> str | None:
    text = (text or "").strip()
    return text[:2000] or None


def _check_schedule(at: datetime | None) -> datetime:
    if at is None:
        raise error(400, "SCHEDULE_REQUIRED")
    if at.tzinfo is None:
        raise error(400, "SCHEDULE_TIMEZONE_REQUIRED")
    t = now()
    if at < t - timedelta(minutes=5):
        raise error(400, "SCHEDULE_IN_PAST")
    if at > t + MAX_SCHEDULE_AHEAD:
        raise error(400, "SCHEDULE_TOO_FAR")
    return at


def finish(db: Session, room: VideoRoom, actor_id, reason: str, close_livekit: bool = True) -> bool:
    """End a live room in the database; then close it in LiveKit (removes everyone). Returns whether LiveKit confirmed."""
    t = now()
    room.status, room.ended_at, room.ended_by, room.end_reason = ROOM_ENDED, t, actor_id, reason
    for p in db.scalars(select(VideoRoomParticipant).where(VideoRoomParticipant.room_id == room.id,
                                                           VideoRoomParticipant.connection_status.in_((*ONLINE, CONN_JOINING)))):
        p.connection_status, p.left_at, p.hand_raised_at = CONN_LEFT, t, None
    if not close_livekit or not lk.configured():
        return False
    try:
        lk.gateway.delete_room(room.room_name)
        return True
    except lk.LiveKitUnavailable:
        return False


def expire(db: Session, room: VideoRoom) -> bool:
    t = now()
    if room.status == ROOM_LIVE and room.started_at and t - room.started_at > MAX_LIVE:
        finish(db, room, None, "expired")
        event(db, room, None, "ended", {"reason": "expired"})
        return True
    if room.status == ROOM_SCHEDULED and room.scheduled_at and t - room.scheduled_at > SCHEDULE_GRACE:
        room.status, room.ended_at, room.end_reason = ROOM_CANCELLED, t, "expired"
        event(db, room, None, "cancelled", {"reason": "expired"})
        return True
    return False


def _expire_group(db: Session, group_id) -> None:
    rooms = db.scalars(select(VideoRoom).where(VideoRoom.group_id == group_id, VideoRoom.status.in_((ROOM_LIVE, ROOM_SCHEDULED))))
    if any([expire(db, r) for r in rooms]):
        db.commit()


# ---------- rooms of a group ----------

def create(db: Session, user: User, group_id: UUID, data: dict) -> dict:
    group = manage_group(db, user, group_id)
    require_group_active(group)
    limit(db, user, "create")
    start_now = bool(data.get("start_now"))
    scheduled_at = data.get("scheduled_at")
    if not start_now:
        scheduled_at = _check_schedule(scheduled_at)
        upcoming = db.scalar(select(func.count()).select_from(VideoRoom).where(VideoRoom.group_id == group.id, VideoRoom.status == ROOM_SCHEDULED))
        if upcoming >= MAX_UPCOMING_PER_GROUP:
            raise error(409, "TOO_MANY_SCHEDULED")
    elif scheduled_at is not None:
        scheduled_at = _check_schedule(scheduled_at)
    cap = settings.VIDEO_ROOM_MAX_PARTICIPANTS
    room_id = uuid4()
    room = VideoRoom(id=room_id, group_id=group.id, created_by=user.id, room_name=f"vizu-{room_id.hex}", title=_clean_title(data.get("title")),
                     description=_clean_description(data.get("description")), status=ROOM_SCHEDULED, scheduled_at=scheduled_at,
                     max_participants=min(data.get("max_participants") or cap, cap),
                     chat_enabled=data.get("chat_enabled", True) is not False,
                     students_can_share_screen=bool(data.get("students_can_share_screen")))
    db.add(room)
    db.flush()
    event(db, room, user.id, "created", {"scheduled_at": scheduled_at.isoformat() if scheduled_at else None, "start_now": start_now})
    audit(db, group.id, user.id, "video_room_created", "video_room", room.id, {"title": room.title})
    if start_now:
        return _start(db, user, group, room)
    notify.to_students(db, group, f"{group.name}: video dars rejalashtirildi", f"{room.title} — {_when(scheduled_at)} (Toshkent vaqti).", "video")
    db.commit()
    db.refresh(room)
    return room_out(room)


def _start(db: Session, user: User, group: StudyGroup, room: VideoRoom) -> dict:
    require_group_active(group)
    if room.status != ROOM_SCHEDULED:
        raise error(409, "VIDEO_ROOM_NOT_SCHEDULED")
    if db.scalar(select(VideoRoom.id).where(VideoRoom.group_id == group.id, VideoRoom.status == ROOM_LIVE, VideoRoom.id != room.id)):
        raise error(409, "VIDEO_ROOM_ALREADY_LIVE")
    if not lk.configured():
        raise error(503, "VIDEO_SERVICE_NOT_CONFIGURED")
    room.status, room.started_at = ROOM_LIVE, now()
    try:
        db.flush()
    except IntegrityError:  # another start won the race (one live room per group)
        db.rollback()
        raise error(409, "VIDEO_ROOM_ALREADY_LIVE") from None
    try:
        lk.gateway.ensure_room(room.room_name, room.max_participants + HOST_SEATS, room_metadata(room))
    except lk.LiveKitUnavailable:
        db.rollback()
        raise error(503, "VIDEO_SERVICE_UNAVAILABLE") from None
    event(db, room, user.id, "started")
    audit(db, group.id, user.id, "video_room_started", "video_room", room.id)
    notify.to_students(db, group, f"{group.name}: video dars boshlandi", f"{room.title} — hozir qo'shiling.", "video")
    db.commit()
    db.refresh(room)
    return room_out(room)


def list_rooms(db: Session, user: User, group_id: UUID) -> dict:
    group, manager = view_group(db, user, group_id)
    _expire_group(db, group.id)
    rooms = list(db.scalars(select(VideoRoom).where(VideoRoom.group_id == group.id, VideoRoom.status.in_((ROOM_LIVE, ROOM_SCHEDULED)))
                            .order_by(VideoRoom.scheduled_at.asc().nulls_first())))
    past = list(db.scalars(select(VideoRoom).where(VideoRoom.group_id == group.id, VideoRoom.status.in_((ROOM_ENDED, ROOM_CANCELLED)))
                           .order_by(func.coalesce(VideoRoom.ended_at, VideoRoom.created_at).desc()).limit(20)))
    counts = online_counts(db, [r.id for r in rooms])
    live = next((r for r in rooms if r.status == ROOM_LIVE), None)
    return {
        "live": room_out(live, counts.get(live.id, 0)) if live else None,
        "upcoming": [room_out(r) for r in rooms if r.status == ROOM_SCHEDULED],
        "past": [room_out(r) for r in past],
        "is_manager": manager, "configured": lk.configured(),
    }


def active(db: Session, user: User, group_id: UUID) -> dict:
    group, manager = view_group(db, user, group_id)
    _expire_group(db, group.id)
    live = db.scalar(select(VideoRoom).where(VideoRoom.group_id == group.id, VideoRoom.status == ROOM_LIVE))
    return {"room": room_out(live, online_counts(db, [live.id]).get(live.id, 0)) if live else None, "is_manager": manager,
            "configured": lk.configured()}


# ---------- one room ----------

def get_room(db: Session, user: User, room_id: UUID) -> dict:
    room, group, manager = view_room(db, user, room_id)
    if expire(db, room):
        db.commit()
    p = participant(db, room.id, user.id)
    return {
        "room": room_out(room, online_counts(db, [room.id]).get(room.id, 0)),
        "group": {"id": group.id, "name": group.name, "level": group.level},
        "viewer": {"is_manager": manager, "permissions": described(room, p, manager), "connection_status": p.connection_status if p else None,
                   "blocked": bool(p and p.blocked and not manager), "hand_raised_at": p.hand_raised_at if p else None},
        "configured": lk.configured(),
    }


def update(db: Session, user: User, room_id: UUID, data: dict) -> dict:
    room, group = moderate_room(db, user, room_id)
    if room.status not in (ROOM_SCHEDULED, ROOM_LIVE):
        raise error(409, "VIDEO_ROOM_CLOSED")
    if "title" in data and data["title"] is not None:
        room.title = _clean_title(data["title"])
    if "description" in data:
        room.description = _clean_description(data["description"])
    if data.get("scheduled_at") is not None:
        if room.status != ROOM_SCHEDULED:
            raise error(409, "VIDEO_ROOM_NOT_SCHEDULED")
        room.scheduled_at = _check_schedule(data["scheduled_at"])
    event(db, room, user.id, "updated", {"fields": sorted(k for k in data if k in ("title", "description", "scheduled_at"))})
    if room.status == ROOM_LIVE and lk.configured():
        try:
            lk.gateway.set_room_metadata(room.room_name, room_metadata(room))
        except lk.LiveKitUnavailable:
            pass
    db.commit()
    db.refresh(room)
    return room_out(room)


def start(db: Session, user: User, room_id: UUID) -> dict:
    room, group = moderate_room(db, user, room_id)
    limit(db, user, "moderate")
    if expire(db, room):
        db.commit()
    return _start(db, user, group, room)


def cancel(db: Session, user: User, room_id: UUID) -> dict:
    room, group = moderate_room(db, user, room_id)
    if room.status != ROOM_SCHEDULED:
        raise error(409, "VIDEO_ROOM_NOT_SCHEDULED")
    room.status, room.ended_at, room.ended_by, room.end_reason = ROOM_CANCELLED, now(), user.id, "cancelled"
    event(db, room, user.id, "cancelled")
    audit(db, group.id, user.id, "video_room_cancelled", "video_room", room.id)
    notify.to_students(db, group, f"{group.name}: video dars bekor qilindi", f"{room.title} bo'lmaydi.", "video")
    db.commit()
    db.refresh(room)
    return room_out(room)


def end(db: Session, user: User, room_id: UUID) -> dict:
    room, group = moderate_room(db, user, room_id)
    if room.status != ROOM_LIVE:
        raise error(409, "VIDEO_ROOM_NOT_LIVE")
    closed = finish(db, room, user.id, "host")
    event(db, room, user.id, "ended", {"reason": "host", "livekit_closed": closed})
    audit(db, group.id, user.id, "video_room_ended", "video_room", room.id)
    db.commit()
    db.refresh(room)
    return {"room": room_out(room), "livekit_closed": closed}


def join(db: Session, user: User, room_id: UUID, ip: str | None) -> dict:
    room, group, manager = view_room(db, user, room_id)
    if expire(db, room):
        db.commit()
    if room.status == ROOM_SCHEDULED:
        raise error(409, "VIDEO_ROOM_NOT_STARTED")
    if room.status != ROOM_LIVE:
        raise error(409, "VIDEO_ROOM_NOT_LIVE")
    if not lk.configured():
        raise error(503, "VIDEO_SERVICE_NOT_CONFIGURED")
    limit(db, user, "join", ip)
    p = participant(db, room.id, user.id)
    if p is not None and p.blocked and not manager:
        raise error(403, "VIDEO_ROOM_REMOVED")
    t = now()
    if not manager:
        seated = db.scalar(select(func.count()).select_from(VideoRoomParticipant).where(
            VideoRoomParticipant.room_id == room.id, VideoRoomParticipant.user_id != user.id, VideoRoomParticipant.role != ROLE_HOST,
            VideoRoomParticipant.connection_status.in_(ONLINE)
            | ((VideoRoomParticipant.connection_status == CONN_JOINING) & (VideoRoomParticipant.last_token_at > t - JOINING_HOLDS_SEAT))))
        if seated >= room.max_participants:
            raise error(409, "VIDEO_ROOM_FULL")
    if p is None:
        p = VideoRoomParticipant(room_id=room.id, user_id=user.id, role=role_for(manager), can_speak=room.students_mic_allowed,
                                 can_share_screen=room.students_can_share_screen, can_chat=True)
        db.add(p)
    p.role = role_for(manager)
    if p.connection_status not in ONLINE:
        p.connection_status = CONN_JOINING
    p.last_token_at = t
    try:
        db.flush()
    except IntegrityError:  # a second tab created the row at the same moment
        db.rollback()
        raise error(409, "VIDEO_JOIN_IN_PROGRESS") from None
    try:
        lk.gateway.ensure_room(room.room_name, room.max_participants + HOST_SEATS, room_metadata(room))
    except lk.LiveKitUnavailable:
        db.rollback()
        raise error(503, "VIDEO_SERVICE_UNAVAILABLE") from None
    ttl = settings.VIDEO_ROOM_TOKEN_TTL_SECONDS
    token = lk.join_token(room_name=room.room_name, identity=str(user.id), name=display_name(user)[:80], role=p.role, sources=sources(p),
                          can_data=can_chat(room, p), ttl_seconds=ttl,
                          attributes={"vizu.role": p.role, "vizu.hand": p.hand_raised_at.isoformat() if p.hand_raised_at else ""})
    event(db, room, user.id, "token_issued", {"role": p.role})
    db.commit()
    db.refresh(room)
    return {"server_url": lk.public_url(), "token": token, "expires_in": ttl, "identity": str(user.id), "room": room_out(room),
            "group": {"id": group.id, "name": group.name, "level": group.level}, "permissions": described(room, p, manager)}


def leave(db: Session, user: User, room_id: UUID) -> dict:
    room, _group, _manager = view_room(db, user, room_id)
    p = participant(db, room.id, user.id)
    if p is not None and p.connection_status in (*ONLINE, CONN_JOINING, CONN_DISCONNECTED):
        had_hand = p.hand_raised_at is not None
        p.connection_status, p.left_at, p.hand_raised_at = CONN_LEFT, now(), None
        event(db, room, user.id, "left")
        if had_hand and room.status == ROOM_LIVE and lk.configured():
            try:
                lk.gateway.set_attributes(room.room_name, str(user.id), {"vizu.hand": ""})
            except lk.LiveKitUnavailable:
                pass
        db.commit()
    return {"ok": True}


def participants(db: Session, user: User, room_id: UUID) -> dict:
    room, group, manager = view_room(db, user, room_id)
    rows = list(db.scalars(select(VideoRoomParticipant).where(VideoRoomParticipant.room_id == room.id)
                           .order_by(VideoRoomParticipant.role.asc(), VideoRoomParticipant.joined_at.asc().nulls_last())))
    live, livekit = {}, "unconfigured"
    if room.status == ROOM_LIVE and lk.configured():
        try:
            live = {info.identity: info for info in lk.gateway.participants(room.room_name)}
            livekit = "available"
        except lk.LiveKitUnavailable:
            livekit = "unavailable"
    items = []
    for p in rows:
        info = live.get(str(p.user_id))
        conn = p.connection_status
        if info is not None and conn != CONN_REMOVED:
            conn = conn if conn == CONN_RECONNECTING else CONN_CONNECTED
        elif livekit == "available" and conn in ONLINE:
            conn = CONN_DISCONNECTED
        if not manager and conn not in ONLINE:
            continue
        item = {"user_id": p.user_id, "name": display_name(p.user), "role": p.role, "connection_status": conn,
                "joined_at": p.joined_at, "hand_raised_at": p.hand_raised_at, "can_speak": p.role == ROLE_HOST or p.can_speak,
                "can_share_screen": p.role == ROLE_HOST or p.can_share_screen, "can_chat": can_chat(room, p),
                **(lk.track_state(info) if info is not None else {"mic_on": False, "camera_on": False, "screen_sharing": False})}
        if manager:
            item.update({"left_at": p.left_at, "join_count": p.join_count, "blocked": p.blocked, "removed_at": p.removed_at})
        items.append(item)
    out = {"items": items, "online_count": sum(1 for i in items if i["connection_status"] in ONLINE), "livekit": livekit}
    if manager:
        seen = {p.user_id for p in rows if p.connection_status in ONLINE or str(p.user_id) in live}
        members = db.scalars(select(StudyGroupMember).where(StudyGroupMember.group_id == group.id, StudyGroupMember.status == MEMBER_ACTIVE,
                                                            StudyGroupMember.role == MEMBER_STUDENT))
        out["absent"] = sorted(({"user_id": m.user_id, "name": display_name(m.user)} for m in members if m.user_id not in seen),
                               key=lambda x: x["name"].lower())
    return out


# ---------- admin monitoring (SUPER_ADMIN; the router enforces it) ----------

def admin_overview(db: Session) -> dict:
    rooms = list(db.scalars(select(VideoRoom).where(VideoRoom.status.in_((ROOM_LIVE, ROOM_SCHEDULED)))
                            .order_by(VideoRoom.status.asc(), VideoRoom.scheduled_at.asc().nulls_first()).limit(200)))
    for r in rooms:
        expire(db, r)
    db.commit()
    rooms = [r for r in rooms if r.status in (ROOM_LIVE, ROOM_SCHEDULED)]
    recent = list(db.scalars(select(VideoRoom).where(VideoRoom.status.in_((ROOM_ENDED, ROOM_CANCELLED)))
                             .order_by(func.coalesce(VideoRoom.ended_at, VideoRoom.created_at).desc()).limit(20)))
    groups = {g.id: g for g in db.scalars(select(StudyGroup).where(StudyGroup.id.in_([r.group_id for r in rooms + recent] or [None])))}
    counts = online_counts(db, [r.id for r in rooms])
    status_, server = lk.gateway.status(), {}
    if status_ == "available":
        try:
            server = lk.gateway.rooms()
        except lk.LiveKitUnavailable:
            status_ = "unavailable"

    def row(r: VideoRoom) -> dict:
        g = groups.get(r.group_id)
        out = room_out(r, counts.get(r.id, 0))
        out["group"] = {"id": r.group_id, "name": g.name if g else "—", "level": g.level if g else None,
                        "teacher": display_name(g.teacher) if g else "—"}
        out["server_participants"] = server.get(r.room_name) if r.status == ROOM_LIVE and status_ == "available" else None
        out["server_room_active"] = (r.room_name in server) if r.status == ROOM_LIVE and status_ == "available" else None
        return out

    live = [row(r) for r in rooms if r.status == ROOM_LIVE]
    return {
        "livekit_status": status_, "live": live, "scheduled": [row(r) for r in rooms if r.status == ROOM_SCHEDULED],
        "recent": [row(r) for r in recent],
        "totals": {"live": len(live), "scheduled": sum(1 for r in rooms if r.status == ROOM_SCHEDULED),
                   "online": sum(x["online_count"] for x in live)},
        "limits": {"max_participants": settings.VIDEO_ROOM_MAX_PARTICIPANTS, "token_ttl_seconds": settings.VIDEO_ROOM_TOKEN_TTL_SECONDS},
    }


def admin_end(db: Session, admin: User, room_id: UUID) -> dict:
    room = db.get(VideoRoom, room_id)
    if room is None:
        raise room_not_found()
    if room.status != ROOM_LIVE:
        raise error(409, "VIDEO_ROOM_NOT_LIVE")
    closed = finish(db, room, admin.id, "admin")
    event(db, room, admin.id, "ended", {"reason": "admin", "livekit_closed": closed})
    audit(db, room.group_id, admin.id, "video_room_force_ended", "video_room", room.id)
    db.commit()
    db.refresh(room)
    return {"room": room_out(room), "livekit_closed": closed}
