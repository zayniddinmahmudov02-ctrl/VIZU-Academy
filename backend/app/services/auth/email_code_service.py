"""One-time 6-digit email codes (registration verification + password reset)
and the database-backed rate limits around them.

Codes:
* generated with `secrets` (cryptographically secure), 10 minutes valid;
* stored only as HMAC-SHA256(SECRET_KEY, purpose:user_id:code) — bound to
  user AND purpose, so a registration code can never pass as a reset code;
* compared with hmac.compare_digest (constant time);
* one active code per (user, purpose): issuing a new one invalidates the
  previous one; a code is single-use; 5 wrong guesses invalidate it.

Rate limits (stored as keyed hashes of email/IP, shared by all workers):
* code e-mails: 60 s cooldown and max 5 per hour per address and purpose,
  plus max 20 per hour per IP;
* code checks: max 30 per 15 minutes per IP (on top of the 5 attempts per
  code), against distributed guessing.

Nothing here logs or returns a raw code.
"""

import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_rate_limit_event import AuthRateLimitEvent
from app.models.email_verification_code import ALL_PURPOSES, EmailVerificationCode
from app.models.user import User

CODE_LENGTH = 6
CODE_TTL = timedelta(minutes=10)
MAX_ATTEMPTS = 5
SEND_COOLDOWN = timedelta(seconds=60)
MAX_SENDS_PER_HOUR = 5
MAX_SENDS_PER_IP_PER_HOUR = 20
VERIFY_WINDOW = timedelta(minutes=15)
MAX_VERIFIES_PER_IP = 30
EVENT_RETENTION = timedelta(days=1)

ACTION_VERIFY = "verify_code"
CODE_RE = re.compile(r"^\d{6}$")


class CodeCheck(str, Enum):
    OK = "OK"
    INVALID = "CODE_INVALID"
    EXPIRED = "CODE_EXPIRED"
    TOO_MANY_ATTEMPTS = "TOO_MANY_ATTEMPTS"


@dataclass
class RateLimited(Exception):
    retry_after: int

    def __str__(self) -> str:
        return "RATE_LIMITED"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hmac(value: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def email_key(email: str) -> str:
    return _hmac(f"email:{normalize_email(email)}")


def ip_key(ip: str | None) -> str | None:
    return _hmac(f"ip:{ip}") if ip else None


def hash_code(user_id, purpose: str, code: str) -> str:
    return _hmac(f"code:{purpose}:{user_id}:{code}")


def generate_code() -> str:
    return f"{secrets.randbelow(10**CODE_LENGTH):0{CODE_LENGTH}d}"


def send_action(purpose: str) -> str:
    return f"send:{purpose}"


# ============================================================
# Rate limiting
# ============================================================


def _record(db: Session, action: str, email: str | None, ip: str | None) -> None:
    db.add(AuthRateLimitEvent(action=action, email_hash=email_key(email) if email else None, ip_hash=ip_key(ip)))


def check_and_record_send(db: Session, purpose: str, email: str, ip: str | None) -> None:
    """Raises RateLimited, otherwise records the request. Counted for EVERY
    request (existing account or not), so the limit itself reveals nothing
    about whether an address is registered."""
    now = _now()
    action = send_action(purpose)
    db.execute(delete(AuthRateLimitEvent).where(AuthRateLimitEvent.created_at < now - EVENT_RETENTION))
    recent = list(
        db.scalars(
            select(AuthRateLimitEvent.created_at)
            .where(
                AuthRateLimitEvent.action == action,
                AuthRateLimitEvent.email_hash == email_key(email),
                AuthRateLimitEvent.created_at > now - timedelta(hours=1),
            )
            .order_by(AuthRateLimitEvent.created_at.desc())
        )
    )
    if recent and recent[0] > now - SEND_COOLDOWN:
        raise RateLimited(int((recent[0] + SEND_COOLDOWN - now).total_seconds()) + 1)
    if len(recent) >= MAX_SENDS_PER_HOUR:
        raise RateLimited(int((recent[-1] + timedelta(hours=1) - now).total_seconds()) + 1)
    if ip:
        per_ip = db.scalar(
            select(func.count())
            .select_from(AuthRateLimitEvent)
            .where(
                AuthRateLimitEvent.action == action,
                AuthRateLimitEvent.ip_hash == ip_key(ip),
                AuthRateLimitEvent.created_at > now - timedelta(hours=1),
            )
        )
        if per_ip >= MAX_SENDS_PER_IP_PER_HOUR:
            raise RateLimited(3600)
    _record(db, action, email, ip)
    db.commit()


def check_and_record_verify(db: Session, ip: str | None) -> None:
    if not ip:
        return
    now = _now()
    count = db.scalar(
        select(func.count())
        .select_from(AuthRateLimitEvent)
        .where(
            AuthRateLimitEvent.action == ACTION_VERIFY,
            AuthRateLimitEvent.ip_hash == ip_key(ip),
            AuthRateLimitEvent.created_at > now - VERIFY_WINDOW,
        )
    )
    if count >= MAX_VERIFIES_PER_IP:
        raise RateLimited(int(VERIFY_WINDOW.total_seconds()))
    _record(db, ACTION_VERIFY, None, ip)
    db.commit()


# ============================================================
# Codes
# ============================================================


def _active(db: Session, user: User, purpose: str, lock: bool = False) -> EmailVerificationCode | None:
    query = select(EmailVerificationCode).where(
        EmailVerificationCode.user_id == user.id,
        EmailVerificationCode.purpose == purpose,
        EmailVerificationCode.used_at.is_(None),
        EmailVerificationCode.invalidated_at.is_(None),
    )
    if lock:
        query = query.with_for_update()
    return db.scalar(query)


def invalidate_active(db: Session, user: User, purpose: str) -> None:
    db.execute(
        update(EmailVerificationCode)
        .where(
            EmailVerificationCode.user_id == user.id,
            EmailVerificationCode.purpose == purpose,
            EmailVerificationCode.used_at.is_(None),
            EmailVerificationCode.invalidated_at.is_(None),
        )
        .values(invalidated_at=_now())
    )


def issue_code(db: Session, user: User, purpose: str) -> str:
    """Invalidates the previous active code and stores a fresh one; returns
    the raw code ONLY so the caller can e-mail it."""
    if purpose not in ALL_PURPOSES:
        raise ValueError("unknown purpose")
    for _ in range(2):  # a concurrent issue may win the unique index once
        code = generate_code()
        invalidate_active(db, user, purpose)
        db.add(
            EmailVerificationCode(
                user_id=user.id,
                email=normalize_email(user.email),
                purpose=purpose,
                code_hash=hash_code(user.id, purpose, code),
                expires_at=_now() + CODE_TTL,
            )
        )
        try:
            db.commit()
            return code
        except IntegrityError:
            db.rollback()
    raise RuntimeError("Could not issue a verification code.")


def check_code(db: Session, user: User | None, purpose: str, code: str, consume: bool) -> CodeCheck:
    """Verifies `code` for (user, purpose). Wrong guesses count against the
    code; `consume=True` marks a correct code as used (single use)."""
    if user is None:
        return CodeCheck.INVALID
    active = _active(db, user, purpose, lock=True)
    if active is None:
        latest = db.scalar(
            select(EmailVerificationCode)
            .where(EmailVerificationCode.user_id == user.id, EmailVerificationCode.purpose == purpose)
            .order_by(EmailVerificationCode.created_at.desc())
            .limit(1)
        )
        db.rollback()
        if latest is not None and latest.used_at is None and latest.attempts >= MAX_ATTEMPTS:
            return CodeCheck.TOO_MANY_ATTEMPTS
        return CodeCheck.INVALID
    now = _now()
    if active.expires_at <= now:
        active.invalidated_at = now
        db.commit()
        return CodeCheck.EXPIRED
    candidate = (code or "").strip()
    valid_format = bool(CODE_RE.fullmatch(candidate))
    if not valid_format or not hmac.compare_digest(active.code_hash, hash_code(user.id, purpose, candidate)):
        active.attempts += 1
        if active.attempts >= MAX_ATTEMPTS:
            active.invalidated_at = now
            db.commit()
            return CodeCheck.TOO_MANY_ATTEMPTS
        db.commit()
        return CodeCheck.INVALID
    if consume:
        active.used_at = now
        db.commit()
    else:
        db.rollback()  # release the row lock; nothing changed
    return CodeCheck.OK
