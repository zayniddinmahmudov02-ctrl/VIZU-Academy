"""The only code that talks to the LiveKit server: join tokens, server API, webhooks.

* LIVEKIT_API_KEY / LIVEKIT_API_SECRET come from settings and never leave the
  backend. Nothing here logs a token, a secret or a request body.
* A join token is bound to one room and one identity (the user id), lives
  VIDEO_ROOM_TOKEN_TTL_SECONDS, and may not change its own metadata: raised
  hands and roles are set by the backend only.
* Server API calls are short (5 s timeout) and run on a private event loop,
  so the sync endpoints that call them keep their sync DB session
  (known-issues #23). A failed call raises LiveKitUnavailable; "participant /
  room not found" is not a failure (returns False / empty).

Tests replace `gateway` with a fake (see tests/test_video_rooms.py)."""

import asyncio
import concurrent.futures
import json
import logging
from datetime import timedelta

import aiohttp
from livekit import api

from app.core.config import settings

log = logging.getLogger(__name__)

TIMEOUT_SECONDS = 5
EMPTY_TIMEOUT = 600  # a started room nobody joins closes after 10 min
DEPARTURE_TIMEOUT = 300  # ... and 5 min after the last person left (a reload must not end the lesson)

CAMERA = "camera"
MICROPHONE = "microphone"
SCREEN_SHARE = "screen_share"
SCREEN_SHARE_AUDIO = "screen_share_audio"
_SOURCE = {CAMERA: api.TrackSource.CAMERA, MICROPHONE: api.TrackSource.MICROPHONE,
           SCREEN_SHARE: api.TrackSource.SCREEN_SHARE, SCREEN_SHARE_AUDIO: api.TrackSource.SCREEN_SHARE_AUDIO}


class LiveKitUnavailable(Exception):
    pass


def configured() -> bool:
    return bool(settings.LIVEKIT_URL and settings.LIVEKIT_API_KEY and settings.LIVEKIT_API_SECRET)


def public_url() -> str:
    return settings.LIVEKIT_URL


def api_url() -> str:
    url = settings.LIVEKIT_API_URL or settings.LIVEKIT_URL
    if url.startswith("wss://"):
        return "https://" + url[len("wss://"):]
    if url.startswith("ws://"):
        return "http://" + url[len("ws://"):]
    return url


def join_token(*, room_name: str, identity: str, name: str, role: str, sources: list[str], can_data: bool,
               attributes: dict[str, str], ttl_seconds: int) -> str:
    """LiveKit treats an EMPTY source list as "everything allowed", so no
    source at all means can_publish=False, never an empty list."""
    grants = api.VideoGrants(room_join=True, room=room_name, can_subscribe=True, can_publish=bool(sources),
                             can_publish_sources=list(sources) or None, can_publish_data=can_data, can_update_own_metadata=False)
    return (api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
            .with_identity(identity).with_name(name).with_metadata(json.dumps({"role": role}))
            .with_attributes(attributes).with_grants(grants).with_ttl(timedelta(seconds=ttl_seconds)).to_jwt())


def verify_webhook(body: str, authorization: str | None) -> api.WebhookEvent:
    """Raises (ValueError / jwt errors) unless the body was signed by our LiveKit server."""
    if not configured() or not authorization:
        raise ValueError("unsigned webhook")
    return api.WebhookReceiver(api.TokenVerifier(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)).receive(body, authorization)


def _not_found(exc: Exception) -> bool:
    return getattr(exc, "status", None) == 404 or str(getattr(exc, "code", "")).lower() == "not_found"


def _permission(sources: list[str], can_data: bool) -> api.ParticipantPermission:
    return api.ParticipantPermission(can_subscribe=True, can_publish=bool(sources), can_publish_data=can_data,
                                     can_publish_sources=[_SOURCE[s] for s in sources], can_update_metadata=False)


class Gateway:
    """LiveKit server API (RoomService). Every method opens one short-lived client."""

    def _run(self, op: str, fn):
        if not configured():
            raise LiveKitUnavailable("not_configured")

        async def call():
            async with api.LiveKitAPI(api_url(), settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET,
                                      timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)) as lk:
                return await fn(lk.room)

        try:
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return asyncio.run(call())
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:  # called from inside an event loop
                return pool.submit(asyncio.run, call()).result()
        except LiveKitUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001 — network / server errors become one clear error
            if _not_found(exc):
                return None
            log.warning("LiveKit %s failed: %s", op, type(exc).__name__)
            raise LiveKitUnavailable(op) from exc

    def ensure_room(self, name: str, max_participants: int, metadata: dict) -> None:
        async def fn(room):
            await room.create_room(api.CreateRoomRequest(name=name, empty_timeout=EMPTY_TIMEOUT, departure_timeout=DEPARTURE_TIMEOUT,
                                                         max_participants=max_participants, metadata=json.dumps(metadata)))
            await room.update_room_metadata(api.UpdateRoomMetadataRequest(room=name, metadata=json.dumps(metadata)))
        self._run("create_room", fn)

    def set_room_metadata(self, name: str, metadata: dict) -> bool:
        async def fn(room):
            await room.update_room_metadata(api.UpdateRoomMetadataRequest(room=name, metadata=json.dumps(metadata)))
            return True
        return bool(self._run("update_room_metadata", fn))

    def delete_room(self, name: str) -> bool:
        async def fn(room):
            await room.delete_room(api.DeleteRoomRequest(room=name))
            return True
        return bool(self._run("delete_room", fn))

    def participants(self, name: str) -> list:
        async def fn(room):
            return list((await room.list_participants(api.ListParticipantsRequest(room=name))).participants)
        return self._run("list_participants", fn) or []

    def rooms(self) -> dict[str, int]:
        """Live LiveKit rooms: name -> participants (admin monitoring)."""
        async def fn(room):
            return {r.name: r.num_participants for r in (await room.list_rooms(api.ListRoomsRequest())).rooms}
        return self._run("list_rooms", fn) or {}

    def update_permission(self, name: str, identity: str, sources: list[str], can_data: bool) -> bool:
        async def fn(room):
            await room.update_participant(api.UpdateParticipantRequest(room=name, identity=identity, permission=_permission(sources, can_data)))
            return True
        return bool(self._run("update_participant", fn))

    def set_attributes(self, name: str, identity: str, attributes: dict[str, str]) -> bool:
        async def fn(room):
            await room.update_participant(api.UpdateParticipantRequest(room=name, identity=identity, attributes=attributes))
            return True
        return bool(self._run("update_participant", fn))

    def mute(self, name: str, identities: list[str], sources: tuple[str, ...] = (MICROPHONE,)) -> int:
        """Server-mute the given sources of these participants (they may unmute again unless the
        permission was taken away as well). Returns how many tracks were muted."""
        wanted = {_SOURCE[s] for s in sources}
        targets = set(identities)

        async def fn(room):
            muted = 0
            for p in (await room.list_participants(api.ListParticipantsRequest(room=name))).participants:
                if p.identity not in targets:
                    continue
                for t in p.tracks:
                    if t.source in wanted and not t.muted:
                        await room.mute_published_track(api.MuteRoomTrackRequest(room=name, identity=p.identity, track_sid=t.sid, muted=True))
                        muted += 1
            return muted
        return int(self._run("mute_published_track", fn) or 0)

    def remove(self, name: str, identity: str) -> bool:
        async def fn(room):
            await room.remove_participant(api.RoomParticipantIdentity(room=name, identity=identity))
            return True
        return bool(self._run("remove_participant", fn))

    def status(self) -> str:
        if not configured():
            return "unconfigured"
        try:
            self.rooms()
            return "available"
        except LiveKitUnavailable:
            return "unavailable"


gateway = Gateway()


def track_state(info) -> dict:
    """What a ParticipantInfo publishes, for the participant list (no SDP, no IPs)."""
    out = {"mic_on": False, "camera_on": False, "screen_sharing": False}
    for t in info.tracks:
        if t.muted:
            continue
        if t.source == api.TrackSource.MICROPHONE:
            out["mic_on"] = True
        elif t.source == api.TrackSource.CAMERA:
            out["camera_on"] = True
        elif t.source == api.TrackSource.SCREEN_SHARE:
            out["screen_sharing"] = True
    return out
