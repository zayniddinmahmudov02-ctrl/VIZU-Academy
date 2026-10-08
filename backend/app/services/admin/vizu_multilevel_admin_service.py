"""VIZU-Multilevel admin dashboard — dashboard stats, activity/level/competency
analytics, paginated attempts (Recent Tests / Results), and Hören audio
CRUD, all read from the existing vizu_multilevel_attempts/vizu_multilevel_tasks data
(no new attempt-related schema needed) plus the new vizu_multilevel_audios
table. Every number here is a real aggregate SQL query; a metric that the
current data model genuinely cannot support (e.g. per-skill timing, since
only one overall started_at/completed_at pair is tracked per attempt) is
simply not exposed here, rather than being estimated or faked."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.user import User
from app.models.vizu_multilevel_attempt import STATUS_COMPLETED, STATUS_IN_PROGRESS, VizuMultilevelAttempt
from app.models.vizu_multilevel_content import CEFR_LEVELS


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _level_expr():
    # The overall result only — set once every competency with content is
    # graded (see services/vizu_multilevel/service.py). Never falls back to
    # a single competency's level.
    return VizuMultilevelAttempt.overall_level


def _average_duration_minutes(db: Session, since: datetime | None = None) -> float | None:
    query = db.query(
        func.avg(func.extract("epoch", VizuMultilevelAttempt.completed_at - VizuMultilevelAttempt.started_at))
    ).filter(VizuMultilevelAttempt.status == STATUS_COMPLETED, VizuMultilevelAttempt.completed_at.isnot(None))
    if since is not None:
        query = query.filter(VizuMultilevelAttempt.started_at >= since)
    seconds = query.scalar()
    return round(float(seconds) / 60, 1) if seconds is not None else None


def _most_common_level(db: Session):
    level_expr = _level_expr()
    rows = (
        db.query(level_expr.label("level"), func.count(VizuMultilevelAttempt.id).label("cnt"))
        .filter(level_expr.isnot(None))
        .group_by(level_expr)
        .order_by(func.count(VizuMultilevelAttempt.id).desc())
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

    total_attempts = db.query(func.count(VizuMultilevelAttempt.id)).scalar() or 0
    today_attempts = (
        db.query(func.count(VizuMultilevelAttempt.id)).filter(VizuMultilevelAttempt.started_at >= today_start).scalar() or 0
    )
    week_attempts = (
        db.query(func.count(VizuMultilevelAttempt.id)).filter(VizuMultilevelAttempt.started_at >= week_start).scalar() or 0
    )
    month_attempts = (
        db.query(func.count(VizuMultilevelAttempt.id)).filter(VizuMultilevelAttempt.started_at >= month_start).scalar() or 0
    )
    completed_attempts = (
        db.query(func.count(VizuMultilevelAttempt.id)).filter(VizuMultilevelAttempt.status == STATUS_COMPLETED).scalar() or 0
    )
    in_progress_attempts = (
        db.query(func.count(VizuMultilevelAttempt.id)).filter(VizuMultilevelAttempt.status == STATUS_IN_PROGRESS).scalar() or 0
    )

    average_score_percent = get_statistics(db)["average_score_percent"] if total_attempts else None

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
            func.date_trunc("day", VizuMultilevelAttempt.started_at).label("day"),
            func.count(VizuMultilevelAttempt.id).label("cnt"),
        )
        .filter(VizuMultilevelAttempt.started_at >= range_start)
        .group_by("day")
        .all()
    )
    completed_rows = (
        db.query(
            func.date_trunc("day", VizuMultilevelAttempt.completed_at).label("day"),
            func.count(VizuMultilevelAttempt.id).label("cnt"),
        )
        .filter(VizuMultilevelAttempt.completed_at.isnot(None), VizuMultilevelAttempt.completed_at >= range_start)
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


def _live_maxima(db: Session) -> dict[str, float]:
    """Max points per competency from the CURRENT published content (0 when
    a competency has no content yet)."""
    from app.services.vizu_multilevel import service as flow

    return {
        "lesen": flow._published_question_count(db, "LESEN")[1],
        "hoeren": flow._published_question_count(db, "HOEREN")[1],
        "schreiben": float(flow._writing_totals(db)[1]),
        "sprechen": float(flow._speaking_totals(db)[1]),
    }


def _competency_stat(db: Session, skill: str, score_col, level_col, max_points: float | None) -> dict:
    avg_score = db.query(func.avg(score_col)).filter(score_col.isnot(None)).scalar()
    average_percent = round(float(avg_score) / max_points * 100, 1) if avg_score is not None and max_points else None
    submitted_count = db.query(func.count(VizuMultilevelAttempt.id)).filter(score_col.isnot(None)).scalar() or 0

    level_rows = (
        db.query(level_col.label("level"), func.count(VizuMultilevelAttempt.id).label("cnt"))
        .filter(level_col.isnot(None))
        .group_by(level_col)
        .order_by(func.count(VizuMultilevelAttempt.id).desc())
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
        db.query(level_expr.label("level"), func.count(VizuMultilevelAttempt.id).label("cnt"))
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

    maxima = _live_maxima(db)
    competencies = [
        _competency_stat(db, "LESEN", VizuMultilevelAttempt.lesen_score, VizuMultilevelAttempt.lesen_level, maxima["lesen"]),
        _competency_stat(db, "HOEREN", VizuMultilevelAttempt.hoeren_score, VizuMultilevelAttempt.hoeren_level, maxima["hoeren"]),
        _competency_stat(
            db, "SCHREIBEN", VizuMultilevelAttempt.schreiben_score, VizuMultilevelAttempt.schreiben_level, maxima["schreiben"]
        ),
        _competency_stat(
            db, "SPRECHEN", VizuMultilevelAttempt.sprechen_score, VizuMultilevelAttempt.sprechen_level, maxima["sprechen"]
        ),
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
    total = db.query(func.count(VizuMultilevelAttempt.id)).scalar() or 0
    in_progress = (
        db.query(func.count(VizuMultilevelAttempt.id)).filter(VizuMultilevelAttempt.status == STATUS_IN_PROGRESS).scalar() or 0
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


def _attempt_item(attempt: VizuMultilevelAttempt) -> dict:
    duration_minutes = None
    if attempt.completed_at is not None:
        duration_minutes = round((attempt.completed_at - attempt.started_at).total_seconds() / 60, 1)

    user = attempt.user
    student_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username

    return {
        "id": attempt.id,
        "attempt_number": attempt.attempt_number,
        "result_score": attempt.result_score,
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
        "sprechen_score": attempt.sprechen_score,
    }


def list_attempts(
    db: Session,
    page: int,
    page_size: int,
    search: str | None = None,
    level: str | None = None,
    status: str | None = None,
) -> dict:
    base_query = db.query(VizuMultilevelAttempt).join(User, User.id == VizuMultilevelAttempt.user_id)

    if search:
        like = f"%{search}%"
        base_query = base_query.filter(or_(User.username.ilike(like), User.email.ilike(like)))
    if status:
        base_query = base_query.filter(VizuMultilevelAttempt.status == status.upper())
    if level:
        base_query = base_query.filter(_level_expr() == level.upper())

    total = base_query.count()
    total_pages = max(1, (total + page_size - 1) // page_size)

    rows = (
        base_query.options(joinedload(VizuMultilevelAttempt.user))
        .order_by(VizuMultilevelAttempt.started_at.desc())
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
        db.query(VizuMultilevelAttempt)
        .options(joinedload(VizuMultilevelAttempt.user))
        .filter(VizuMultilevelAttempt.id == attempt_id)
        .first()
    )
    return _attempt_item(attempt) if attempt is not None else None


# ============================================================
# Statistics tab
# ============================================================


def get_statistics(db: Session) -> dict:
    """Real aggregates only; with no data every number is 0. Attempts that
    are not kept in a student's history (below A1, abandoned) are counted
    through the anonymous `VizuMultilevelDiscardedAttempt` tally rows."""
    from app.models.vizu_multilevel_discarded import (
        REASON_ABANDONED,
        REASON_BELOW_A1,
        VizuMultilevelDiscardedAttempt,
    )
    from app.services.vizu_multilevel import service as flow

    # Rows marked as discarded (below A1 / no content) are counted through
    # their tally row only; abandoned = idle unfinished attempts (they are no
    # longer deleted) + legacy tally rows.
    kept = VizuMultilevelAttempt.discarded_reason.is_(None)
    stale_cutoff = flow._now() - flow.ABANDON_AFTER
    saved_total = db.query(func.count(VizuMultilevelAttempt.id)).filter(kept).scalar() or 0
    completed = (
        db.query(func.count(VizuMultilevelAttempt.id))
        .filter(kept, VizuMultilevelAttempt.status == STATUS_COMPLETED)
        .scalar()
        or 0
    )
    stale = (
        db.query(func.count(VizuMultilevelAttempt.id))
        .filter(VizuMultilevelAttempt.status == STATUS_IN_PROGRESS, VizuMultilevelAttempt.updated_at < stale_cutoff)
        .scalar()
        or 0
    )
    in_progress = saved_total - completed - stale
    below_a1 = (
        db.query(func.count(VizuMultilevelDiscardedAttempt.id))
        .filter(VizuMultilevelDiscardedAttempt.reason == REASON_BELOW_A1)
        .scalar()
        or 0
    )
    abandoned = (
        db.query(func.count(VizuMultilevelDiscardedAttempt.id))
        .filter(VizuMultilevelDiscardedAttempt.reason == REASON_ABANDONED)
        .scalar()
        or 0
    ) + stale
    pending_review = (
        db.query(func.count(VizuMultilevelAttempt.id))
        .filter(kept, VizuMultilevelAttempt.status == STATUS_COMPLETED, VizuMultilevelAttempt.overall_level.is_(None))
        .scalar()
        or 0
    )

    level_rows = dict(
        db.query(VizuMultilevelAttempt.overall_level, func.count(VizuMultilevelAttempt.id))
        .filter(VizuMultilevelAttempt.overall_level.isnot(None))
        .group_by(VizuMultilevelAttempt.overall_level)
        .all()
    )
    results = [{"result": level, "count": int(level_rows.get(level, 0))} for level in CEFR_LEVELS]
    results.append({"result": "BELOW_A1", "count": below_a1})

    # Per-competency averages over every FINISHED attempt (kept + below-A1
    # tally rows), as a percentage of the current content's max points.
    maxima = _live_maxima(db)
    columns = {
        "lesen": "lesen_score",
        "hoeren": "hoeren_score",
        "schreiben": "schreiben_score",
        "sprechen": "sprechen_score",
    }
    averages = []
    for skill, column in columns.items():
        kept_col = getattr(VizuMultilevelAttempt, column)
        discarded_col = getattr(VizuMultilevelDiscardedAttempt, column)
        kept_sum, kept_count = (
            db.query(func.coalesce(func.sum(kept_col), 0), func.count(kept_col))
            .filter(kept, VizuMultilevelAttempt.status == STATUS_COMPLETED, kept_col.isnot(None))
            .one()
        )
        disc_sum, disc_count = (
            db.query(func.coalesce(func.sum(discarded_col), 0), func.count(discarded_col))
            .filter(VizuMultilevelDiscardedAttempt.reason == REASON_BELOW_A1, discarded_col.isnot(None))
            .one()
        )
        count = int(kept_count) + int(disc_count)
        maximum = maxima[skill]
        percent = round((float(kept_sum) + float(disc_sum)) / count / maximum * 100, 1) if count and maximum else 0.0
        averages.append({"skill": skill.upper(), "average_percent": percent, "finished_count": count})

    scored = [a["average_percent"] for a in averages if a["finished_count"] > 0 and a["average_percent"] > 0]
    average_score = round(sum(scored) / len(scored), 1) if scored else 0.0

    finished = completed + below_a1
    total = saved_total - stale + below_a1 + abandoned
    completion_rate = round(finished / total * 100, 1) if total else 0.0

    return {
        "total_attempts": total,
        "completed_attempts": completed,
        "in_progress_attempts": in_progress,
        "abandoned_attempts": abandoned,
        "pending_review_attempts": pending_review,
        "results": results,
        "average_score_percent": average_score,
        "competency_averages": averages,
        "completion_rate_percent": completion_rate,
    }


# ============================================================
# Studenten — best result per student (up to MAX_ATTEMPTS attempts each)
# ============================================================

STUDENT_SORTS = ("best_score", "level", "attempts", "date")


def _student_row(user: User, attempts: list[VizuMultilevelAttempt]) -> dict:
    from app.models.vizu_multilevel_attempt import MAX_ATTEMPTS
    from app.services.vizu_multilevel import service as flow

    attempts = sorted(attempts, key=lambda a: (a.attempt_number or 0, a.started_at))
    best = flow.best_attempt(attempts)
    last = attempts[-1] if attempts else None
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username
    return {
        "user_id": user.id,
        "student_name": name,
        "email": user.email,
        "attempts_used": len(attempts),
        "attempts_remaining": max(0, MAX_ATTEMPTS - len(attempts)),
        "max_attempts": MAX_ATTEMPTS,
        "best_score": best.result_score if best else None,
        "best_level": flow.result_level(best) if best else None,
        "best_attempt_number": best.attempt_number if best else None,
        "best_attempt_id": best.id if best else None,
        "last_attempt_id": last.id if last else None,
        "last_attempt_number": last.attempt_number if last else None,
        "last_attempt_status": last.status if last else None,
        "last_attempt_score": last.result_score if last else None,
        "last_attempt_level": flow.result_level(last) if last else None,
        "last_attempt_date": (last.completed_at or last.started_at) if last else None,
        "attempts": [
            {**flow.attempt_summary_item(a), "certificate_number": a.certificate_number} for a in attempts
        ],
    }


def _sorted_rows(rows: list[dict], sort: str, descending: bool) -> list[dict]:
    """Rows without a value for the sort key always go last; ties fall back
    to the best score (desc), then the name."""
    from app.services.vizu_multilevel import service as flow

    def value(row: dict):
        if sort == "level":
            level = row["best_level"]
            return flow.RESULT_LEVEL_ORDER.index(level) if level in flow.RESULT_LEVEL_ORDER else None
        if sort == "attempts":
            return row["attempts_used"]
        if sort == "date":
            return row["last_attempt_date"]
        return row["best_score"]

    rows = sorted(rows, key=lambda r: (-(r["best_score"] if r["best_score"] is not None else -1), r["student_name"].lower()))
    with_value = [r for r in rows if value(r) is not None]
    without = [r for r in rows if value(r) is None]
    with_value.sort(key=value, reverse=descending)  # stable: keeps the tie order
    return with_value + without


def list_students(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    sort: str = "best_score",
    order: str = "desc",
) -> dict:
    """Every student who started VIZU-Multilevel, with attempts used/remaining,
    best result (highest Gesamtergebnis over ALL final attempts, not just the
    last) and the last attempt. Default order: Bestes Ergebnis, descending."""
    from app.services.vizu_multilevel import service as flow

    sort = sort if sort in STUDENT_SORTS else "best_score"
    descending = order != "asc"
    query = db.query(VizuMultilevelAttempt).join(User, User.id == VizuMultilevelAttempt.user_id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(User.username.ilike(like), User.email.ilike(like), User.first_name.ilike(like), User.last_name.ilike(like))
        )
    attempts = query.options(joinedload(VizuMultilevelAttempt.user)).all()
    flow.sync_missing_scores(db, attempts)

    by_user: dict = {}
    for attempt in attempts:
        by_user.setdefault(attempt.user_id, (attempt.user, []))[1].append(attempt)
    rows = _sorted_rows([_student_row(user, items) for user, items in by_user.values()], sort, descending)

    total = len(rows)
    start = (page - 1) * page_size
    return {
        "items": rows[start : start + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "sort": sort,
        "order": "desc" if descending else "asc",
    }
