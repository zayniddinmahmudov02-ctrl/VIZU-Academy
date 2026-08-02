from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class ListeningBase(BaseSchema):
    lesson_id: UUID
    title: str
    audio_url: str
    transcript: str | None = None
    order_index: int = 1
    is_published: bool = False


class ListeningCreate(ListeningBase):
    pass


class ListeningUpdate(BaseSchema):
    title: str | None = None
    audio_url: str | None = None
    transcript: str | None = None
    order_index: int | None = None
    is_published: bool | None = None


class ListeningResponse(ListeningBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
