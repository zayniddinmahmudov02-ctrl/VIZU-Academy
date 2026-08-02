import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from jose import JWTError

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging.logger import logger
from app.core.security import (
    create_password_reset_token,
    create_user_token,
    decode_password_reset_token,
    hash_password,
    password_hash_fingerprint,
    verify_password,
)

from app.models.user import User

from app.repositories.refresh_token import RefreshTokenRepository

from app.schemas.auth.user import (
    Token,
    UserRegister,
)


def create_user(
    db: Session,
    data: UserRegister,
) -> User:

    existing_email = db.scalar(
        select(User).where(
            User.email == data.email,
        )
    )

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email already exists.",
        )

    existing_username = db.scalar(
        select(User).where(
            User.username == data.username,
        )
    )

    if existing_username:
        raise HTTPException(
            status_code=409,
            detail="Username already exists.",
        )

    user = User(
        email=data.email,
        username=data.username,
        password_hash=hash_password(
            data.password,
        ),
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
):

    user = db.scalar(
        select(User).where(
            User.email == email,
        )
    )

    if user is None:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user


def get_user_by_id(
    db: Session,
    user_id: str,
):

    return db.get(
        User,
        UUID(user_id),
    )


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:

    return db.scalar(
        select(User).where(
            User.email == email,
        )
    )


# ==========================
# Refresh tokens
# ==========================

def issue_refresh_token(
    db: Session,
    user: User,
) -> str:
    """Generates a new opaque refresh token, persists it, and returns the
    raw value to hand back to the client. Storing the raw token (not a
    hash) matches the existing `refresh_tokens` table shape — see
    RefreshToken model."""

    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )

    RefreshTokenRepository(db).issue(
        user_id=str(user.id),
        token=token,
        expires_at=expires_at,
    )

    return token


def issue_token_pair(
    db: Session,
    user: User,
) -> Token:
    return Token(
        access_token=create_user_token(user),
        refresh_token=issue_refresh_token(db, user),
        token_type="bearer",
    )


def refresh_access_token(
    db: Session,
    refresh_token: str,
) -> Token | None:
    """Validates and rotates a refresh token. Returns None (never raises)
    for any invalid/expired/unknown token — the caller turns that into a
    401, same as every other auth failure mode in this module."""

    repository = RefreshTokenRepository(db)
    stored = repository.get_by_token(refresh_token)

    if stored is None:
        return None

    if stored.expires_at < datetime.now(UTC).replace(tzinfo=None):
        repository.delete(stored)
        return None

    user = get_user_by_id(db, str(stored.user_id))

    if user is None:
        repository.delete(stored)
        return None

    # Rotate: the old token is single-use — deleting it here means a
    # stolen-and-replayed refresh token stops working the moment the
    # legitimate client refreshes first.
    repository.delete(stored)

    return issue_token_pair(db, user)


def revoke_refresh_token(
    db: Session,
    refresh_token: str,
) -> None:
    """Logout. Deleting an unknown token is a no-op, not an error —
    logout should always succeed from the client's point of view."""

    repository = RefreshTokenRepository(db)
    stored = repository.get_by_token(refresh_token)

    if stored is not None:
        repository.delete(stored)


# ==========================
# Password reset
# ==========================

def request_password_reset(
    db: Session,
    email: str,
) -> None:
    """Never reveals whether the email exists — the router always returns
    the same generic message regardless of what happens in here. With no
    email-sending infrastructure in this codebase, the reset link is
    logged server-side instead; wiring an actual mail provider is the one
    piece of real infrastructure this still needs before it's usable in
    production."""

    user = get_user_by_email(db, email)

    if user is None:
        return

    token = create_password_reset_token(user)
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    logger.info(
        "Password reset requested for user_id=%s email=%s — link: %s",
        user.id,
        user.email,
        reset_link,
    )


def reset_password(
    db: Session,
    token: str,
    new_password: str,
) -> bool:
    """Returns False for any invalid/expired/already-used token, True on
    success. Never raises for a bad token — only for genuinely
    unexpected failures."""

    try:
        payload = decode_password_reset_token(token)
    except (JWTError, ValueError):
        return False

    user_id = payload.get("sub")

    if not user_id:
        return False

    try:
        user = get_user_by_id(db, user_id)
    except (ValueError, TypeError):
        return False

    if user is None:
        return False

    if payload.get("pwd_fp") != password_hash_fingerprint(user.password_hash):
        # Password already changed since this token was issued — either
        # it was already redeemed, or the account changed some other way.
        return False

    user.password_hash = hash_password(new_password)
    db.commit()

    return True