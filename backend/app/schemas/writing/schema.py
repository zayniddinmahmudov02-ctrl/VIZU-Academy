from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class WritingBase(BaseSchema):
    lesson_id: str
    title: str
    instruction: str
    min_words: int = 30
    max_words: int = 150
    order_index: int = 1
    is_published: bool = False


class WritingCreate(WritingBase):
    pass


class WritingUpdate(BaseSchema):
    title: str | None = None
    instruction: str | None = None
    min_words: int | None = None
    max_words: int | None = None
    order_index: int | None = None
    is_published: bool | None = None


class WritingResponse(WritingBase):
    id: str

    model_config = ConfigDict(from_attributes=True)