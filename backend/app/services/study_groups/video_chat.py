"""LiveKit SFU integration for one authorized video room per study group."""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

import aiohttp
from fastapi import HTTPException, status
from livekit.api import (
    AccessToken,
    CreateRoomRequest,
    DeleteRoomRequest,
    ListParticipantsRequest,
    ListRoomsRequest,
    MuteRoomTrackRequest,
    RoomParticipantIdentity,
    UpdateParticipantRequest,
    VideoGrants,
    LiveKitAPI,
)
from livekit.api.twirp_client import ServerError
from livekit.protocol.models import ParticipantPermission, TrackSource, TrackType
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging.logger import logger
from app.models.auth_rate_limit_event import AuthRateLimitEvent
from app.models.study_group import (
    GROUP_ACTIVE,
    MEMBER_ACTIVE,
    MEMBER_STUDENT,
    VIDEO_ROOM_ENDED,
    VIDEO_ROOM_LIVE,
    VIDEO_ROOM_SCHEDULED,
    StudyGroup,
    StudyGroupMember,
    StudyGroupVideoEvent,
    StudyGroupVideoRoom,
    StudyGroupVideoSession,
)
from app.models.user import User
from app.services.auth.rate_limit import RateLimited, _check, ip_key
from app.services.study_groups.access import audit, display_name, is_manager, require_manage, require_view
from app.services.study_groups.codes import user_key

ACTION_VIDEO_JOIN = "video_join"
ACTION_VIDEO_EVENT = "video_event"
VIDEO_JOIN_WINDOW = timedelta(minutes=1)
VIDEO_EVENT_WINDOW = timedelta(minutes=1)
MAX_VIDEO_JOINS = 10
MAX_VIDEO_EVENTS = 120
MAX_VIDEO_IP_JOINS = 60
MAX_VIDEO_IP_EVENTS = 1200
VIDEO_EVENTS = {
    "join",
    "leave",
    "raise_hand",
    "lower_hand",
    "camera_on",
    "camera_off",
    "mic_on",
    "mic_off",
    "screen_share_start",
    "screen_share_stop",
    "connection_reconnecting",
    "connection_reconnected",
    "connection_disconnected",
    "connection_quality",
    "track_published",
    "track_unpublished",
    "participant_metadata_changed",
}
VIDEO_CONTROLS = {"mute_all", "kick", "mute", "allow_mic", "deny_mic", "allow_screen", "deny_screen"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _require_livekit() -> tuple[str, str, str]:
    url = settings.LIVEKIT_URL.strip()
    if not settings.LIVEKIT_API_KEY or not settings.LIVEKIT_API_SECRET or not url:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LIVEKIT_NOT_CONFIGURED")
    if not url.startswith(("wss://", "ws://")):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LIVEKIT_URL_MUST_USE_WS_OR_WSS")
    api_url = url.replace("wss://", "https://", 1) if url.startswith("wss://") else url.replace("ws://", "http://", 1)
    return url, api_url, settings.LIVEKIT_API_KEY


async def _with_livekit(operation: str, action):
    _, api_url, api_key = _require_livekit()
    client = LiveKitAPI(api_url, api_key, settings.LIVEKIT_API_SECRET)
    try:
        return await action(client)
    except ServerError as exc:
        logger.error("LiveKit %s failed: code=%s status=%s", operation, exc.code, exc.status)
        if exc.code == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VIDEO_PARTICIPANT_NOT_FOUND") from exc
        if exc.code == "resource_exhausted":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="VIDEO_ROOM_FULL") from exc
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LIVEKIT_UNAVAILABLE") from exc
    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        logger.error("LiveKit %s failed: %s", operation, type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LIVEKIT_UNAVAILABLE") from exc
    finally:
        await client.aclose()


def _room(db: Session, group: StudyGroup, *, lock: bool = False) -> StudyGroupVideoRoom:
    query = select(StudyGroupVideoRoom).where(StudyGroupVideoRoom.group_id == group.id)
    if lock:
        query = query.with_for_update()
    room = db.scalar(query)
    if room is None:
        room = StudyGroupVideoRoom(
            group_id=group.id,
            livekit_room_name=f"group-{group.id}",
            status=VIDEO_ROOM_SCHEDULED,
            max_participants=settings.LIVEKIT_PARTICIPANT_LIMIT,
        )
        db.add(room)
        db.flush()
    if room.livekit_room_name != f"group-{group.id}":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="VIDEO_ROOM_CONFIGURATION_INVALID")
    return room


def _active_session(db: Session, room_id: UUID) -> StudyGroupVideoSession | None:
    return db.scalar(
        select(StudyGroupVideoSession)
        .where(StudyGroupVideoSession.room_id == room_id, StudyGroupVideoSession.ended_at.is_(None))
        .order_by(StudyGroupVideoSession.started_at.desc())
        .limit(1)
    )


def _rate_limit(db: Session, user: User, ip: str | None, action: str) -> None:
    if action == ACTION_VIDEO_JOIN:
        window, user_limit, ip_limit = VIDEO_JOIN_WINDOW, MAX_VIDEO_JOINS, MAX_VIDEO_IP_JOINS
    else:
        window, user_limit, ip_limit = VIDEO_EVENT_WINDOW, MAX_VIDEO_EVENTS, MAX_VIDEO_IP_EVENTS
    user_hash = user_key(user.id)
    ip_hash = ip_key(ip)
    try:
        _check(db, action, AuthRateLimitEvent.email_hash, user_hash, user_limit, window)
        _check(db, action, AuthRateLimitEvent.ip_hash, ip_hash, ip_limit, window)
    except RateLimited as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="VIDEO_RATE_LIMITED",
                            headers={"Retry-After": str(exc.retry_after)}) from exc
    db.add(AuthRateLimitEvent(action=action, email_hash=user_hash, ip_hash=ip_hash))


def status_for(db: Session, user: User, group_id: UUID) -> dict:
    group, _ = require_view(db, user, group_id)
    room = _room(db, group)
    db.commit()
    session = _active_session(db, room.id)
    return {
        "room_id": str(room.id),
        "status": room.status,
        "scheduled_at": room.scheduled_at,
        "started_at": session.started_at if session else room.started_at,
        "ended_at": room.ended_at,
        "max_participants": room.max_participants or settings.LIVEKIT_PARTICIPANT_LIMIT,
        "active": session is not None,
        "is_manager": is_manager(user, group),
        "livekit_configured": bool(settings.LIVEKIT_URL and settings.LIVEKIT_API_KEY and settings.LIVEKIT_API_SECRET),
    }


def schedule(db: Session, user: User, group_id: UUID, scheduled_at: datetime | None, max_participants: int | None) -> dict:
    group = require_manage(db, user, group_id)
    room = _room(db, group, lock=True)
    if room.status == VIDEO_ROOM_LIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="VIDEO_ROOM_ALREADY_LIVE")
    room.scheduled_at = scheduled_at
    if max_participants is not None:
        room.max_participants = min(max_participants, settings.LIVEKIT_PARTICIPANT_LIMIT)
    audit(db, group.id, user.id, "video_scheduled", "video_room", room.id,
          {"scheduled_at": scheduled_at.isoformat() if scheduled_at else None})
    db.commit()
    return status_for(db, user, group_id)


async def _create_remote_room(room_name: str, participant_limit: int) -> None:
    async def create(client: LiveKitAPI):
        response = await client.room.list_rooms(ListRoomsRequest(names=[room_name]))
        if response.rooms:
            participants = await client.room.list_participants(ListParticipantsRequest(room=room_name))
            if participants.participants:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="VIDEO_ROOM_ALREADY_HAS_PARTICIPANTS")
            await client.room.delete_room(DeleteRoomRequest(room=room_name))
        return await client.room.create_room(CreateRoomRequest(
            name=room_name,
            empty_timeout=60,
            max_participants=participant_limit,
        ))

    await _with_livekit("create room", create)


async def start(db: Session, user: User, group_id: UUID) -> dict:
    group = require_manage(db, user, group_id)
    if group.status != GROUP_ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="GROUP_NOT_ACTIVE")
    room = _room(db, group, lock=True)
    if room.status != VIDEO_ROOM_LIVE:
        await _create_remote_room(room.livekit_room_name, room.max_participants or settings.LIVEKIT_PARTICIPANT_LIMIT)
        now = _now()
        room.status = VIDEO_ROOM_LIVE
        room.started_at = now
        room.ended_at = None
        db.add(StudyGroupVideoSession(room_id=room.id, started_by_id=user.id, started_at=now))
    audit(db, group.id, user.id, "video_started", "video_room", room.id)
    db.commit()
    return status_for(db, user, group_id)


async def _delete_remote_room(room_name: str) -> None:
    async def delete(client: LiveKitAPI):
        rooms = await client.room.list_rooms(ListRoomsRequest(names=[room_name]))
        if rooms.rooms:
            return await client.room.delete_room(DeleteRoomRequest(room=room_name))
        return None

    await _with_livekit("delete room", delete)


async def end(db: Session, user: User, group_id: UUID) -> dict:
    group = require_manage(db, user, group_id)
    room = _room(db, group, lock=True)
    if room.status == VIDEO_ROOM_LIVE:
        await _delete_remote_room(room.livekit_room_name)
    now = _now()
    room.status = VIDEO_ROOM_ENDED
    room.ended_at = now
    session = _active_session(db, room.id)
    if session is not None:
        session.ended_at = now
        session.ended_by_id = user.id
    audit(db, group.id, user.id, "video_ended", "video_room", room.id)
    db.commit()
    return status_for(db, user, group_id)


def join(db: Session, user: User, group_id: UUID, ip: str | None = None) -> dict:
    group, _ = require_view(db, user, group_id)
    if group.status != GROUP_ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="GROUP_NOT_ACTIVE")
    room = _room(db, group, lock=True)
    if room.status != VIDEO_ROOM_LIVE or _active_session(db, room.id) is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="VIDEO_ROOM_NOT_LIVE")
    url, _, api_key = _require_livekit()
    _rate_limit(db, user, ip, ACTION_VIDEO_JOIN)

    manager = is_manager(user, group)
    participant_role = "teacher" if group.teacher_id == user.id else "admin" if user.role == "SUPER_ADMIN" else "student"
    grants = VideoGrants(
        room_join=True,
        room=room.livekit_room_name,
        room_admin=False,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
        can_publish_sources=["camera", "microphone", "screen_share", "screen_share_audio"],
        can_update_own_metadata=False,
    )
    token = (
        AccessToken(api_key, settings.LIVEKIT_API_SECRET)
        .with_identity(str(user.id))
        .with_name(display_name(user))
        .with_metadata(f'{{"role":"{participant_role}"}}')
        .with_grants(grants)
        .with_ttl(timedelta(minutes=settings.LIVEKIT_TOKEN_TTL_MINUTES))
        .to_jwt()
    )
    audit(db, group.id, user.id, "video_token_issued", "video_room", room.id)
    db.commit()
    return {
        "url": url,
        "token": token,
        "room_name": room.livekit_room_name,
        "identity": str(user.id),
        "is_manager": manager,
        "participant_limit": room.max_participants or settings.LIVEKIT_PARTICIPANT_LIMIT,
    }


def event(db: Session, user: User, group_id: UUID, kind: str, ip: str | None = None) -> dict:
    if kind not in VIDEO_EVENTS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="INVALID_VIDEO_EVENT")
    group, _ = require_view(db, user, group_id)
    room = _room(db, group)
    session = _active_session(db, room.id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="VIDEO_ROOM_NOT_LIVE")
    _rate_limit(db, user, ip, ACTION_VIDEO_EVENT)
    db.add(StudyGroupVideoEvent(session_id=session.id, room_id=room.id, user_id=user.id, kind=kind))
    db.commit()
    return {"ok": True}


async def _participants(room_name: str):
    async def list_participants(client: LiveKitAPI):
        response = await client.room.list_participants(ListParticipantsRequest(room=room_name))
        return response.participants

    return await _with_livekit("list participants", list_participants)


