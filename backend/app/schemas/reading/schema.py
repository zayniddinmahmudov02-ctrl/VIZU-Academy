from uuid import UUID

from pydantic import ConfigDict, field_validator

from app.core.utils.safe_html import sanitize_html

from app.schemas.base import BaseSchema


class ReadingBase(BaseSchema):
    title: str
    content: str

    order_index: int = 1
    is_published: bool = False
    image_url: str | None = None
    content_id: str | None = None


class ReadingCreate(ReadingBase):
    lesson_id: UUID

    # rendered as HTML for students -> only simple formatting tags survive
    _safe_content = field_validator("content")(classmethod(lambda cls, v: sanitize_html(v)))


class ReadingUpdate(BaseSchema):
    title: str | None = None
    content: str | None = None

    order_index: int | None = None
    is_published: bool | None = None
    image_url: str | None = None

    _safe_content = field_validator("content")(classmethod(lambda cls, v: sanitize_html(v)))


class ReadingResponse(ReadingBase):
    id: UUID
    lesson_id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )