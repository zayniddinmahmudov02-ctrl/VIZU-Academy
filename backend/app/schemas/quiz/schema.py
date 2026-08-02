from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class QuizBase(BaseSchema):
    lesson_id: UUID
    title: str
    description: str | None = None
    passing_score: int = 70
    order_index: int = 1
    is_published: bool = False


class QuizCreate(QuizBase):
    pass


class QuizUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    passing_score: int | None = None
    order_index: int | None = None
    is_published: bool | None = None


class QuizResponse(QuizBase):
    id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )
