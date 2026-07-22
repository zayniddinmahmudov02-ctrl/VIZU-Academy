from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class ReadingBase(BaseSchema):
    title: str
    content: str

    order_index: int = 1
    is_published: bool = False


class ReadingCreate(ReadingBase):
    lesson_id: UUID


class ReadingUpdate(BaseSchema):
    title: str | None = None
    content: str | None = None

    order_index: int | None = None
    is_published: bool | None = None


class ReadingResponse(ReadingBase):
    id: UUID
    lesson_id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )