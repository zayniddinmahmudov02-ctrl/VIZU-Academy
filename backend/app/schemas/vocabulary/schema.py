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


# ==========================
# Bulk generator
# ==========================


class BulkAnalyzeRequest(BaseSchema):
    lesson_id: UUID
    words: list[str]
    auto_complete: bool = True


class BulkSaveItem(BaseSchema):
    german_word: str
    article: str | None = None
    plural: str | None = None
    translation: str
    example_sentence: str | None = None
    example_translation: str | None = None
    is_published: bool = False
    # Admin's explicit choice for a row flagged is_duplicate during
    # preview — "Überspringen" (skip=True) or "Als neues Wort erstellen"
    # (force_duplicate=True). Neither set = server re-checks and refuses.
    skip: bool = False
    force_duplicate: bool = False


class BulkSaveRequest(BaseSchema):
    lesson_id: UUID
    items: list[BulkSaveItem]


class BulkSaveNeedsReview(BaseSchema):
    word: str
    reason: str


class BulkSaveResponse(BaseSchema):
    saved_count: int
    needs_review: list[BulkSaveNeedsReview]


# ==========================
# Bulk delete
# ==========================


class BulkDeleteRequest(BaseSchema):
    lesson_id: UUID
    vocabulary_ids: list[UUID]


class BulkDeleteResponse(BaseSchema):
    deleted_count: int
