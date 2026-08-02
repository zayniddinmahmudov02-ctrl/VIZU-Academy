from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class HomeworkBase(BaseSchema):
    lesson_id: UUID
    title: str
    description: str
    max_score: int = 100
    is_published: bool = False


class HomeworkCreate(HomeworkBase):
    pass


class HomeworkUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    max_score: int | None = None
    is_published: bool | None = None


class HomeworkResponse(HomeworkBase):
    id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )
