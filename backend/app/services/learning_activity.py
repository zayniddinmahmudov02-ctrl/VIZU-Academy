"""Lernserie: server-confirmed learning time and daily streak.

Only events the server can verify are credited — never a duration the
browser reports:

* VIDEO — the stored playback position really advanced. Credit = the
  advance, at most the server-measured time since the previous report and at
  most VIDEO_MAX_CREDIT_PER_REPORT. Opening a lesson, a paused player or a
  repeated report credits nothing; seeking cannot add more than real time.
* SKILL_ATTEMPT — a submitted Lesen / Hören / Übungen attempt: server
  started_at -> submitted_at, capped at ATTEMPT_MAX_CREDIT (an attempt left
  open for hours is not hours of learning). Credited once per attempt.

Rows are bucketed per UTC hour; local days (streak, week) are derived at
read time in the student's time zone, so the same data serves every zone.
Idempotency: unique (user, source, source_ref, bucket_start) — an attempt is
inserted once (ON CONFLICT DO NOTHING), video seconds accumulate atomically
(ON CONFLICT DO UPDATE seconds = seconds + new).
"""

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.learning_activity import SOURCE_SKILL_ATTEMPT, SOURCE_VIDEO, LearningActivity

VIDEO_MAX_CREDIT_PER_REPORT = 120  # seconds — the player reports every few seconds while playing
ATTEMPT_MAX_CREDIT = 20 * 60
DEFAULT_TZ = "Asia/Tashkent"
WEEK_DAYS = 7


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _bucket(dt: datetime) -> datetime:
    return _aware(dt).astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def _credit(db: Session, user_id, source: str, source_ref: str, seconds: int, at: datetime, lesson_id=None, *, accumulate: bool) -> int:
    seconds = int(seconds)
    if seconds <= 0:
        return 0
    at = _aware(at)
    stmt = insert(LearningActivity).values(
        id=uuid4(), user_id=user_id, source=source, source_ref=str(source_ref)[:64], lesson_id=lesson_id,
        bucket_start=_bucket(at), seconds=seconds, last_event_at=at, created_at=at, updated_at=at,
    )
    if accumulate:
        stmt = stmt.on_conflict_do_update(
            constraint="uq_learning_activity_bucket",
            set_={"seconds": LearningActivity.seconds + stmt.excluded.seconds, "last_event_at": stmt.excluded.last_event_at,
                  "updated_at": stmt.excluded.updated_at},
        )
    else:
        stmt = stmt.on_conflict_do_nothing(constraint="uq_learning_activity_bucket")
    db.execute(stmt)
    return seconds


def video_credit(old_position: int | None, new_position: int, last_report_at: datetime | None, now: datetime) -> int:
    """Seconds to credit for one video progress report (pure, testable)."""
    if old_position is None or last_report_at is None:
        return 0  # first report: nothing to compare with
    advance = int(new_position) - int(old_position)
    elapsed = int((_aware(now) - _aware(last_report_at)).total_seconds())
    if advance <= 0 or elapsed <= 0:
        return 0
    return min(advance, elapsed, VIDEO_MAX_CREDIT_PER_REPORT)


def credit_video(db: Session, user_id, video_id, lesson_id, old_position: int | None, new_position: int,
                 last_report_at: datetime | None, now: datetime | None = None) -> int:
    now = now or _now()
    seconds = video_credit(old_position, new_position, last_report_at, now)
    return _credit(db, user_id, SOURCE_VIDEO, str(video_id), seconds, now, lesson_id, accumulate=True)


def attempt_credit(duration_seconds: int | None) -> int:
    return max(0, min(int(duration_seconds or 0), ATTEMPT_MAX_CREDIT))


def credit_attempt(db: Session, user_id, attempt_id, lesson_id, duration_seconds: int | None, submitted_at: datetime) -> int:
    return _credit(db, user_id, SOURCE_SKILL_ATTEMPT, str(attempt_id), attempt_credit(duration_seconds), submitted_at, lesson_id,
                   accumulate=False)


# ============================================================
# Read: the student's Lernserie
# ============================================================


def resolve_tz(name: str | None):
    """The student's IANA time zone (from the browser); unknown -> Tashkent."""
    try:
        return ZoneInfo(name) if name and len(name) <= 64 else ZoneInfo(DEFAULT_TZ)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo(DEFAULT_TZ)


def streak_days(active_days: set[date], today: date) -> int:
    """Consecutive active days ending today — or yesterday while today has
    no activity yet (the series is only broken once a whole day is missed)."""
    day = today if today in active_days else today - timedelta(days=1)
    count = 0
    while day in active_days:
        count += 1
        day -= timedelta(days=1)
    return count


def summary(db: Session, user_id, tz_name: str | None = None, now: datetime | None = None) -> dict:
    tz = resolve_tz(tz_name)
    now = _aware(now or _now())
    rows = db.execute(
        select(LearningActivity.bucket_start, func.sum(LearningActivity.seconds), func.max(LearningActivity.last_event_at))
        .where(LearningActivity.user_id == user_id, LearningActivity.seconds > 0)
        .group_by(LearningActivity.bucket_start)
    ).all()
    per_day: dict[date, int] = {}
    last = None
    for bucket, seconds, last_event in rows:
        day = _aware(bucket).astimezone(tz).date()
        per_day[day] = per_day.get(day, 0) + int(seconds or 0)
        if last_event is not None and (last is None or _aware(last_event) > last):
            last = _aware(last_event)
    today = now.astimezone(tz).date()
    week = [{"date": (today - timedelta(days=i)).isoformat(), "seconds": per_day.get(today - timedelta(days=i), 0)}
            for i in range(WEEK_DAYS - 1, -1, -1)]
    return {
        "timezone": str(tz),
        "streak_days": streak_days(set(per_day), today),
        "total_seconds": sum(per_day.values()),
        "last_activity_at": last,
        "active_days_week": sum(1 for d in week if d["seconds"] > 0),
        "week_seconds": sum(d["seconds"] for d in week),
        "week": week,
    }
