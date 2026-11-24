"""Group video lessons API (LiveKit SFU). Thin: validation here, rules in app.services.video_rooms.

Auth per endpoint:
* every room / group endpoint: `get_current_user`; who may see, join or moderate is decided in
  services/video_rooms/permissions.py (group teacher / SUPER_ADMIN moderate, active members join, others 404);
* `/admin/video-rooms*`: `require_super_admin` (the groups admin policy: only a SUPER_ADMIN sees every group);
* `POST /video-rooms/webhooks/livekit`: public by design, accepted only with a valid LiveKit signature.
Bodies never carry the caller's id, role or a room name. The join response (LiveKit token) is no-store."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_super_admin
from app.core.client_ip import client_ip
from app.db.session import get_db
from app.models.user import User
from app.services.video_rooms import moderation, service

router = APIRouter(tags=["Video rooms"])

MAX_WEBHOOK_BYTES = 64 * 1024


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RoomCreate(_In):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(None, max_length=2000)
    scheduled_at: datetime | None = None
    start_now: bool = False
    max_participants: int | None = Field(None, ge=2, le=500)
    chat_enabled: bool = True
    students_can_share_screen: bool = False


class RoomUpdate(_In):
    title: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(None, max_length=2000)
    scheduled_at: datetime | None = None


class TargetIn(_In):
    user_id: UUID


class PermissionIn(_In):
    allowed: bool
    user_id: UUID | None = None  # none = every student (and the room default)


class MuteAllIn(_In):
    lock: bool = False  # also take the microphone permission away


class RemoveIn(_In):
    user_id: UUID
    block: bool = False  # may not join this room again


class HandIn(_In):
    raised: bool = True
    user_id: UUID | None = None  # a host lowering someone else's hand


class ConnectionIn(_In):
    state: Literal["connected", "reconnecting", "disconnected", "failed"]
    quality: Literal["excellent", "good", "poor", "lost", "unknown"] | None = None


# ---------- LiveKit webhook (declared before /video-rooms/{room_id}) ----------

@router.post("/video-rooms/webhooks/livekit", include_in_schema=False)
async def livekit_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    if len(body) > MAX_WEBHOOK_BYTES:
        return Response(status_code=413)
    return await run_in_threadpool(moderation.webhook, db, body.decode("utf-8", "replace"), request.headers.get("authorization"))


# ---------- admin monitoring ----------

@router.get("/admin/video-rooms")
def admin_rooms(db: Session = Depends(get_db), _admin: User = Depends(require_super_admin)):
    return service.admin_overview(db)


@router.post("/admin/video-rooms/{room_id}/end")
def admin_end(room_id: UUID, db: Session = Depends(get_db), admin: User = Depends(require_super_admin)):
    return service.admin_end(db, admin, room_id)


# ---------- rooms of a group ----------

@router.post("/groups/{group_id}/video-rooms", status_code=201)
def create_room(group_id: UUID, data: RoomCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.create(db, user, group_id, data.model_dump())


@router.get("/groups/{group_id}/video-rooms")
def list_rooms(group_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.list_rooms(db, user, group_id)


@router.get("/groups/{group_id}/video-rooms/active")
def active_room(group_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.active(db, user, group_id)


# ---------- one room ----------

@router.get("/video-rooms/{room_id}")
def get_room(room_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.get_room(db, user, room_id)


@router.patch("/video-rooms/{room_id}")
def update_room(room_id: UUID, data: RoomUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.update(db, user, room_id, data.model_dump(exclude_unset=True))


@router.post("/video-rooms/{room_id}/start")
def start_room(room_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.start(db, user, room_id)


@router.post("/video-rooms/{room_id}/cancel")
def cancel_room(room_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.cancel(db, user, room_id)


@router.post("/video-rooms/{room_id}/end")
def end_room(room_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.end(db, user, room_id)


@router.post("/video-rooms/{room_id}/join")
def join_room(room_id: UUID, request: Request, response: Response, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    response.headers["Cache-Control"] = "no-store"
    return service.join(db, user, room_id, client_ip(request))


@router.post("/video-rooms/{room_id}/leave")
def leave_room(room_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.leave(db, user, room_id)


@router.get("/video-rooms/{room_id}/participants")
def room_participants(room_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.participants(db, user, room_id)


@router.post("/video-rooms/{room_id}/connection")
def connection(room_id: UUID, data: ConnectionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return moderation.connection_report(db, user, room_id, data.state, data.quality)


@router.post("/video-rooms/{room_id}/raise-hand")
def raise_hand(room_id: UUID, data: HandIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return moderation.raise_hand(db, user, room_id, data.raised, data.user_id)


# ---------- teacher moderation ----------

@router.post("/video-rooms/{room_id}/mute-participant")
def mute_participant(room_id: UUID, data: TargetIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return moderation.mute_participant(db, user, room_id, data.user_id)


@router.post("/video-rooms/{room_id}/mute-all")
def mute_all(room_id: UUID, data: MuteAllIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return moderation.mute_all(db, user, room_id, data.lock)


@router.post("/video-rooms/{room_id}/mic-permission")
def mic_permission(room_id: UUID, data: PermissionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return moderation.mic_permission(db, user, room_id, data.allowed, data.user_id)


@router.post("/video-rooms/{room_id}/camera-permission")
def camera_permission(room_id: UUID, data: PermissionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return moderation.camera_permission(db, user, room_id, data.allowed, data.user_id)


@router.post("/video-rooms/{room_id}/screen-share-permission")
def screen_share_permission(room_id: UUID, data: PermissionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return moderation.screen_share_permission(db, user, room_id, data.allowed, data.user_id)


@router.post("/video-rooms/{room_id}/chat-permission")
def chat_permission(room_id: UUID, data: PermissionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return moderation.chat_permission(db, user, room_id, data.allowed, data.user_id)


@router.post("/video-rooms/{room_id}/remove-participant")
def remove_participant(room_id: UUID, data: RemoveIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return moderation.remove_participant(db, user, room_id, data.user_id, data.block)
