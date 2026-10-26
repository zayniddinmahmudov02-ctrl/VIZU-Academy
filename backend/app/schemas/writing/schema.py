from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from app.schemas.base import BaseSchema


class RubricCriterion(BaseSchema):
    key: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)
    max: int = Field(ge=1, le=100)


def _check_rubric(value):
    if value is None:
        return value
    from app.services.lesson_skills.ai_evaluation import validate_rubric

    validate_rubric([c.model_dump() if hasattr(c, "model_dump") else c for c in value])
    return value


class WritingBase(BaseSchema):
    lesson_id: UUID
    title: str
    instruction: str
    # None = no limit (book task without a word count)
    min_words: int | None = 30
    max_words: int | None = 150
    order_index: int = 1
    is_published: bool = False
    # AI evaluation (A1 rubric by default — see services/lesson_skills/ai_evaluation.py)
    ai_evaluation_enabled: bool = True
    feedback_language: str = Field(default="uz", pattern=r"^[a-z]{2}$")
    max_score: int = Field(default=100, ge=1, le=1000)
    max_attempts: int = Field(default=3, ge=1, le=20)
    rubric: list[RubricCriterion] | None = None
    helper_words: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    opens_at: datetime | None = None
    closes_at: datetime | None = None
    # A1-C1 task metadata
    text_type: str | None = Field(default=None, pattern=r"^(message|email|letter|description|opinion|essay|report|other)$")
    audience: str | None = Field(default=None, max_length=1000)
    time_limit_minutes: int | None = Field(default=None, ge=1, le=240)
    content_id: str | None = Field(default=None, max_length=120)

    _rubric_ok = field_validator("rubric")(classmethod(lambda cls, v: _check_rubric(v)))


class WritingCreate(WritingBase):
    # Server-side only: never part of a student-facing response.
    ai_instructions: str | None = Field(default=None, max_length=5000)


class WritingUpdate(BaseSchema):
    title: str | None = None
    instruction: str | None = None
    min_words: int | None = None
    max_words: int | None = None
    order_index: int | None = None
    is_published: bool | None = None
    ai_evaluation_enabled: bool | None = None
    ai_instructions: str | None = Field(default=None, max_length=5000)
    feedback_language: str | None = Field(default=None, pattern=r"^[a-z]{2}$")
    max_score: int | None = Field(default=None, ge=1, le=1000)
    max_attempts: int | None = Field(default=None, ge=1, le=20)
    rubric: list[RubricCriterion] | None = None
    helper_words: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    opens_at: datetime | None = None
    closes_at: datetime | None = None
    text_type: str | None = Field(default=None, pattern=r"^(message|email|letter|description|opinion|essay|report|other)$")
    audience: str | None = Field(default=None, max_length=1000)
    time_limit_minutes: int | None = Field(default=None, ge=1, le=240)

    _rubric_ok = field_validator("rubric")(classmethod(lambda cls, v: _check_rubric(v)))


class WritingResponse(WritingBase):
    """Student-facing — never contains ai_instructions."""

    id: UUID

    model_config = ConfigDict(from_attributes=True)


class WritingAdminResponse(WritingResponse):
    ai_instructions: str | None = None
