"""VIZU-Multilevel certificate — data assembled ONLY from the database.

Eligibility = completed attempt (not discarded) whose overall result is FINAL
with a level A1..C1. The level is the exam's existing final level
(service.overall_result: the weakest competency caps the overall level); the
certificate never recomputes or accepts a level/score from the client.

Gesamtergebnis = the average of the graded competency percentages — exactly
the number on the student's result page — and each competency is shown as
points out of 25 (percentage / 4), so the four lines add up to the total.

The certificate number is issued once per attempt (atomic UPDATE ... WHERE
certificate_number IS NULL), from a dedicated sequence: "VIZU-ML-2026-000123".
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import text, update
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.vizu_multilevel_attempt import VizuMultilevelAttempt
from app.services.vizu_multilevel import service

CERTIFIED_LEVELS = ("A1", "A2", "B1", "B2", "C1")
# Uzbekistan has no DST — dates are shown as the student experienced them.
DISPLAY_TZ = timezone(timedelta(hours=5))
GERMAN_MONTHS = (
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
)
SKILLS = (("lesen", "Lesen"), ("hoeren", "Hören"), ("schreiben", "Schreiben"), ("sprechen", "Sprechen"))
POINTS_PER_SKILL = 25

# Why a certificate is not available (machine-readable, never shown raw to students).
NOT_COMPLETED = "NOT_COMPLETED"
BELOW_A1 = "BELOW_A1"
NOT_FINAL = "NOT_FINAL"


class CertificateUnavailable(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class CompetencyLine:
    label: str
    points: float | None  # out of POINTS_PER_SKILL; None = not part of this exam


@dataclass(frozen=True)
class CertificateData:
    student_name: str
    level: str
    total_score: int
    competencies: tuple[CompetencyLine, ...]
    completed_at: datetime
    certificate_number: str


def round_half_up(value: float) -> int:
    """Same rounding as the result page (JS Math.round), not banker's rounding."""
    return int(math.floor(value + 0.5))


def german_date(moment: datetime) -> str:
    local = moment.astimezone(DISPLAY_TZ) if moment.tzinfo else moment
    return f"{local.day:02d}. {GERMAN_MONTHS[local.month - 1]} {local.year}"


def format_points(points: float | None) -> str:
    """German number format: 21 or 21,5."""
    if points is None:
        return "—"
    return f"{points:.1f}".replace(".", ",").removesuffix(",0")


def student_name(user: User) -> str:
    return f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username


def summarize(competencies: list[dict]) -> tuple[int, tuple[CompetencyLine, ...]]:
    """(Gesamtergebnis 0-100, per-skill points /25) from service.competency_results."""
    by_skill = {c["skill"]: c for c in competencies}
    lines = []
    graded = []
    for skill, label in SKILLS:
        comp = by_skill.get(skill)
        pct = comp.get("percentage") if comp and comp.get("status") == service.R_GRADED else None
        if pct is not None:
            graded.append(float(pct))
            lines.append(CompetencyLine(label, round(float(pct) * POINTS_PER_SKILL / 100, 1)))
        else:
            lines.append(CompetencyLine(label, None))
    total = round_half_up(sum(graded) / len(graded)) if graded else 0
    return max(0, min(100, total)), tuple(lines)


def eligibility(db: Session, attempt: VizuMultilevelAttempt) -> dict:
    """The exam's own result for this attempt; raises CertificateUnavailable."""
    if attempt.status != service.STATUS_COMPLETED or attempt.completed_at is None:
        raise CertificateUnavailable(NOT_COMPLETED)
    if attempt.discarded_reason is not None:
        raise CertificateUnavailable(BELOW_A1)
    result = service.build_result(db, attempt)
    overall = result["overall"]
    if overall["status"] == service.O_BELOW_A1:
        raise CertificateUnavailable(BELOW_A1)
    if overall["status"] != service.O_FINAL or overall["level"] not in CERTIFIED_LEVELS:
        raise CertificateUnavailable(NOT_FINAL)
    return result


def ensure_certificate_number(db: Session, attempt: VizuMultilevelAttempt) -> str:
    if attempt.certificate_number:
        return attempt.certificate_number
    serial = db.scalar(text("SELECT nextval('vizu_multilevel_certificate_seq')"))
    year = attempt.completed_at.astimezone(DISPLAY_TZ).year if attempt.completed_at.tzinfo else attempt.completed_at.year
    number = f"VIZU-ML-{year}-{int(serial):06d}"
    db.execute(
        update(VizuMultilevelAttempt)
        .where(VizuMultilevelAttempt.id == attempt.id, VizuMultilevelAttempt.certificate_number.is_(None))
        .values(certificate_number=number)
    )
    db.commit()
    db.refresh(attempt)  # a concurrent request may have won — use the stored number
    return attempt.certificate_number


def build_certificate(db: Session, attempt: VizuMultilevelAttempt, user: User) -> CertificateData:
    """Everything printed on the certificate, from the database only.
    `user` must be the attempt's owner (callers enforce ownership)."""
    result = eligibility(db, attempt)
    total, lines = summarize(result["competencies"])
    return CertificateData(
        student_name=student_name(user),
        level=result["overall"]["level"],
        total_score=total,
        competencies=lines,
        completed_at=attempt.completed_at,
        certificate_number=ensure_certificate_number(db, attempt),
    )


def certificate_status(db: Session, attempt: VizuMultilevelAttempt) -> dict:
    """Admin overview — never issues a number (read-only)."""
    try:
        result = eligibility(db, attempt)
    except CertificateUnavailable as exc:
        return {"available": False, "reason": exc.reason, "level": None, "total_score": None,
                "certificate_number": attempt.certificate_number, "completed_at": attempt.completed_at}
    total, _ = summarize(result["competencies"])
    return {"available": True, "reason": None, "level": result["overall"]["level"], "total_score": total,
            "certificate_number": attempt.certificate_number, "completed_at": attempt.completed_at}


def pdf_filename(data: CertificateData) -> str:
    return f"VIZU-Zertifikat-{data.level}-{data.certificate_number}.pdf"
