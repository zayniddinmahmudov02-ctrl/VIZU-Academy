"""Brute-force protection for password login and registration.

Database-backed (table auth_rate_limit_events), so the limits hold across
every server worker. The identifier and the IP are stored only as keyed
hashes (HMAC-SHA256 with SECRET_KEY) — enough to count, useless otherwise.

* Login: only FAILED attempts are recorded. While an identifier (or an IP)
  is over its limit, even a correct password is refused with 429 — so a
  password cannot be guessed by trying faster.
* Registration: every attempt per IP is counted (account-creation spam)."""

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_rate_limit_event import AuthRateLimitEvent

ACTION_LOGIN_FAILED = "login_failed"
ACTION_REGISTER = "register"

LOGIN_WINDOW = timedelta(minutes=15)
MAX_FAILED_LOGINS_PER_IDENTIFIER = 10
MAX_FAILED_LOGINS_PER_IP = 50
REGISTER_WINDOW = timedelta(hours=1)
MAX_REGISTRATIONS_PER_IP = 10
EVENT_RETENTION = timedelta(days=1)


class RateLimited(Exception):
    def __init__(self, retry_after: int):
        super().__init__("rate limited")
        self.retry_after = max(1, int(retry_after))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _key(kind: str, value: str | None) -> str | None:
    if not value:
        return None
    return hmac.new(settings.SECRET_KEY.encode(), f"{kind}:{value.strip().lower()}".encode(), hashlib.sha256).hexdigest()


def identifier_key(identifier: str) -> str | None:
    return _key("identifier", identifier)


def ip_key(ip: str | None) -> str | None:
    return _key("ip", ip)


def _count_since(db: Session, action: str, column, value: str, since: datetime) -> tuple[int, datetime | None]:
    count, oldest = db.execute(
        select(func.count(AuthRateLimitEvent.id), func.min(AuthRateLimitEvent.created_at)).where(
            AuthRateLimitEvent.action == action, column == value, AuthRateLimitEvent.created_at > since
        )
    ).one()
    return int(count or 0), oldest


def _check(db: Session, action: str, column, value: str | None, limit: int, window: timedelta) -> None:
    if value is None:
        return
    now = _now()
    count, oldest = _count_since(db, action, column, value, now - window)
    if count >= limit:
        retry = (oldest + window - now).total_seconds() if oldest else window.total_seconds()
        raise RateLimited(retry)


def _prune(db: Session) -> None:
    db.execute(delete(AuthRateLimitEvent).where(AuthRateLimitEvent.created_at < _now() - EVENT_RETENTION))


def check_login_allowed(db: Session, identifier: str, ip: str | None) -> None:
    _check(db, ACTION_LOGIN_FAILED, AuthRateLimitEvent.email_hash, identifier_key(identifier), MAX_FAILED_LOGINS_PER_IDENTIFIER, LOGIN_WINDOW)
    _check(db, ACTION_LOGIN_FAILED, AuthRateLimitEvent.ip_hash, ip_key(ip), MAX_FAILED_LOGINS_PER_IP, LOGIN_WINDOW)


def record_failed_login(db: Session, identifier: str, ip: str | None) -> None:
    _prune(db)
    db.add(AuthRateLimitEvent(action=ACTION_LOGIN_FAILED, email_hash=identifier_key(identifier), ip_hash=ip_key(ip)))
    db.commit()


def check_and_record_registration(db: Session, ip: str | None) -> None:
    _check(db, ACTION_REGISTER, AuthRateLimitEvent.ip_hash, ip_key(ip), MAX_REGISTRATIONS_PER_IP, REGISTER_WINDOW)
    db.add(AuthRateLimitEvent(action=ACTION_REGISTER, ip_hash=ip_key(ip)))
    db.commit()
