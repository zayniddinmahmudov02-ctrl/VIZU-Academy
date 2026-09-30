"""VIZU-Mock admin dashboard — dashboard stats, activity/level/competency
analytics, paginated attempts (Recent Tests / Results), and Hören audio
CRUD, all read from the existing vizu_mock_attempts/vizu_mock_tasks data
(no new attempt-related schema needed) plus the new vizu_mock_audios
table. Every number here is a real aggregate SQL query; a metric that the
current data model genuinely cannot support (e.g. per-skill timing, since
only one overall started_at/completed_at pair is tracked per attempt) is
simply not exposed here, rather than being estimated or faked."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.user import User
from app.models.vizu_mock_attempt import STATUS_COMPLETED, STATUS_IN_PROGRESS, VizuMockAttempt
from app.models.vizu_mock_audio import VizuMockAudio
from app.models.vizu_mock_content import CEFR_LEVELS
from app.schemas.vizu_mock import VizuMockAudioCreate, VizuMockAudioUpdate


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _level_expr():
    # Prefers overall_level (cross-skill result) once later phases start
    # setting it; falls back to lesen_level, the only real per-skill
    # result today, so this stays correct without a code change once
    # Hören/Schreiben/Sprechen are wired up.
    return func.coalesce(VizuMockAttempt.overall_level, VizuMockAttempt.lesen_level)


def _average_duration_minutes(db: Session, since: datetime | None = None) -> float | None:
    query = db.query(
        func.avg(func.extract("epoch", VizuMockAttempt.completed_at - VizuMockAttempt.started_at))
    ).filter(VizuMockAttempt.status == STATUS_COMPLETED, VizuMockAttempt.completed_at.isnot(None))
    if since is not None:
        query = query.filter(VizuMockAttempt.started_at >= since)
    seconds = query.scalar()
    return round(float(seconds) / 60, 1) if seconds is not None else None


def _most_common_level(db: Session):
    level_expr = _level_expr()
    rows = (
        db.query(level_expr.label("level"), func.count(VizuMockAttempt.id).label("cnt"))
        .filter(level_expr.isnot(None))
        .group_by(level_expr)
        .order_by(func.count(VizuMockAttempt.id).desc())
        .all()
    )
    return rows[0].level if rows else None


# ============================================================
# Overview — stat cards
# ============================================================


def get_overview(db: Session) -> dict:
    now = _now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = today_start.replace(day=1)

    total_attempts = db.query(func.count(VizuMockAttempt.id)).scalar() or 0
    today_attempts = (
        db.query(func.count(VizuMockAttempt.id)).filter(VizuMockAttempt.started_at >= today_start).scalar() or 0
    )
    week_attempts = (
        db.query(func.count(VizuMockAttempt.id)).filter(VizuMockAttempt.started_at >= week_start).scalar() or 0
    )
    month_attempts = (
        db.query(func.count(VizuMockAttempt.id)).filter(VizuMockAttempt.started_at >= month_start).scalar() or 0
    )
    completed_attempts = (
        db.query(func.count(VizuMockAttempt.id)).filter(VizuMockAttempt.status == STATUS_COMPLETED).scalar() or 0
    )
    in_progress_attempts = (
        db.query(func.count(VizuMockAttempt.id)).filter(VizuMockAttempt.status == STATUS_IN_PROGRESS).scalar() or 0
    )

    avg_score = (
        db.query(func.avg(VizuMockAttempt.lesen_score)).filter(VizuMockAttempt.lesen_score.isnot(None)).scalar()
    )
    # Lesen is now scored out of 100 (20 questions x 5 points, see
    # scripts/seed_vizu_mock_lesen.py) — this stat is Lesen-only (see the
    # module's "based on available modules today" note elsewhere), so the
    # percentage is just the raw average.
    average_score_percent = round(float(avg_score), 1) if avg_score is not None else None

    return {
        "total_attempts": total_attempts,
        "today_attempts": today_attempts,
        "week_attempts": week_attempts,
        "month_attempts": month_attempts,
        "completed_attempts": completed_attempts,
        "in_progress_attempts": in_progress_attempts,
        "average_score_percent": average_score_percent,
        "most_common_level": _most_common_level(db),
    }


# ============================================================
# Test Faolligi — activity trend
# ============================================================


def get_activity(db: Session, days: int) -> dict:
    now = _now()
    range_start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)

    started_rows = (
        db.query(
            func.date_trunc("day", VizuMockAttempt.started_at).label("day"),
            func.count(VizuMockAttempt.id).label("cnt"),
        )
        .filter(VizuMockAttempt.started_at >= range_start)
        .group_by("day")
        .all()
    )
    completed_rows = (
        db.query(
            func.date_trunc("day", VizuMockAttempt.completed_at).label("day"),
            func.count(VizuMockAttempt.id).label("cnt"),
        )
        .filter(VizuMockAttempt.completed_at.isnot(None), VizuMockAttempt.completed_at >= range_start)
        .group_by("day")
        .all()
    )

    started_by_day = {row.day.date(): row.cnt for row in started_rows}
    completed_by_day = {row.day.date(): row.cnt for row in completed_rows}

    points = []
    for i in range(days):
        day = (range_start + timedelta(days=i)).date()
        points.append(
            {
                "label": day.strftime("%d.%m"),
                "started": started_by_day.get(day, 0),
                "completed": completed_by_day.get(day, 0),
            }
        )

    total_started = sum(p["started"] for p in points)
    total_completed = sum(p["completed"] for p in points)
    completion_rate_percent = round(total_completed / total_started * 100, 1) if total_started > 0 else None

    return {
        "days": days,
        "points": points,
        "completion_rate_percent": completion_rate_percent,
        "average_duration_minutes": _average_duration_minutes(db, since=range_start),
    }


# ============================================================
# Aniqlangan darajalar + Kompetenz bo'yicha natijalar
# ============================================================


def _competency_stat(db: Session, skill: str, score_col, level_col, max_points: int | None) -> dict:
    if score_col is not None:
        avg_score = db.query(func.avg(score_col)).filter(score_col.isnot(None)).scalar()
        average_percent = round(float(avg_score) / max_points * 100, 1) if avg_score is not None else None
        submitted_count = db.query(func.count(VizuMockAttempt.id)).filter(score_col.isnot(None)).scalar() or 0
    else:
        # Hören/Schreiben/Sprechen have no score column yet — no grading
        # exists for them, so average_percent stays None rather than a
        # fabricated 0, and "submitted" is approximated by "has a level".
        average_percent = None
        submitted_count = db.query(func.count(VizuMockAttempt.id)).filter(level_col.isnot(None)).scalar() or 0

    level_rows = (
        db.query(level_col.label("level"), func.count(VizuMockAttempt.id).label("cnt"))
        .filter(level_col.isnot(None))
        .group_by(level_col)
        .order_by(func.count(VizuMockAttempt.id).desc())
        .all()
    )

    return {
        "skill": skill,
        "average_percent": average_percent,
        "submitted_count": submitted_count,
        "most_common_level": level_rows[0].level if level_rows else None,
    }


def get_level_analytics(db: Session) -> dict:
    level_expr = _level_expr()
    rows = (
        db.query(level_expr.label("level"), func.count(VizuMockAttempt.id).label("cnt"))
        .filter(level_expr.isnot(None))
        .group_by(level_expr)
        .all()
    )
    counts = {row.level: row.cnt for row in rows}
    total_leveled = sum(counts.values())

    level_distribution = [
        {
            "level": level,
            "count": counts.get(level, 0),
            "percent": round(counts.get(level, 0) / total_leveled * 100, 1) if total_leveled > 0 else 0.0,
        }
        for level in CEFR_LEVELS
    ]

    competencies = [
        _competency_stat(db, "LESEN", VizuMockAttempt.lesen_score, VizuMockAttempt.lesen_level, max_points=100),
        _competency_stat(db, "HOEREN", VizuMockAttempt.hoeren_score, VizuMockAttempt.hoeren_level, max_points=20),
        _competency_stat(db, "SCHREIBEN", VizuMockAttempt.schreiben_score, VizuMockAttempt.schreiben_level, max_points=100),
        _competency_stat(db, "SPRECHEN", None, VizuMockAttempt.sprechen_level, max_points=None),
    ]

    return {
        "level_distribution": level_distribution,
        "total_leveled": total_leveled,
        "competencies": competencies,
    }


# ============================================================
# Comprehensive Analytics tab
# ============================================================


def get_analytics(db: Session) -> dict:
    total = db.query(func.count(VizuMockAttempt.id)).scalar() or 0
    in_progress = (
        db.query(func.count(VizuMockAttempt.id)).filter(VizuMockAttempt.status == STATUS_IN_PROGRESS).scalar() or 0
    )
    abandonment_rate_percent = round(in_progress / total * 100, 1) if total > 0 else None

    return {
        "overview": get_overview(db),
        "activity_7d": get_activity(db, 7),
        "activity_30d": get_activity(db, 30),
        "level_analytics": get_level_analytics(db),
        "time_analytics": {
            "average_completion_minutes": _average_duration_minutes(db),
            "abandonment_rate_percent": abandonment_rate_percent,
        },
    }


# ============================================================
# Oxirgi testlar / Natijalar — paginated attempts list
# ============================================================


def _attempt_item(attempt: VizuMockAttempt) -> dict:
    duration_minutes = None
    if attempt.completed_at is not None:
        duration_minutes = round((attempt.completed_at - attempt.started_at).total_seconds() / 60, 1)

    user = attempt.user
    student_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username

    return {
        "id": attempt.id,
        "user_id": attempt.user_id,
        "student_name": student_name,
        "username": user.username,
        "email": user.email,
        "status": attempt.status,
        "started_at": attempt.started_at,
        "completed_at": attempt.completed_at,
        "duration_minutes": duration_minutes,
        "lesen_level": attempt.lesen_level,
        "hoeren_level": attempt.hoeren_level,
        "schreiben_level": attempt.schreiben_level,
        "sprechen_level": attempt.sprechen_level,
        "overall_level": attempt.overall_level,
        "lesen_score": attempt.lesen_score,
        "hoeren_score": attempt.hoeren_score,
        "schreiben_score": attempt.schreiben_score,
    }


def list_attempts(
    db: Session,
    page: int,
    page_size: int,
    search: str | None = None,
    level: str | None = None,
    status: str | None = None,
) -> dict:
    base_query = db.query(VizuMockAttempt).join(User, User.id == VizuMockAttempt.user_id)

    if search:
        like = f"%{search}%"
        base_query = base_query.filter(or_(User.username.ilike(like), User.email.ilike(like)))
    if status:
        base_query = base_query.filter(VizuMockAttempt.status == status.upper())
    if level:
        base_query = base_query.filter(_level_expr() == level.upper())

    total = base_query.count()
    total_pages = max(1, (total + page_size - 1) // page_size)

    rows = (
        base_query.options(joinedload(VizuMockAttempt.user))
        .order_by(VizuMockAttempt.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [_attempt_item(a) for a in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def get_attempt_detail(db: Session, attempt_id: UUID) -> dict | None:
    attempt = (
        db.query(VizuMockAttempt)
        .options(joinedload(VizuMockAttempt.user))
        .filter(VizuMockAttempt.id == attempt_id)
        .first()
    )
    return _attempt_item(attempt) if attempt is not None else None


# ============================================================
# Hören Audio management
# ============================================================


def list_audio(db: Session) -> list[VizuMockAudio]:
    return db.query(VizuMockAudio).order_by(VizuMockAudio.created_at.desc()).all()


def create_audio(db: Session, data: VizuMockAudioCreate) -> VizuMockAudio:
    audio = VizuMockAudio(
        title=data.title,
        audio_url=data.audio_url,
        duration_seconds=data.duration_seconds,
        task_id=data.task_id,
    )
    db.add(audio)
    db.commit()
    db.refresh(audio)
    return audio


def update_audio(db: Session, audio_id: UUID, data: VizuMockAudioUpdate) -> VizuMockAudio | None:
    audio = db.query(VizuMockAudio).filter(VizuMockAudio.id == audio_id).first()
    if audio is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(audio, field, value)
    db.commit()
    db.refresh(audio)
    return audio


def delete_audio(db: Session, audio_id: UUID) -> bool:
    audio = db.query(VizuMockAudio).filter(VizuMockAudio.id == audio_id).first()
    if audio is None:
        return False
    db.delete(audio)
    db.commit()
    return True
