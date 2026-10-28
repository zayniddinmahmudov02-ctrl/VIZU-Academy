"""Join codes: 8 characters from a 31-letter alphabet without look-alikes
(31^8 ≈ 8.5·10^11), shown as XXXX-XXXX. Only an HMAC of the code is stored,
so the plain code exists exactly once — in the response that generated it.
Wrong guesses are rate limited per user and per IP (database-backed, shared
by all workers — the same table as the login limiter)."""

import hashlib
import hmac
import secrets
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_rate_limit_event import AuthRateLimitEvent
from app.models.study_group import CODE_ACTIVE, CODE_PAUSED, CODE_REVOKED, StudyGroup, StudyGroupJoinCode
from app.services.auth.rate_limit import RateLimited, _check, ip_key
from app.services.study_groups.access import now

# no I, L, O, 0, 1 — easy to read aloud and to type
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8
ACTION_JOIN_FAILED = "group_join_failed"
JOIN_WINDOW = timedelta(minutes=15)
MAX_FAILED_JOINS_PER_USER = 10
MAX_FAILED_JOINS_PER_IP = 30


def normalize(code: str) -> str:
    return "".join(ch for ch in (code or "").upper() if ch.isalnum())


def code_hash(code: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), f"group-join:{normalize(code)}".encode(), hashlib.sha256).hexdigest()


def generate() -> str:
    raw = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
    return f"{raw[:4]}-{raw[4:]}"


def user_key(user_id) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), f"user:{user_id}".encode(), hashlib.sha256).hexdigest()


def current(db: Session, group_id) -> StudyGroupJoinCode | None:
    return db.scalar(select(StudyGroupJoinCode).where(StudyGroupJoinCode.group_id == group_id,
                                                      StudyGroupJoinCode.status != CODE_REVOKED)
                     .order_by(StudyGroupJoinCode.created_at.desc()).limit(1))


def revoke_all(db: Session, group_id) -> None:
    db.execute(update(StudyGroupJoinCode).where(StudyGroupJoinCode.group_id == group_id, StudyGroupJoinCode.status != CODE_REVOKED)
               .values(status=CODE_REVOKED, revoked_at=now()))


def create(db: Session, group: StudyGroup, actor_id, expires_at=None, max_uses: int | None = None) -> str:
    """Revokes the previous code and returns the new plain code (shown once)."""
    revoke_all(db, group.id)
    for _ in range(5):
        plain = generate()
        h = code_hash(plain)
        if db.scalar(select(StudyGroupJoinCode.id).where(StudyGroupJoinCode.code_hash == h)) is None:
            db.add(StudyGroupJoinCode(group_id=group.id, code_hash=h, status=CODE_ACTIVE, expires_at=expires_at,
                                      max_uses=max_uses, created_by=actor_id))
            return plain
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not create a code, try again")


def describe(code: StudyGroupJoinCode | None) -> dict | None:
    if code is None:
        return None
    expired = code.expires_at is not None and code.expires_at <= now()
    used_up = code.max_uses is not None and code.use_count >= code.max_uses
    return {"status": code.status, "expires_at": code.expires_at, "max_uses": code.max_uses, "use_count": code.use_count,
            "created_at": code.created_at, "usable": code.status == CODE_ACTIVE and not expired and not used_up,
            "expired": expired, "used_up": used_up}


def check_rate(db: Session, user_id, ip: str | None) -> None:
    try:
        _check(db, ACTION_JOIN_FAILED, AuthRateLimitEvent.email_hash, user_key(user_id), MAX_FAILED_JOINS_PER_USER, JOIN_WINDOW)
        _check(db, ACTION_JOIN_FAILED, AuthRateLimitEvent.ip_hash, ip_key(ip), MAX_FAILED_JOINS_PER_IP, JOIN_WINDOW)
    except RateLimited as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="too_many_attempts",
                            headers={"Retry-After": str(exc.retry_after)})


def record_failure(db: Session, user_id, ip: str | None) -> None:
    db.add(AuthRateLimitEvent(action=ACTION_JOIN_FAILED, email_hash=user_key(user_id), ip_hash=ip_key(ip)))
    db.commit()


def lookup(db: Session, code: str) -> StudyGroupJoinCode | None:
    if len(normalize(code)) != CODE_LENGTH:
        return None
    return db.scalar(select(StudyGroupJoinCode).where(StudyGroupJoinCode.code_hash == code_hash(code)))


def set_state(code: StudyGroupJoinCode, paused: bool | None = None, expires_at=..., max_uses=...) -> None:
    if paused is not None and code.status != CODE_REVOKED:
        code.status = CODE_PAUSED if paused else CODE_ACTIVE
    if expires_at is not ...:
        code.expires_at = expires_at
    if max_uses is not ...:
        code.max_uses = max_uses
