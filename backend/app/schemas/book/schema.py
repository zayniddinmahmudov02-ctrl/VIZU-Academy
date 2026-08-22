from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class BookBase(BaseSchema):
    title: str
    author: str | None = None
    description: str | None = None
    level: str
    order_index: int = 1
    is_published: bool = False


class BookCreate(BookBase):
    pass


class BookUpdate(BaseSchema):
    title: str | None = None
    author: str | None = None
    description: str | None = None
    level: str | None = None
    order_index: int | None = None
    is_published: bool | None = None


class BookResponse(BookBase):
    """Admin-only shape — includes storage_key, since this is only ever
    returned from admin-authenticated endpoints. Students get
    BookPublicResponse instead, which never includes it."""

    id: UUID
    cover_url: str | None = None
    storage_key: str | None = None
    original_filename: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BookPublicResponse(BaseSchema):
    """Student-facing shape — no storage_key or any other internal
    field. The PDF itself is only ever fetched through the separate,
    access-checked GET /books/{id}/file endpoint."""

    id: UUID
    title: str
    author: str | None = None
    description: str | None = None
    level: str
    cover_url: str | None = None
    order_index: int = 1

    model_config = ConfigDict(from_attributes=True)