async def _set_participant_permission(room_name: str, identity: str, *, mic: bool | None = None, screen: bool | None = None):
    async def update(client: LiveKitAPI):
        current = await client.room.get_participant(RoomParticipantIdentity(room=room_name, identity=identity))
        permission = current.permission
        sources = set(permission.can_publish_sources) if permission.can_publish_sources else {
            TrackSource.CAMERA,
            TrackSource.MICROPHONE,
            TrackSource.SCREEN_SHARE,
            TrackSource.SCREEN_SHARE_AUDIO,
        }
        if mic is not None:
            if mic:
                sources.update((TrackSource.MICROPHONE,))
            else:
                sources.discard(TrackSource.MICROPHONE)
                sources.discard(TrackSource.SCREEN_SHARE_AUDIO)
        if screen is not None:
            if screen:
                sources.update((TrackSource.SCREEN_SHARE, TrackSource.SCREEN_SHARE_AUDIO))
            else:
                sources.discard(TrackSource.SCREEN_SHARE)
                sources.discard(TrackSource.SCREEN_SHARE_AUDIO)
        return await client.room.update_participant(UpdateParticipantRequest(
            room=room_name,
            identity=identity,
            permission=ParticipantPermission(
                can_subscribe=permission.can_subscribe,
                can_publish=permission.can_publish,
                can_publish_data=permission.can_publish_data,
                can_publish_sources=sorted(sources),
                hidden=permission.hidden,
                recorder=permission.recorder,
            ),
        ))

    return await _with_livekit("update participant permissions", update)


async def control(db: Session, user: User, group_id: UUID, action: str, target_user_id: UUID | None = None,
                  ip: str | None = None) -> dict:
    group = require_manage(db, user, group_id)
    if action not in VIDEO_CONTROLS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="INVALID_VIDEO_CONTROL")
    if action != "mute_all" and target_user_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="VIDEO_TARGET_REQUIRED")
    room = _room(db, group)
    if room.status != VIDEO_ROOM_LIVE or _active_session(db, room.id) is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="VIDEO_ROOM_NOT_LIVE")
    _rate_limit(db, user, ip, ACTION_VIDEO_EVENT)

    affected = 0
    if action == "mute_all":
        async def mute_all_audio(client: LiveKitAPI):
            response = await client.room.list_participants(ListParticipantsRequest(room=room.livekit_room_name))
            count = 0
            for participant in response.participants:
                if participant.identity == str(user.id):
                    continue
                for track in participant.tracks:
                    if track.type == TrackType.AUDIO and not track.muted:
                        await client.room.mute_published_track(MuteRoomTrackRequest(
                            room=room.livekit_room_name,
                            identity=participant.identity,
                            track_sid=track.sid,
                            muted=True,
                        ))
                        count += 1
            return count
        affected = await _with_livekit("mute all participant audio", mute_all_audio)
    else:
        member = db.scalar(select(StudyGroupMember).where(
            StudyGroupMember.group_id == group.id,
            StudyGroupMember.user_id == target_user_id,
            StudyGroupMember.status == MEMBER_ACTIVE,
            StudyGroupMember.role == MEMBER_STUDENT,
        ))
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VIDEO_PARTICIPANT_NOT_FOUND")
        identity = str(target_user_id)
        if action == "kick":
            async def remove(client: LiveKitAPI):
                return await client.room.remove_participant(RoomParticipantIdentity(room=room.livekit_room_name, identity=identity))
            await _with_livekit("remove participant", remove)
        elif action == "mute":
            participants = await _participants(room.livekit_room_name)
            participant = next((p for p in participants if p.identity == identity), None)
            if participant is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VIDEO_PARTICIPANT_NOT_FOUND")
            for track in participant.tracks:
                if track.type == TrackType.AUDIO and not track.muted:
                    async def mute(client: LiveKitAPI, track_sid=track.sid):
                        return await client.room.mute_published_track(MuteRoomTrackRequest(
                            room=room.livekit_room_name,
                            identity=identity,
                            track_sid=track_sid,
                            muted=True,
                        ))
                    await _with_livekit("mute participant audio", mute)
                    affected += 1
        elif action in ("allow_mic", "deny_mic", "allow_screen", "deny_screen"):
            await _set_participant_permission(
                room.livekit_room_name,
                identity,
                mic=True if action == "allow_mic" else False if action == "deny_mic" else None,
                screen=True if action == "allow_screen" else False if action == "deny_screen" else None,
            )
        affected = max(affected, 1)

    session = _active_session(db, room.id)
    db.add(StudyGroupVideoEvent(
        session_id=session.id if session is not None else None,
        room_id=room.id,
        user_id=target_user_id,
        kind=action,
        meta={"actor_id": str(user.id), "affected_tracks": affected},
    ))
    audit(db, group.id, user.id, f"video_{action}", "video_participant" if target_user_id else "video_room",
          target_user_id or room.id, {"affected_tracks": affected})
    db.commit()
    return {"ok": True, "action": action, "affected_tracks": affected}


