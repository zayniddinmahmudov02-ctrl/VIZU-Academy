from uuid import UUID

from pydantic import field_validator, model_validator

from app.models.vizu_multilevel_content import ALL_QUESTION_TYPES, CEFR_LEVELS
from app.schemas.base import BaseSchema


class VizuMultilevelOptionAdmin(BaseSchema):
    id: UUID
    option_text: str
    is_correct: bool
    order_index: int


class VizuMultilevelQuestionAdmin(BaseSchema):
    id: UUID
    question_type: str
    passage_text: str | None
    prompt: str
    order_index: int
    points: float
    is_active: bool
    options: list[VizuMultilevelOptionAdmin]


class VizuMultilevelTaskAdmin(BaseSchema):
    """Admin view of a Lesen/Hören Aufgabe — unlike the student schema this
    DOES carry the CEFR level, the transcript, publish state and which
    option is correct."""

    id: UUID
    skill: str
    level: str
    order_index: int
    passage_text: str | None
    transcript: str | None
    is_published: bool
    audio_url: str | None = None
    questions: list[VizuMultilevelQuestionAdmin]


def _check_level(value: str) -> str:
    value = value.strip().upper()
    if value not in CEFR_LEVELS:
        raise ValueError(f"level must be one of {', '.join(CEFR_LEVELS)}")
    return value


class VizuMultilevelTaskAdminCreate(BaseSchema):
    level: str
    order_index: int
    passage_text: str | None = None
    transcript: str | None = None
    is_published: bool = True

    @field_validator("level")
    @classmethod
    def _level(cls, value: str) -> str:
        return _check_level(value)


class VizuMultilevelTaskAdminUpdate(BaseSchema):
    level: str | None = None
    order_index: int | None = None
    passage_text: str | None = None
    transcript: str | None = None
    is_published: bool | None = None

    @field_validator("level")
    @classmethod
    def _level(cls, value: str | None) -> str | None:
        return _check_level(value) if value is not None else None


class VizuMultilevelOptionInput(BaseSchema):
    option_text: str
    is_correct: bool = False


class VizuMultilevelQuestionInput(BaseSchema):
    """Full desired state of one question, options included — on update the
    option list is replaced wholesale (simpler than a per-option diff)."""

    question_type: str = "MULTIPLE_CHOICE"
    passage_text: str | None = None
    prompt: str
    order_index: int
    points: float = 5
    is_active: bool = True
    options: list[VizuMultilevelOptionInput]

    @field_validator("question_type")
    @classmethod
    def _type(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in ALL_QUESTION_TYPES:
            raise ValueError(f"question_type must be one of {', '.join(sorted(ALL_QUESTION_TYPES))}")
        return value

    @field_validator("points")
    @classmethod
    def _points(cls, value: float) -> float:
        if value < 0:
            raise ValueError("points must not be negative")
        return value

    @model_validator(mode="after")
    def _options(self):
        if len(self.options) < 2:
            raise ValueError("a question needs at least 2 options")
        if sum(1 for o in self.options if o.is_correct) != 1:
            raise ValueError("exactly one option must be marked correct")
        if any(not o.option_text.strip() for o in self.options):
            raise ValueError("option text must not be empty")
        return self
