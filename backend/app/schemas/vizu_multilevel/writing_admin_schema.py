from uuid import UUID

from app.schemas.base import BaseSchema


class VizuMultilevelWritingRubricCriterionInput(BaseSchema):
    """`id` is None for a brand-new criterion; when set, the admin
    service updates that existing row in place instead of recreating it.
    On every task update, the full desired rubric list is sent and the
    service reconciles it (delete-missing / update-existing / create-
    new) — simpler and less error-prone than a partial diff endpoint."""

    id: UUID | None = None
    name: str
    max_score: int
    order_index: int = 1


class VizuMultilevelWritingRubricCriterionResponse(BaseSchema):
    id: UUID
    name: str
    max_score: int
    order_index: int


class VizuMultilevelWritingTaskAdminCreate(BaseSchema):
    level: str
    order_index: int
    title: str
    instruction: str
    min_words: int
    max_words: int
    image_url: str | None = None
    points: int = 20
    is_active: bool = True
    rubric_criteria: list[VizuMultilevelWritingRubricCriterionInput] = []


class VizuMultilevelWritingTaskAdminUpdate(BaseSchema):
    level: str | None = None
    order_index: int | None = None
    title: str | None = None
    instruction: str | None = None
    min_words: int | None = None
    max_words: int | None = None
    image_url: str | None = None
    points: int | None = None
    is_active: bool | None = None
    # None = leave the rubric untouched; [] = clear it; a list = replace
    # it wholesale (see VizuMultilevelWritingRubricCriterionInput's docstring).
    rubric_criteria: list[VizuMultilevelWritingRubricCriterionInput] | None = None


class VizuMultilevelWritingTaskAdminResponse(BaseSchema):
    id: UUID
    level: str
    order_index: int
    title: str
    instruction: str
    min_words: int
    max_words: int
    image_url: str | None
    points: int
    is_active: bool
    rubric_criteria: list[VizuMultilevelWritingRubricCriterionResponse]
