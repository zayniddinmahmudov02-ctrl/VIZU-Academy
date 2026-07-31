from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class VideoProgressResponse(BaseSchema):
    video_id: UUID
    lesson_id: UUID
    last_position: int
    watch_percent: int
    completed: bool

    model_config = ConfigDict(from_attributes=True)


class VideoProgressUpdateRequest(BaseSchema):
    video_id: UUID
    position: int
    ended: bool = False


class VideoProgressCompleteRequest(BaseSchema):
    video_id: UUID
    ended: bool = False
