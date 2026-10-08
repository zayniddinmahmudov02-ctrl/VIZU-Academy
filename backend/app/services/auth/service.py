import re
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_user_token,
    hash_password,
    verify_password,
)

from app.models.user import User
from app.services.auth.identifier import (
    KIND_EMAIL,
    InvalidIdentifier,
    LoginIdentifier,
    is_reserved_email,
    parse_identifier,
    phone_placeholder_email,
)

from app.repositories.refresh_token import RefreshTokenRepository

from app.schemas.auth.user import (
    ProfileUpdateRequest,
    Token,
    UserRegister,
)


def _split_name(full_name: str | None) -> tuple[str | None, str | None]:
    parts = (full_name or "").split()
    if not parts:
        return None, None
    return parts[0][:100], (" ".join(parts[1:])[:100] or None)


def _unique_username(db: Session, base: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9_]", "_", base).strip("_")[:30] or "user"
    if len(base) < 3:
        base = f"{base}_user"
    candidate, suffix = base, 0
    while db.scalar(select(User.id).where(func.lower(User.username) == candidate.lower())) is not None:
        suffix += 1
        candidate = f"{base}_{suffix}"
    return candidate


def _find_by_identifier(db: Session, ident: LoginIdentifier) -> User | None:
    if ident.kind == KIND_EMAIL:
        return db.scalar(select(User).where(func.lower(User.email) == ident.value))
    return db.scalar(select(User).where(User.login_phone == ident.value))


def create_user(
    db: Session,
    data: UserRegister,
) -> User:
    """Self-registration with an e-mail address OR a phone number. The
    account is active and verified immediately — there is no confirmation
    step. One account per e-mail and per phone number (409 ACCOUNT_EXISTS);
    the unique constraints on users.email / users.login_phone back this up
    against concurrent requests."""

    try:
        ident = parse_identifier(data.login_identifier, strict=True)
    except InvalidIdentifier:
        raise HTTPException(status_code=422, detail="INVALID_IDENTIFIER")
    if ident.kind == KIND_EMAIL and is_reserved_email(ident.value):
        raise HTTPException(status_code=422, detail="INVALID_IDENTIFIER")

    if _find_by_identifier(db, ident) is not None:
        raise HTTPException(status_code=409, detail="ACCOUNT_EXISTS")

    if ident.kind == KIND_EMAIL:
        email, login_phone, phone_number = ident.value, None, None
        username_base = ident.value.split("@", 1)[0]
    else:
        email, login_phone, phone_number = phone_placeholder_email(ident.value), ident.value, ident.value
        username_base = f"u{ident.value.lstrip('+')}"
        if db.scalar(select(User.id).where(func.lower(User.email) == email)) is not None:
            raise HTTPException(status_code=409, detail="ACCOUNT_EXISTS")

    if data.username:
        if db.scalar(select(User).where(func.lower(User.username) == data.username.lower())):
            raise HTTPException(status_code=409, detail="Username already exists.")
        username = data.username
    else:
        username = _unique_username(db, username_base)

    first_name, last_name = _split_name(data.full_name)

    user = User(
        email=email,
        login_phone=login_phone,
        phone_number=phone_number,
        username=username,
        first_name=first_name,
        last_name=last_name,
        password_hash=hash_password(data.password),
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # a concurrent registration with the same e-mail / phone won the race
        db.rollback()
        raise HTTPException(status_code=409, detail="ACCOUNT_EXISTS")
    db.refresh(user)
    return user


def display_name(user: User) -> str:
    return (user.first_name or "").strip() or user.username


def get_user_by_identifier(db: Session, identifier: str) -> User | None:
    """E-mail (case-insensitive) or phone number (normalised) -> account."""
    try:
        ident = parse_identifier(identifier)
    except InvalidIdentifier:
        return None
    return _find_by_identifier(db, ident)


def authenticate_user(
    db: Session,
    identifier: str,
    password: str,
):
    """Login with e-mail OR phone number. E-mail lookup stays
    case-insensitive and whitespace-trimmed (stored case is untouched, so a
    mobile autocapitalised address still matches). Returns None for an
    unknown identifier or a wrong password — the caller cannot tell which."""

    user = get_user_by_identifier(db, identifier)

    if user is None:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user


def get_or_create_telegram_user(
    db: Session,
    telegram_user: dict,
) -> User:
    """Telegram Mini App login's identity resolution — called only after
    validate_telegram_init_data() has already verified the HMAC signature
    (see app/api/auth/router.py's POST /auth/telegram); `telegram_user` is
    the trusted, JSON-decoded `user` field from that verified payload,
    never the frontend's own unverified initDataUnsafe.

    A returning Telegram user is found by `telegram_id` alone — never by
    email/username, which are only ever synthetic placeholders on a
    Telegram-originated account (Telegram doesn't give out an email
    address), so two different logins here can never create a second,
    duplicate account for the same Telegram id. A brand-new account gets
    a random, never-typed password (hash_password over a generated
    token) — there is no password-based login path for a Telegram-only
    account, only this one."""

    telegram_id = telegram_user["id"]

    existing = db.scalar(
        select(User).where(User.telegram_id == telegram_id)
    )
    if existing is not None:
        return existing

    username_base = telegram_user.get("username") or f"tg_{telegram_id}"
    username = username_base
    suffix = 0
    while db.scalar(select(User).where(User.username == username)) is not None:
        suffix += 1
        username = f"{username_base}_{suffix}"

    user = User(
        email=f"telegram_{telegram_id}@telegram.local",
        username=username,
        password_hash=hash_password(secrets.token_urlsafe(32)),
        telegram_id=telegram_id,
        first_name=telegram_user.get("first_name"),
        last_name=telegram_user.get("last_name"),
        is_verified=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

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
    """Case-insensitive e-mail lookup (same comparison as login)."""

    return db.scalar(
        select(User).where(
            func.lower(User.email) == email.strip().lower(),
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
# Profile
# ==========================

def update_profile(
    db: Session,
    user: User,
    data: ProfileUpdateRequest,
) -> User:

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


def change_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> bool:
    """Returns False if the current password is wrong. On success, revokes
    every outstanding refresh token for this user — other sessions can no
    longer silently refresh with the old credential's trust; the access
    token they're still holding expires naturally within
    ACCESS_TOKEN_EXPIRE_MINUTES, same as every other standing-change in
    this codebase (ban/suspend re-checked per-request, not via a JWT
    blacklist)."""

    if not verify_password(current_password, user.password_hash):
        return False

    user.password_hash = hash_password(new_password)
    db.commit()

    RefreshTokenRepository(db).delete_all_for_user(str(user.id))

    return True


def update_preferred_language(
    db: Session,
    user: User,
    language: str,
) -> User:

    user.preferred_language = language
    db.commit()
    db.refresh(user)

    return user


def set_profile_image(
    db: Session,
    user: User,
    url: str,
) -> User:

    user.profile_image = url
    db.commit()
    db.refresh(user)

    return user


def remove_profile_image(
    db: Session,
    user: User,
) -> User:

    user.profile_image = None
    db.commit()
    db.refresh(user)

    return user