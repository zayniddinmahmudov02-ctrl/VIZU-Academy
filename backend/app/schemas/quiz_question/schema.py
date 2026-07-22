from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class QuizQuestionBase(BaseSchema):
    quiz_id: str
    question: str
    explanation: str | None = None
    points: int = 1
    order_index: int = 1
    is_published: bool = False


class QuizQuestionCreate(QuizQuestionBase):
    pass


class QuizQuestionUpdate(BaseSchema):
    question: str | None = None
    explanation: str | None = None
    points: int | None = None
    order_index: int | None = None
    is_published: bool | None = None


class QuizQuestionResponse(QuizQuestionBase):
    id: str

    model_config = ConfigDict(
        from_attributes=True,
    )