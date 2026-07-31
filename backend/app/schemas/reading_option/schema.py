from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class ReadingOptionBase(BaseSchema):

    question_id: str

    option_text: str

    is_correct: bool = False

    order_index: int = 1


class ReadingOptionCreate(ReadingOptionBase):
    pass


class ReadingOptionUpdate(BaseSchema):

    option_text: str | None = None

    is_correct: bool | None = None

    order_index: int | None = None


class ReadingOptionResponse(ReadingOptionBase):

    id: str

    model_config = ConfigDict(
        from_attributes=True,
    )