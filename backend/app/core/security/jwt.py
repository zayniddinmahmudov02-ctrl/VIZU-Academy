from datetime import (
    UTC,
    datetime,
    timedelta,
)

from jose import jwt

from app.core.config import settings

VIDEO_STREAM_PURPOSE = "video_stream"


def create_access_token(
    data: dict,
    expires_minutes: int | None = None,
) -> str:
    """Low-level primitive: stamps iat/exp onto an arbitrary claims dict and
    signs it. Prefer create_user_token() for anything tied to a User —
    this exists for the rare case (e.g. impersonation) that needs extra
    claims layered on top of the standard user claims.
    """

    payload = data.copy()

    now = datetime.now(UTC)

    payload["iat"] = now
    payload["exp"] = now + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_user_token(
    user,
    expires_minutes: int | None = None,
    extra_claims: dict | None = None,
) -> str:
    """The single source of truth for what a user's JWT looks like.

    Every endpoint that issues a token for a User (login, impersonation,
    anything added later) must go through this function so the payload
    shape — and therefore what get_current_user() can safely rely on — is
    identical everywhere.
    """

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    }

    if extra_claims:
        payload.update(extra_claims)

    return create_access_token(payload, expires_minutes=expires_minutes)


def decode_access_token(token: str) -> dict:
    """Decodes and verifies a token, or raises.

    Callers MUST handle jose.JWTError (invalid signature / malformed) and
    its subclass jose.ExpiredSignatureError (expired) — this function does
    not swallow failures into an empty dict, because a caller checking
    `payload["sub"]` on an empty dict is exactly how this class of bug
    (KeyError -> unhandled 500) happens.
    """

    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[
            settings.ALGORITHM,
        ],
    )


def create_video_stream_token(video_id: str, user_id: str | None = None) -> str:
    """A short-lived, single-video-scoped credential embedded in the
    playback URL itself. Native <video> elements can't send an
    Authorization header, so the stream endpoint uses this signed token
    to identify the requester and rechecks their current course access."""

    payload = {
        "sub": str(video_id),
        "purpose": VIDEO_STREAM_PURPOSE,
    }
    if user_id is not None:
        payload["user_id"] = str(user_id)

    return create_access_token(
        payload,
        expires_minutes=settings.VIDEO_STREAM_TOKEN_EXPIRE_MINUTES,
    )


def decode_video_stream_token(token: str) -> str:
    """Returns the authorized video_id, or raises jose.JWTError /
    ExpiredSignatureError (invalid/expired) or ValueError (well-formed
    token, wrong purpose — e.g. a login access token reused here)."""

    payload = decode_access_token(token)

    if payload.get("purpose") != VIDEO_STREAM_PURPOSE:
        raise ValueError("Not a video-stream token")

    return payload["sub"]


def decode_video_stream_claims(token: str) -> tuple[str, str]:
    """Decode a user-scoped stream grant so access can be rechecked per request."""
    payload = decode_access_token(token)
    if payload.get("purpose") != VIDEO_STREAM_PURPOSE:
        raise ValueError("Not a video-stream token")
    video_id, user_id = payload.get("sub"), payload.get("user_id")
    if not isinstance(video_id, str) or not isinstance(user_id, str):
        raise ValueError("Stream token is not scoped to a user")
    return video_id, user_id


LMS_RESOURCE_PURPOSE = "lms_resource"


def create_resource_token(resource_id: str, user_id: str) -> str:
    """Same idea as create_video_stream_token for VIZU LMS resource files
    (<audio>, PDF viewer, <img> can't send a Bearer header): issued only by
    GET /lms/lessons/{id} after the lesson access check, scoped to one
    resource. Owner and current access are rechecked when bytes are requested."""

    return create_access_token(
        {"sub": str(resource_id), "purpose": LMS_RESOURCE_PURPOSE, "user_id": str(user_id)},
        expires_minutes=settings.VIDEO_STREAM_TOKEN_EXPIRE_MINUTES,
    )


def decode_resource_token(token: str) -> str:
    payload = decode_access_token(token)

    if payload.get("purpose") != LMS_RESOURCE_PURPOSE:
        raise ValueError("Not an LMS resource token")

    return payload["sub"]


def decode_resource_token_claims(token: str) -> tuple[str, str]:
    payload = decode_access_token(token)
    if payload.get("purpose") != LMS_RESOURCE_PURPOSE:
        raise ValueError("Not an LMS resource token")
    resource_id, user_id = payload.get("sub"), payload.get("user_id")
    if not isinstance(resource_id, str) or not isinstance(user_id, str):
        raise ValueError("Resource token is not scoped to a user")
    return resource_id, user_id


ADMIN_VIDEO_PREVIEW_PURPOSE = "admin_video_preview"


def create_admin_video_preview_token(video_id: str) -> str:
    """Admin player in Media Management: like create_video_stream_token, but
    also for drafts — so it has its own purpose and is issued only by the
    admin-authenticated preview endpoint; a student stream token never opens
    a draft."""

    return create_access_token(
        {"sub": str(video_id), "purpose": ADMIN_VIDEO_PREVIEW_PURPOSE},
        expires_minutes=settings.VIDEO_STREAM_TOKEN_EXPIRE_MINUTES,
    )


def decode_admin_video_preview_token(token: str) -> str:
    payload = decode_access_token(token)

    if payload.get("purpose") != ADMIN_VIDEO_PREVIEW_PURPOSE:
        raise ValueError("Not an admin video preview token")

    return payload["sub"]
