from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class SpeakingBase(BaseSchema):
    lesson_id: UUID

    title: str

    topic: str

    instruction: str

    sample_answer: str | None = None

    keywords: str | None = None

    preparation_time: int = 15

    speaking_time: int = 90

    order_index: int = 1

    is_published: bool = False


class SpeakingCreate(SpeakingBase):
    pass


class SpeakingUpdate(BaseSchema):
    title: str | None = None

    topic: str | None = None

    instruction: str | None = None

    sample_answer: str | None = None

    keywords: str | None = None

    preparation_time: int | None = None

    speaking_time: int | None = None

    order_index: int | None = None

    is_published: bool | None = None


class SpeakingResponse(SpeakingBase):
    id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )