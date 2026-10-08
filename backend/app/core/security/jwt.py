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


def create_video_stream_token(video_id: str) -> str:
    """A short-lived, single-video-scoped credential embedded in the
    playback URL itself. Native <video> elements can't send an
    Authorization header, so the usual Bearer-token check can't gate
    GET /videos/{id}/stream — this token is issued once, at the moment
    VideoService.get_playable_video() already confirmed the requesting
    user has real access (free preview, Premium, or enrollment), and the
    stream endpoint trusts it exactly like an S3/CloudFront presigned URL:
    the signature is the authorization, valid until it expires."""

    payload = {
        "sub": str(video_id),
        "purpose": VIDEO_STREAM_PURPOSE,
    }

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
