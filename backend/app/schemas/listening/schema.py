from uuid import UUID

from pydantic import ConfigDict, Field

from app.schemas.base import BaseSchema


class ListeningBase(BaseSchema):
    lesson_id: UUID
    title: str
    # Legacy external URL; new tasks upload the audio (POST
    # /admin/lesson-skills/listenings/{id}/audio) — stored privately.
    audio_url: str | None = None
    transcript: str | None = None
    instruction: str | None = Field(default=None, max_length=5000)
    order_index: int = 1
    is_published: bool = False
    content_id: str | None = Field(default=None, max_length=120)


class ListeningCreate(ListeningBase):
    pass


class ListeningUpdate(BaseSchema):
    title: str | None = None
    audio_url: str | None = None
    transcript: str | None = None
    instruction: str | None = Field(default=None, max_length=5000)
    order_index: int | None = None
    is_published: bool | None = None


class ListeningResponse(ListeningBase):
    id: UUID
    has_uploaded_audio: bool = False
    audio_duration_seconds: int | None = None
    audio_content_type: str | None = None
    audio_original_name: str | None = None
    question_count: int = 0

    model_config = ConfigDict(from_attributes=True)
