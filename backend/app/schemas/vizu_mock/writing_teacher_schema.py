from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseSchema

from .writing_admin_schema import VizuMockWritingRubricCriterionResponse


class VizuMockTeacherWritingListItem(BaseSchema):
    attempt_id: UUID
    student_name: str
    username: str
    email: str
    schreiben_submitted_at: datetime
    graded_count: int
    total_tasks: int
    schreiben_score: int | None
    max_score: int
    # NEW = submitted, nothing graded yet; IN_PROGRESS = some but not all
    # 5 Aufgabe graded; GRADED = all 5 graded — computed, never stored.
    status: str


class VizuMockTeacherWritingSubmissionDetail(BaseSchema):
    task_id: UUID
    order_index: int
    level: str
    title: str
    instruction: str
    min_words: int
    max_words: int
    image_url: str | None
    content: str
    word_count: int
    rubric_criteria: list[VizuMockWritingRubricCriterionResponse]
    # criterion id (as string) -> assigned score; empty until graded.
    criterion_scores: dict[str, int]
    teacher_score: int | None
    teacher_comment: str | None


class VizuMockTeacherWritingDetail(BaseSchema):
    attempt_id: UUID
    student_name: str
    username: str
    email: str
    schreiben_submitted_at: datetime
    schreiben_score: int | None
    schreiben_level: str | None
    schreiben_feedback: str | None
    submissions: list[VizuMockTeacherWritingSubmissionDetail]


class VizuMockTeacherGradeTaskRequest(BaseSchema):
    criterion_scores: dict[UUID, int]
    comment: str | None = None


class VizuMockTeacherFeedbackRequest(BaseSchema):
    schreiben_feedback: str | None
