from datetime import (
    UTC,
    datetime,
    timedelta,
)

from jose import jwt

from app.core.config import settings


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
