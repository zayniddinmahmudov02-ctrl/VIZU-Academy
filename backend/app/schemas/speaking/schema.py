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



class SpeakingBase(BaseSchema):
    lesson_id: UUID

    title: str

    topic: str

    instruction: str

    sample_answer: str | None = None

    keywords: str | None = None

    preparation_time: int = 15

    speaking_time: int = 90

    order_index: int = 1

    is_published: bool = False

    # AI evaluation (A1 speaking rubric by default)
    ai_evaluation_enabled: bool = True
    feedback_language: str = Field(default="uz", pattern=r"^[a-z]{2}$")
    max_score: int = Field(default=100, ge=1, le=1000)
    max_attempts: int = Field(default=3, ge=1, le=20)
    rubric: list[RubricCriterion] | None = None
    # speaking_time (above) is the maximum answer length in seconds
    min_duration_seconds: int = Field(default=0, ge=0, le=3600)
    # A1-C1 task metadata
    response_type: str = Field(default="MONOLOG", pattern=r"^(MONOLOG|DIALOG)$")
    questions: list[str] | None = Field(default=None, max_length=20)
    content_id: str | None = Field(default=None, max_length=120)
    # SPRECHEN = the Sprechen step; FRAGE = Frage des Themas (same recorder)
    task_kind: str = Field(default="SPRECHEN", pattern=r"^(SPRECHEN|FRAGE)$")

    _rubric_ok = field_validator("rubric")(classmethod(lambda cls, v: _check_rubric(v)))


class SpeakingCreate(SpeakingBase):
    ai_instructions: str | None = Field(default=None, max_length=5000)
    # expected communicative goal — for the AI evaluation only
    speech_goal: str | None = Field(default=None, max_length=2000)

    pass


class SpeakingUpdate(BaseSchema):
    title: str | None = None

    topic: str | None = None

    instruction: str | None = None

    sample_answer: str | None = None

    keywords: str | None = None

    preparation_time: int | None = None

    speaking_time: int | None = None

    order_index: int | None = None

    is_published: bool | None = None
    ai_evaluation_enabled: bool | None = None
    ai_instructions: str | None = Field(default=None, max_length=5000)
    feedback_language: str | None = Field(default=None, pattern=r"^[a-z]{2}$")
    max_score: int | None = Field(default=None, ge=1, le=1000)
    max_attempts: int | None = Field(default=None, ge=1, le=20)
    rubric: list[RubricCriterion] | None = None
    min_duration_seconds: int | None = Field(default=None, ge=0, le=3600)
    response_type: str | None = Field(default=None, pattern=r"^(MONOLOG|DIALOG)$")
    questions: list[str] | None = Field(default=None, max_length=20)
    speech_goal: str | None = Field(default=None, max_length=2000)
    task_kind: str | None = Field(default=None, pattern=r"^(SPRECHEN|FRAGE)$")

    _rubric_ok = field_validator("rubric")(classmethod(lambda cls, v: _check_rubric(v)))


class SpeakingResponse(SpeakingBase):
    id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )


class SpeakingAdminResponse(SpeakingResponse):
    ai_instructions: str | None = None
    speech_goal: str | None = None
