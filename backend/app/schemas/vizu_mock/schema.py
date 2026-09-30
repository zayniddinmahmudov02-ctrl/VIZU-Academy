from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class VizuMockAttemptResponse(BaseSchema):
    id: UUID
    status: str
    started_at: datetime
    completed_at: datetime | None
    lesen_score: int | None
    lesen_level: str | None
    hoeren_score: int | None
    hoeren_level: str | None
    schreiben_score: int | None
    schreiben_level: str | None
    schreiben_submitted_at: datetime | None
    sprechen_level: str | None
    overall_level: str | None
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Lesen — public content (never exposes is_correct/correct_text_answer,
# same convention as every other student-facing question schema in this
# codebase, e.g. QuizQuestionPublicResponse)
# ============================================================


class VizuMockOptionPublic(BaseSchema):
    id: UUID
    option_text: str
    order_index: int
    model_config = ConfigDict(from_attributes=True)


class VizuMockQuestionPublic(BaseSchema):
    id: UUID
    question_type: str
    # Set only when this question has its own passage, distinct from its
    # task's shared one — see VizuMockTask.passage_text below and the
    # model's own docstring for why both shapes exist in the real content.
    passage_text: str | None
    prompt: str
    order_index: int
    points: int
    options: list[VizuMockOptionPublic]
    model_config = ConfigDict(from_attributes=True)


class VizuMockTaskPublic(BaseSchema):
    id: UUID
    skill: str
    level: str
    order_index: int
    passage_text: str | None
    questions: list[VizuMockQuestionPublic]
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Lesen — submit + result
# ============================================================


class VizuMockAnswerSubmit(BaseSchema):
    question_id: UUID
    # None = left unanswered (e.g. the 20-minute timer expired first).
    option_id: UUID | None = None


class VizuMockLesenSubmitRequest(BaseSchema):
    answers: list[VizuMockAnswerSubmit]


class VizuMockLevelScore(BaseSchema):
    level: str
    points: int
    max_points: int
    passed: bool


class VizuMockLesenResult(BaseSchema):
    attempt_id: UUID
    total_points: int
    max_points: int
    level_scores: list[VizuMockLevelScore]
    lesen_level: str | None
