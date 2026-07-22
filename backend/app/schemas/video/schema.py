from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class VideoBase(BaseSchema):
    title: str
    description: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None
    duration_seconds: int = 0
    order_index: int = 1
    is_preview: bool = False
    is_published: bool = False


class VideoCreate(VideoBase):
    lesson_id: UUID


class VideoUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None
    duration_seconds: int | None = None
    order_index: int | None = None
    is_preview: bool | None = None
    is_published: bool | None = None


class VideoResponse(VideoBase):
    id: UUID
    lesson_id: UUID

    # R2 object key — fine to surface here since VideoResponse is only
    # ever returned from admin-authenticated endpoints. The student
    # streaming endpoint (GET /videos/{id}) returns VideoStreamResponse
    # instead, which never includes this field.
    storage_key: str | None = None

    model_config = ConfigDict(from_attributes=True)


class VideoStreamResponse(BaseSchema):
    """The only shape ever returned to a student for playback. A
    short-lived (5 minute) presigned R2 URL — never the storage_key, a
    permanent URL, or any other video metadata."""

    video_url: str
