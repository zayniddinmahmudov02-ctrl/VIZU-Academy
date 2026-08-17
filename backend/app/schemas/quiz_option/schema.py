from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class QuizOptionBase(BaseSchema):
    question_id: UUID
    option_text: str
    is_correct: bool = False
    order_index: int = 1
    match_value: str | None = None


class QuizOptionCreate(QuizOptionBase):
    pass


class QuizOptionUpdate(BaseSchema):
    option_text: str | None = None
    is_correct: bool | None = None
    order_index: int | None = None
    match_value: str | None = None


class QuizOptionResponse(QuizOptionBase):
    id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )
