from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class VizuMultilevelAttemptResponse(BaseSchema):
    id: UUID
    status: str
    started_at: datetime
    completed_at: datetime | None
    lesen_score: int | None
    lesen_level: str | None
    # Float, not int: Hören weights points by CEFR level (A1=0.5 ...
    # C1=2.5) — see services/vizu_multilevel/hoeren_csv_import_service.py.
    hoeren_score: float | None
    hoeren_level: str | None
    schreiben_score: int | None
    schreiben_level: str | None
    schreiben_submitted_at: datetime | None
    lesen_submitted_at: datetime | None
    discarded_reason: str | None = None
    hoeren_submitted_at: datetime | None
    sprechen_submitted_at: datetime | None
    sprechen_score: int | None
    sprechen_level: str | None
    overall_level: str | None
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Lesen — public content (never exposes is_correct/correct_text_answer,
# same convention as every other student-facing question schema in this
# codebase, e.g. QuizQuestionPublicResponse)
# ============================================================


class VizuMultilevelOptionPublic(BaseSchema):
    id: UUID
    option_text: str
    order_index: int
    model_config = ConfigDict(from_attributes=True)


class VizuMultilevelQuestionPublic(BaseSchema):
    id: UUID
    question_type: str
    # Set only when this question has its own passage, distinct from its
    # task's shared one — see VizuMultilevelTask.passage_text below and the
    # model's own docstring for why both shapes exist in the real content.
    passage_text: str | None
    prompt: str
    order_index: int
    points: float
    options: list[VizuMultilevelOptionPublic]
    model_config = ConfigDict(from_attributes=True)


class VizuMultilevelTaskPublic(BaseSchema):
    """Deliberately has NO `level`: the CEFR level of a task is backend/
    admin-side data used only by the scoring algorithm — a student must not
    see which level a question belongs to while taking the test."""

    id: UUID
    skill: str
    order_index: int
    passage_text: str | None
    questions: list[VizuMultilevelQuestionPublic]
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Lesen — submit + result
# ============================================================


class VizuMultilevelAnswerSubmit(BaseSchema):
    question_id: UUID
    # None = left unanswered (e.g. the 20-minute timer expired first).
    option_id: UUID | None = None


class VizuMultilevelLesenSubmitRequest(BaseSchema):
    answers: list[VizuMultilevelAnswerSubmit]


class VizuMultilevelLevelScore(BaseSchema):
    level: str
    points: float
    max_points: float
    passed: bool


class VizuMultilevelLesenResult(BaseSchema):
    attempt_id: UUID
    total_points: float
    max_points: float
    correct: int
    wrong: int
    unanswered: int
    # null = below A1: not stored as a successful level.
    lesen_level: str | None
    below_a1: bool


# ============================================================
# Server-authoritative timing / flow state
# ============================================================


class VizuMultilevelSectionState(BaseSchema):
    skill: str
    # LOCKED (previous competency not finished) / AVAILABLE / RUNNING / SUBMITTED
    status: str
    started_at: datetime | None
    deadline_at: datetime | None
    # Computed by the server from its own clock; null until started / after submit.
    seconds_remaining: int | None
    duration_seconds: int
    server_now: datetime
    submitted: bool


class VizuMultilevelAttemptState(BaseSchema):
    attempt_id: UUID
    status: str
    next_skill: str | None
    server_now: datetime
    sections: list[VizuMultilevelSectionState]


# ============================================================
# Results
# ============================================================


class VizuMultilevelCompetencyResult(BaseSchema):
    skill: str
    # NO_CONTENT / NOT_SUBMITTED / PENDING_REVIEW / GRADED
    status: str
    raw_score: float | None
    max_score: float | None
    percentage: float | None
    # null for a GRADED competency = did not reach A1 ("Below A1").
    level: str | None


class VizuMultilevelOverallResult(BaseSchema):
    # NO_CONTENT / IN_PROGRESS / PENDING_REVIEW / FINAL / BELOW_A1
    status: str
    level: str | None


class VizuMultilevelAttemptResult(BaseSchema):
    attempt_id: UUID
    competencies: list[VizuMultilevelCompetencyResult]
    overall: VizuMultilevelOverallResult


class VizuMultilevelCompleteResponse(BaseSchema):
    # False = the result was shown once but not stored (below A1 / empty).
    saved: bool
    result: VizuMultilevelAttemptResult


class VizuMultilevelCertificate(BaseSchema):
    """Data for the VIZU-Multilevel certificate. Only ever returned for a
    completed attempt with a final overall level of A1 or higher."""

    attempt_id: UUID
    student_name: str
    issued_at: datetime | None
    overall_level: str
    competencies: list[VizuMultilevelCompetencyResult]
    certificate_number: str | None = None
    # Gesamtergebnis 0-100 (average of the graded competencies, as on the result page).
    total_score: int | None = None


class VizuMultilevelCertificateStatus(BaseSchema):
    """Admin: certificate information for one attempt (read-only)."""

    attempt_id: UUID
    student_name: str
    available: bool
    reason: str | None
    level: str | None
    total_score: int | None
    certificate_number: str | None
    completed_at: datetime | None


class VizuMultilevelAvailability(BaseSchema):
    lesen: int
    hoeren: int
    schreiben: int
    sprechen: int
    min_answers: int
    available: bool
