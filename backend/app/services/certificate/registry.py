"""One read view over every certificate a student holds (student panel +
admin "Zertifikate").

Two real sources, nothing copied, nothing invented:
  * `certificates` rows — course certificates and manually issued ones
    (source COURSE / VORBEREITUNG / VIZU_MULTILEVEL as stored per row);
  * VIZU-Multilevel attempts with a FINAL result (A1–C1 or "unter A1") —
    the certificate of the exam is derived from the attempt (number
    "VIZU-ML-…" issued on first view, PDF rendered on request; see
    services/vizu_multilevel/certificate_service). "Available" is read from
    the stored columns (result_score + level) — no result is recomputed here.
Item ids are prefixed ("c:" certificate row, "ml:" multilevel attempt) so the
two id spaces never clash."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.certificate import SOURCE_COURSE, SOURCE_VIZU_MULTILEVEL, SOURCE_VORBEREITUNG, Certificate
from app.models.course import Course
from app.models.user import User
from app.models.vizu_multilevel_attempt import STATUS_COMPLETED, VizuMultilevelAttempt
from app.models.vizu_multilevel_discarded import REASON_BELOW_A1
from app.services.vizu_multilevel.service import LEVEL_BELOW_A1

TYPE_LABELS = {SOURCE_COURSE: "Kursabschluss", SOURCE_VORBEREITUNG: "Vorbereitung", SOURCE_VIZU_MULTILEVEL: "VIZU-Multilevel Zertifikat"}
LEVEL_ORDER = ("BELOW_A1", "A1", "A2", "B1", "B2", "C1")
PDF_DIR = Path("uploads/certificates")  # CertificatePDFService.OUTPUT_DIR

# status values
VALID, REVOKED, ISSUED, AVAILABLE = "valid", "revoked", "issued", "available"


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def level_label(level: str | None) -> str | None:
    return "unter A1" if level == LEVEL_BELOW_A1 else level


def course_pdf_path(cert: Certificate) -> Path | None:
    """The stored PDF of a certificate row — only inside the certificates folder."""
    if not cert.pdf_url:
        return None
    root = PDF_DIR.resolve()
    path = Path(cert.pdf_url).resolve()
    return path if (root in path.parents) and path.is_file() else None


def _user_ref(user: User | None) -> dict | None:
    if user is None:
        return None
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username
    return {"id": str(user.id), "name": name, "email": user.email, "username": user.username}


def _from_row(c: Certificate, course: Course | None, user: User | None) -> dict:
    return {
        "id": f"c:{c.id}", "source": c.source, "type_label": TYPE_LABELS.get(c.source, c.source), "level": c.level,
        "level_label": level_label(c.level), "certificate_number": c.certificate_number, "issued_at": _aware(c.issued_at),
        "status": VALID if c.is_valid else REVOKED, "score": c.score,
        "course": {"id": str(course.id), "title": course.title, "level": course.level} if course else None,
        "user": _user_ref(user), "pdf_available": course_pdf_path(c) is not None, "attempt_id": None,
    }


def _from_attempt(a: VizuMultilevelAttempt, user: User | None) -> dict:
    level = a.overall_level or (LEVEL_BELOW_A1 if a.discarded_reason == REASON_BELOW_A1 else None)
    return {
        "id": f"ml:{a.id}", "source": SOURCE_VIZU_MULTILEVEL, "type_label": TYPE_LABELS[SOURCE_VIZU_MULTILEVEL], "level": level,
        "level_label": level_label(level), "certificate_number": a.certificate_number, "issued_at": _aware(a.completed_at),
        # the number is issued the first time the certificate is opened
        "status": ISSUED if a.certificate_number else AVAILABLE, "score": a.result_score, "course": None,
        "user": _user_ref(user), "pdf_available": True, "attempt_id": str(a.id), "attempt_number": a.attempt_number,
    }


def _final_attempts():
    return select(VizuMultilevelAttempt).where(
        VizuMultilevelAttempt.status == STATUS_COMPLETED,
        VizuMultilevelAttempt.result_score.is_not(None),
        or_(VizuMultilevelAttempt.overall_level.is_not(None), VizuMultilevelAttempt.discarded_reason == REASON_BELOW_A1),
    )


def collect(db: Session, user_id: UUID | None = None) -> list[dict]:
    """Every certificate (or only one student's), newest first. Two queries
    per source plus one for users and one for courses — no N+1."""
    rows = list(db.scalars(select(Certificate).where(Certificate.user_id == user_id) if user_id else select(Certificate)))
    q = _final_attempts()
    attempts = list(db.scalars(q.where(VizuMultilevelAttempt.user_id == user_id) if user_id else q))
    user_ids = {r.user_id for r in rows} | {a.user_id for a in attempts}
    users = {u.id: u for u in db.scalars(select(User).where(User.id.in_(user_ids)))} if user_ids else {}
    course_ids = {r.course_id for r in rows if r.course_id}
    courses = {c.id: c for c in db.scalars(select(Course).where(Course.id.in_(course_ids)))} if course_ids else {}
    items = [_from_row(r, courses.get(r.course_id), users.get(r.user_id)) for r in rows]
    items += [_from_attempt(a, users.get(a.user_id)) for a in attempts]
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    items.sort(key=lambda i: i["issued_at"] or epoch, reverse=True)
    return items


def for_student(db: Session, user: User) -> dict:
    """The student's own certificates, grouped for display (by type, then level)."""
    items = collect(db, user.id)
    for i in items:
        i.pop("user", None)
    return {"items": items, "total": len(items)}


def filter_items(items: list[dict], *, q: str | None = None, level: str | None = None, source: str | None = None, status: str | None = None,
                 date_from: date | None = None, date_to: date | None = None) -> list[dict]:
    needle = (q or "").strip().casefold()
    out = []
    for i in items:
        if level and i["level"] != level:
            continue
        if source and i["source"] != source:
            continue
        if status and i["status"] != status:
            continue
        day = i["issued_at"].date() if i["issued_at"] else None
        if date_from and (day is None or day < date_from):
            continue
        if date_to and (day is None or day > date_to):
            continue
        if needle:
            u = i.get("user") or {}
            hay = " ".join(str(x or "") for x in (u.get("name"), u.get("email"), u.get("username"), i["certificate_number"],
                                                   (i.get("course") or {}).get("title"))).casefold()
            if needle not in hay:
                continue
        out.append(i)
    return out


def admin_list(db: Session, *, page: int = 1, page_size: int = 25, user_id: UUID | None = None, **filters) -> dict:
    everything = collect(db, user_id)
    items = filter_items(everything, **filters)
    page_size = max(1, min(page_size, 100))
    total = len(items)
    pages = max(1, -(-total // page_size))
    page = max(1, min(page, pages))
    by_source: dict[str, int] = {}
    by_level: dict[str, int] = {}
    for i in everything:
        by_source[i["source"]] = by_source.get(i["source"], 0) + 1
        by_level[i["level"] or "—"] = by_level.get(i["level"] or "—", 0) + 1
    return {
        "items": items[(page - 1) * page_size: page * page_size], "total": total, "page": page, "page_size": page_size, "total_pages": pages,
        "stats": {"total": len(everything), "by_source": by_source,
                  "by_level": dict(sorted(by_level.items(), key=lambda kv: LEVEL_ORDER.index(kv[0]) if kv[0] in LEVEL_ORDER else 99))},
    }


def count_all(db: Session) -> int:
    """Certificates issued or available — the admin dashboard KPI."""
    from sqlalchemy import func

    rows = int(db.scalar(select(func.count()).select_from(Certificate)) or 0)
    attempts = int(db.scalar(select(func.count()).select_from(_final_attempts().subquery())) or 0)
    return rows + attempts
