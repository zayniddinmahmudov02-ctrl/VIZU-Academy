"""LiveKit SFU integration for one authorized video room per study group."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from livekit.api import AccessToken, VideoGrants

from app.core.config import settings
from app.models.study_group import (
    StudyGroup,
    StudyGroupVideoEvent,
    StudyGroupVideoRoom,
    StudyGroupVideoSession,
    VIDEO_ROOM_ENDED,
    VIDEO_ROOM_LIVE,
    VIDEO_ROOM_SCHEDULED,
)
from app.models.user import User
from app.services.study_groups.access import audit, display_name, is_manager, require_manage, require_view


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _room(db: Session, group: StudyGroup) -> StudyGroupVideoRoom:
    room = db.scalar(select(StudyGroupVideoRoom).where(StudyGroupVideoRoom.group_id == group.id))
    if room is None:
        room = StudyGroupVideoRoom(
            group_id=group.id,
            livekit_room_name=f"group-{group.id}",
            status=VIDEO_ROOM_SCHEDULED,
            max_participants=settings.LIVEKIT_PARTICIPANT_LIMIT,
        )
        db.add(room)
        db.flush()
    return room


def status_for(db: Session, user: User, group_id: UUID) -> dict:
    group, _ = require_view(db, user, group_id)
    room = _room(db, group)
    db.commit()
    session = db.scalar(
        select(StudyGroupVideoSession)
        .where(StudyGroupVideoSession.room_id == room.id, StudyGroupVideoSession.ended_at.is_(None))
        .order_by(StudyGroupVideoSession.started_at.desc())
        .limit(1)
    )
    return {
        "room_id": str(room.id),
        "livekit_room_name": room.livekit_room_name,
        "status": room.status,
        "scheduled_at": room.scheduled_at,
        "started_at": room.started_at,
        "ended_at": room.ended_at,
        "max_participants": room.max_participants,
        "recording_enabled": room.recording_enabled,
        "active": session is not None,
        "is_manager": is_manager(user, group),
        "livekit_configured": bool(settings.LIVEKIT_URL and settings.LIVEKIT_API_KEY and settings.LIVEKIT_API_SECRET),
    }


def schedule(db: Session, user: User, group_id: UUID, scheduled_at: datetime | None, max_participants: int | None) -> dict:
    group = require_manage(db, user, group_id)
    room = _room(db, group)
    room.scheduled_at = scheduled_at
    if max_participants is not None:
        room.max_participants = min(max_participants, settings.LIVEKIT_PARTICIPANT_LIMIT)
    audit(db, group.id, user.id, "video_scheduled", "video_room", room.id, {"scheduled_at": scheduled_at.isoformat() if scheduled_at else None})
    db.commit()
    db.refresh(room)
    return status_for(db, user, group_id)


def start(db: Session, user: User, group_id: UUID) -> dict:
    group = require_manage(db, user, group_id)
    room = _room(db, group)
    now = _now()
    if room.status != VIDEO_ROOM_LIVE:
        room.status = VIDEO_ROOM_LIVE
        room.started_at = now
        room.ended_at = None
        session = StudyGroupVideoSession(room_id=room.id, started_by_id=user.id, started_at=now)
        db.add(session)
        db.flush()
    else:
        session = db.scalar(
            select(StudyGroupVideoSession)
            .where(StudyGroupVideoSession.room_id == room.id, StudyGroupVideoSession.ended_at.is_(None))
            .order_by(StudyGroupVideoSession.started_at.desc())
            .limit(1)
        )
    audit(db, group.id, user.id, "video_started", "video_room", room.id)
    db.commit()
    return status_for(db, user, group_id)


def end(db: Session, user: User, group_id: UUID) -> dict:
    group = require_manage(db, user, group_id)
    room = _room(db, group)
    now = _now()
    room.status = VIDEO_ROOM_ENDED
    room.ended_at = now
    session = db.scalar(
        select(StudyGroupVideoSession)
        .where(StudyGroupVideoSession.room_id == room.id, StudyGroupVideoSession.ended_at.is_(None))
        .order_by(StudyGroupVideoSession.started_at.desc())
        .limit(1)
    )
    if session is not None:
        session.ended_at = now
        session.ended_by_id = user.id
    audit(db, group.id, user.id, "video_ended", "video_room", room.id)
    db.commit()
    return status_for(db, user, group_id)


def join(db: Session, user: User, group_id: UUID) -> dict:
    group, member = require_view(db, user, group_id)
    room = _room(db, group)
    now = _now()
    if room.status != VIDEO_ROOM_LIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="VIDEO_ROOM_NOT_LIVE")
    if not settings.LIVEKIT_URL or not settings.LIVEKIT_API_KEY or not settings.LIVEKIT_API_SECRET:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LIVEKIT_NOT_CONFIGURED")

    manager = is_manager(user, group)
    grants = VideoGrants(
        room_join=True,
        room=room.livekit_room_name,
        room_admin=manager,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
        can_publish_sources=["camera", "microphone", "screen_share", "screen_share_audio"],
        can_update_own_metadata=True,
    )
    token = (
        AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(str(user.id))
        .with_name(display_name(user))
        .with_metadata(display_name(user))
        .with_grants(grants)
        .with_ttl(timedelta(minutes=settings.LIVEKIT_TOKEN_TTL_MINUTES))
        .to_jwt()
    )
    session = db.scalar(
        select(StudyGroupVideoSession)
        .where(StudyGroupVideoSession.room_id == room.id, StudyGroupVideoSession.ended_at.is_(None))
        .order_by(StudyGroupVideoSession.started_at.desc())
        .limit(1)
    )
    db.add(StudyGroupVideoEvent(
        session_id=session.id if session is not None else None,
        room_id=room.id,
        user_id=user.id,
        kind="join",
    ))
    audit(db, group.id, user.id, "video_join", "video_room", room.id)
    db.commit()
    return {
        "url": settings.LIVEKIT_URL,
        "token": token,
        "room_name": room.livekit_room_name,
        "identity": str(user.id),
        "is_manager": manager,
        "participant_limit": room.max_participants or settings.LIVEKIT_PARTICIPANT_LIMIT,
    }


def event(db: Session, user: User, group_id: UUID, kind: str, meta: dict | None = None) -> dict:
    group, _ = require_view(db, user, group_id)
    room = _room(db, group)
    session = db.scalar(
        select(StudyGroupVideoSession)
        .where(StudyGroupVideoSession.room_id == room.id, StudyGroupVideoSession.ended_at.is_(None))
        .order_by(StudyGroupVideoSession.started_at.desc())
        .limit(1)
    )
    db.add(StudyGroupVideoEvent(session_id=session.id if session is not None else None, room_id=room.id, user_id=user.id, kind=kind, meta=meta))
    db.commit()
    return {"ok": True}


def control(db: Session, user: User, group_id: UUID, action: str, target_user_id: UUID | None = None) -> dict:
    group = require_manage(db, user, group_id)
    room = _room(db, group)
    session = db.scalar(
        select(StudyGroupVideoSession)
        .where(StudyGroupVideoSession.room_id == room.id, StudyGroupVideoSession.ended_at.is_(None))
        .order_by(StudyGroupVideoSession.started_at.desc())
        .limit(1)
    )
    if action not in ("mute_all", "kick", "mute", "allow_mic", "deny_mic", "allow_screen", "deny_screen", "close_chat"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="INVALID_VIDEO_CONTROL")
    db.add(StudyGroupVideoEvent(
        session_id=session.id if session is not None else None,
        room_id=room.id,
        user_id=target_user_id,
        kind=action,
        meta={"actor_id": str(user.id)},
    ))
    audit(db, group.id, user.id, f"video_{action}", "video_participant" if target_user_id else "video_room", target_user_id or room.id)
    db.commit()
    return {"ok": True, "action": action}
