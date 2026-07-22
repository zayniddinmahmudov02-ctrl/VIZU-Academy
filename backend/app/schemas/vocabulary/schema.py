from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class VocabularyBase(BaseSchema):
    german_word: str
    article: str | None = None
    plural: str | None = None
    translation: str

    example_sentence: str | None = None
    example_translation: str | None = None

    audio_url: str | None = None
    image_url: str | None = None

    order_index: int = 1
    is_published: bool = False


class VocabularyCreate(VocabularyBase):
    lesson_id: UUID


class VocabularyUpdate(BaseSchema):
    german_word: str | None = None
    article: str | None = None
    plural: str | None = None
    translation: str | None = None

    example_sentence: str | None = None
    example_translation: str | None = None

    audio_url: str | None = None
    image_url: str | None = None

    order_index: int | None = None
    is_published: bool | None = None


class VocabularyResponse(VocabularyBase):
    id: UUID
    lesson_id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )