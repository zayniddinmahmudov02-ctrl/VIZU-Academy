from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class ReadingQuestionBase(BaseSchema):

    reading_id: UUID

    question: str

    explanation: str | None = None

    order_index: int = 1

    is_published: bool = False


class ReadingQuestionCreate(ReadingQuestionBase):
    pass


class ReadingQuestionUpdate(BaseSchema):

    question: str | None = None

    explanation: str | None = None

    order_index: int | None = None

    is_published: bool | None = None


class ReadingQuestionResponse(ReadingQuestionBase):

    id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )
