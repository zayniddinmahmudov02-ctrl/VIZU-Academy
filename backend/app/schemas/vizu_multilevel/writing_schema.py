from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseSchema


class VizuMultilevelWritingTaskPublic(BaseSchema):
    """Never includes the rubric — that's teacher-only grading metadata,
    not something a student needs (or should see) while answering."""

    id: UUID
    order_index: int
    title: str
    instruction: str
    min_words: int
    max_words: int
    image_url: str | None
    points: int


class VizuMultilevelWritingSubmissionPublic(BaseSchema):
    task_id: UUID
    content: str
    word_count: int
    status: str


class VizuMultilevelWritingSaveRequest(BaseSchema):
    task_id: UUID
    content: str


class VizuMultilevelWritingSubmitAllResponse(BaseSchema):
    attempt_id: UUID
    schreiben_submitted_at: datetime