async def admin_status(db: Session) -> dict:
    rooms = list(db.scalars(
        select(StudyGroupVideoRoom)
        .where(StudyGroupVideoRoom.status.in_((VIDEO_ROOM_SCHEDULED, VIDEO_ROOM_LIVE)))
        .order_by(StudyGroupVideoRoom.started_at.desc().nullslast(), StudyGroupVideoRoom.scheduled_at.desc().nullslast())
    ).unique())
    groups_by_id = {group.id: group for group in db.scalars(
        select(StudyGroup).where(StudyGroup.id.in_([room.group_id for room in rooms]))
    ).unique()} if rooms else {}
    remote_rooms = None
    livekit_status = "unconfigured"
    if settings.LIVEKIT_URL and settings.LIVEKIT_API_KEY and settings.LIVEKIT_API_SECRET:
        async def list_rooms(client: LiveKitAPI):
            return await client.room.list_rooms(ListRoomsRequest())
        try:
            response = await _with_livekit("list rooms", list_rooms)
            remote_rooms = {item.name: item for item in response.rooms}
            livekit_status = "available"
        except HTTPException as exc:
            livekit_status = "unavailable"
            remote_rooms = {}
            logger.warning("LiveKit admin status unavailable: %s", exc.detail)

    active_sessions = {room.id: _active_session(db, room.id) for room in rooms}
    session_ids = [session.id for session in active_sessions.values() if session is not None]
    event_counts: dict[tuple[UUID, str], int] = {}
    if session_ids:
        rows = db.execute(
            select(StudyGroupVideoEvent.session_id, StudyGroupVideoEvent.kind, func.count())
            .where(
                StudyGroupVideoEvent.session_id.in_(session_ids),
                StudyGroupVideoEvent.kind.in_(("connection_disconnected", "connection_reconnecting", "connection_reconnected")),
            )
            .group_by(StudyGroupVideoEvent.session_id, StudyGroupVideoEvent.kind)
        )
        event_counts = {(session_id, kind): count for session_id, kind, count in rows}

    output = []
    for room in rooms:
        group = groups_by_id.get(room.group_id)
        session = active_sessions.get(room.id)
        livekit_room = remote_rooms.get(room.livekit_room_name) if remote_rooms is not None else None
        room_event_counts = {
            kind: event_counts.get((session.id, kind), 0) if session else 0
            for kind in ("connection_disconnected", "connection_reconnecting", "connection_reconnected")
        }
        output.append({
            "room_id": str(room.id),
            "group_id": str(room.group_id),
            "group_name": group.name if group else "—",
            "teacher": display_name(group.teacher) if group else "—",
            "status": room.status,
            "scheduled_at": room.scheduled_at,
            "started_at": session.started_at if session else room.started_at,
            "duration_seconds": max(0, int((_now() - session.started_at).total_seconds())) if session else None,
            "participant_count": livekit_room.num_participants if livekit_room else (0 if remote_rooms is not None else None),
            "participant_limit": room.max_participants or settings.LIVEKIT_PARTICIPANT_LIMIT,
            "server_room_active": livekit_room is not None if remote_rooms is not None else None,
            "connection_disconnects": room_event_counts["connection_disconnected"],
            "reconnect_attempts": room_event_counts["connection_reconnecting"],
            "reconnect_successes": room_event_counts["connection_reconnected"],
        })
    return {
        "checked_at": _now(),
        "livekit_status": livekit_status,
        "rooms": output,
    }
