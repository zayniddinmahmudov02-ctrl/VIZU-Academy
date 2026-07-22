from uuid import UUID

from pydantic import BaseModel, ConfigDict


class VideoBase(BaseModel):
    title: str
    description: str | None = None
    video_url: str
    thumbnail_url: str | None = None
    duration_seconds: int = 0
    order_index: int = 1
    is_published: bool = False


class VideoCreate(VideoBase):
    lesson_id: UUID


class VideoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None
    duration_seconds: int | None = None
    order_index: int | None = None
    is_published: bool | None = None


class VideoResponse(VideoBase):
    id: UUID
    lesson_id: UUID

    model_config = ConfigDict(from_attributes=True)