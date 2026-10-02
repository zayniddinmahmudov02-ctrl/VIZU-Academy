from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseSchema


class VizuMultilevelWritingTaskPublic(BaseSchema):
    """Never includes the rubric — that's teacher-only grading metadata,
    not something a student needs (or should see) while answering."""

    id: UUID
    order_index: int
    title: str
    instruction: str
    min_words: int
    max_words: int
    image_url: str | None
    points: int


class VizuMultilevelWritingSubmissionPublic(BaseSchema):
    task_id: UUID
    content: str
    word_count: int
    status: str


class VizuMultilevelWritingSaveRequest(BaseSchema):
    task_id: UUID
    content: str


class VizuMultilevelWritingSubmitAllResponse(BaseSchema):
    attempt_id: UUID
    schreiben_submitted_at: datetime


# ---- AI evaluation result (read-only for the student) ----


class VizuMultilevelWritingCriterionResult(BaseSchema):
    name: str
    score: int
    max: int
    justification: str = ""


class VizuMultilevelWritingErrorItem(BaseSchema):
    original: str
    correction: str
    explanation: str
    category: str = ""


class VizuMultilevelWritingTaskEvaluation(BaseSchema):
    task_id: UUID
    order_index: int
    title: str
    score: int
    max_score: int
    word_count: int
    criteria: list[VizuMultilevelWritingCriterionResult]
    strengths: list[str]
    errors: list[VizuMultilevelWritingErrorItem]
    feedback: str
    next_steps: list[str]


class VizuMultilevelWritingSummary(BaseSchema):
    good: list[str]
    improve: list[str]
    next: list[str]


class VizuMultilevelWritingEvaluation(BaseSchema):
    # NOT_SUBMITTED / PENDING / DONE / FAILED
    status: str
    evaluated: int
    total_tasks: int
    total_score: int | None
    max_score: int
    tasks: list[VizuMultilevelWritingTaskEvaluation]
    summary: VizuMultilevelWritingSummary | None
