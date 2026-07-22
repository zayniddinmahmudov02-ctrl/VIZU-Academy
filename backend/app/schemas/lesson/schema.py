from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LessonBase(BaseModel):
    module_id: UUID
    number: int
    title: str
    duration: int
    is_free: bool = False
    video_url: str | None = None


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    number: int | None = None
    title: str | None = None
    duration: int | None = None
    is_free: bool | None = None
    video_url: str | None = None


class LessonResponse(LessonBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class LessonListItem(BaseModel):
    id: str
    module_id: str
    number: int
    title: str
    duration: int
    video_url: str | None
    is_free: bool
    progress: int


class LessonDetail(LessonListItem):
    audio_url: str | None
