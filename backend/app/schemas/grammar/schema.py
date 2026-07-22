from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class GrammarBase(BaseSchema):
    lesson_id: str
    title: str
    content: str
    video_url: str | None = None
    order_index: int = 1
    is_published: bool = False


class GrammarCreate(GrammarBase):
    pass


class GrammarUpdate(BaseSchema):
    title: str | None = None
    content: str | None = None
    video_url: str | None = None
    order_index: int | None = None
    is_published: bool | None = None


class GrammarResponse(GrammarBase):
    id: str

    model_config = ConfigDict(from_attributes=True)