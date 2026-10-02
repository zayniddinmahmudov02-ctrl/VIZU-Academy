from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema

SpeakingLevel = Literal["A1", "A2", "B1", "B2", "C1"]


class VizuMultilevelSpeakingTaskPublic(BaseSchema):
    """No `level` — backend/admin-side scoring data, never shown to the student."""

    id: UUID
    order_index: int
    title: str
    instruction: str
    preparation_text: str | None
    prep_seconds: int
    min_seconds: int
    max_seconds: int
    points: int


class VizuMultilevelSpeakingSubmissionPublic(BaseSchema):
    """The student's own saved answer — pipeline status only; no score,
    level or transcript while the test is running."""

    id: UUID
    task_id: UUID
    duration_seconds: int | None
    submitted_at: datetime | None
    status: str | None


class VizuMultilevelSpeakingCriterionResult(BaseSchema):
    key: str
    label: str
    score: int
    max: int


class VizuMultilevelSpeakingErrorItem(BaseSchema):
    original: str
    correction: str
    explanation: str


class VizuMultilevelSpeakingTaskEvaluation(BaseSchema):
    task_id: UUID
    order_index: int
    title: str
    score: int
    max_score: int
    answered: bool
    transcript: str | None
    criteria: list[VizuMultilevelSpeakingCriterionResult]
    strengths: list[str]
    improvements: list[str]
    errors: list[VizuMultilevelSpeakingErrorItem]
    feedback: str
    next_step: str
    teacher_comment: str | None


class VizuMultilevelSpeakingProgressItem(BaseSchema):
    task_id: UUID
    order_index: int
    status: str | None


class VizuMultilevelSpeakingEvaluation(BaseSchema):
    # NOT_SUBMITTED / PENDING / DONE / FAILED
    status: str
    evaluated: int
    total_tasks: int
    progress: list[VizuMultilevelSpeakingProgressItem]
    total_score: int | None
    max_score: int
    # Only in the final result: A1..C1 or BELOW_A1.
    level: str | None
    tasks: list[VizuMultilevelSpeakingTaskEvaluation]


class VizuMultilevelSpeakingSubmitAllResponse(BaseSchema):
    attempt_id: UUID
    sprechen_submitted_at: datetime


# ---- Admin ----


class VizuMultilevelSpeakingTaskAdminCreate(BaseSchema):
    """`order_index` = Aufgabe 1-5 (task type); `level` = internal CEFR
    variant. (order_index, level) is unique."""

    level: SpeakingLevel
    order_index: int = Field(ge=1, le=5)
    title: str = Field(min_length=1, max_length=255)
    instruction: str = Field(min_length=1)
    preparation_text: str | None = None
    prep_seconds: int = Field(default=0, ge=0, le=600)
    min_seconds: int = Field(default=0, ge=0, le=600)
    max_seconds: int = Field(default=120, ge=10, le=600)
    points: int = Field(default=20, ge=1, le=100)
    is_active: bool = True


class VizuMultilevelSpeakingTaskAdminUpdate(BaseSchema):
    level: SpeakingLevel | None = None
    order_index: int | None = Field(default=None, ge=1, le=5)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    instruction: str | None = Field(default=None, min_length=1)
    preparation_text: str | None = None
    prep_seconds: int | None = Field(default=None, ge=0, le=600)
    min_seconds: int | None = Field(default=None, ge=0, le=600)
    max_seconds: int | None = Field(default=None, ge=10, le=600)
    points: int | None = Field(default=None, ge=1, le=100)
    is_active: bool | None = None


class VizuMultilevelSpeakingTaskAdminResponse(BaseSchema):
    id: UUID
    level: str
    order_index: int
    title: str
    instruction: str
    preparation_text: str | None
    prep_seconds: int
    min_seconds: int
    max_seconds: int
    points: int
    is_active: bool


# ---- Teacher ----


class VizuMultilevelTeacherSpeakingListItem(BaseSchema):
    attempt_id: UUID
    student_name: str
    username: str
    email: str
    sprechen_submitted_at: datetime
    graded_count: int
    total_submissions: int
    sprechen_score: int | None
    max_score: int
    status: str  # NEW / IN_PROGRESS / GRADED


class VizuMultilevelTeacherSpeakingSubmissionDetail(BaseSchema):
    submission_id: UUID | None
    task_id: UUID
    order_index: int
    level: str
    title: str
    instruction: str
    points: int
    duration_seconds: int | None
    has_audio: bool
    teacher_score: int | None
    teacher_comment: str | None
    # Server-side pipeline (speech-to-text + AI evaluation).
    status: str | None = None
    transcript: str | None = None
    transcript_confidence: float | None = None
    audio_observations: dict | None = None
    ai_score: int | None = None
    ai_feedback: dict | None = None
    evaluation_error: str | None = None


class VizuMultilevelTeacherSpeakingDetail(BaseSchema):
    attempt_id: UUID
    student_name: str
    username: str
    email: str
    sprechen_submitted_at: datetime
    sprechen_score: int | None
    sprechen_level: str | None
    sprechen_feedback: str | None
    submissions: list[VizuMultilevelTeacherSpeakingSubmissionDetail]


class VizuMultilevelTeacherSpeakingGradeRequest(BaseSchema):
    score: int
    comment: str | None = None


class VizuMultilevelTeacherSpeakingFeedbackRequest(BaseSchema):
    sprechen_feedback: str | None
