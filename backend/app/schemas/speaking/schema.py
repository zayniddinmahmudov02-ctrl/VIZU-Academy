from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class SpeakingBase(BaseSchema):
    lesson_id: UUID

    title: str

    instruction: str

    sample_answer: str | None = None

    max_score: int = 100

    order_index: int = 1

    is_published: bool = False


class SpeakingCreate(SpeakingBase):
    pass


class SpeakingUpdate(BaseSchema):
    title: str | None = None

    instruction: str | None = None

    sample_answer: str | None = None

    max_score: int | None = None

    order_index: int | None = None

    is_published: bool | None = None


class SpeakingResponse(SpeakingBase):
    id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )