from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseSchema


class VizuMultilevelSpeakingTaskPublic(BaseSchema):
    """No `level` — backend/admin-side scoring data, never shown to the student."""

    id: UUID
    order_index: int
    title: str
    instruction: str
    preparation_text: str | None
    prep_seconds: int
    max_seconds: int
    points: int


class VizuMultilevelSpeakingSubmissionPublic(BaseSchema):
    id: UUID
    task_id: UUID
    duration_seconds: int | None
    submitted_at: datetime | None


class VizuMultilevelSpeakingSubmitAllResponse(BaseSchema):
    attempt_id: UUID
    sprechen_submitted_at: datetime


# ---- Admin ----


class VizuMultilevelSpeakingTaskAdminCreate(BaseSchema):
    level: str
    order_index: int
    title: str
    instruction: str
    preparation_text: str | None = None
    prep_seconds: int = 0
    max_seconds: int = 120
    points: int = 20
    is_active: bool = True


class VizuMultilevelSpeakingTaskAdminUpdate(BaseSchema):
    level: str | None = None
    order_index: int | None = None
    title: str | None = None
    instruction: str | None = None
    preparation_text: str | None = None
    prep_seconds: int | None = None
    max_seconds: int | None = None
    points: int | None = None
    is_active: bool | None = None


class VizuMultilevelSpeakingTaskAdminResponse(BaseSchema):
    id: UUID
    level: str
    order_index: int
    title: str
    instruction: str
    preparation_text: str | None
    prep_seconds: int
    max_seconds: int
    points: int
    is_active: bool


# ---- Teacher ----


class VizuMultilevelTeacherSpeakingListItem(BaseSchema):
    attempt_id: UUID
    student_name: str
    username: str
    email: str
    sprechen_submitted_at: datetime
    graded_count: int
    total_submissions: int
    sprechen_score: int | None
    max_score: int
    status: str  # NEW / IN_PROGRESS / GRADED


class VizuMultilevelTeacherSpeakingSubmissionDetail(BaseSchema):
    submission_id: UUID | None
    task_id: UUID
    order_index: int
    level: str
    title: str
    instruction: str
    points: int
    duration_seconds: int | None
    has_audio: bool
    teacher_score: int | None
    teacher_comment: str | None


class VizuMultilevelTeacherSpeakingDetail(BaseSchema):
    attempt_id: UUID
    student_name: str
    username: str
    email: str
    sprechen_submitted_at: datetime
    sprechen_score: int | None
    sprechen_level: str | None
    sprechen_feedback: str | None
    submissions: list[VizuMultilevelTeacherSpeakingSubmissionDetail]


class VizuMultilevelTeacherSpeakingGradeRequest(BaseSchema):
    score: int
    comment: str | None = None


class VizuMultilevelTeacherSpeakingFeedbackRequest(BaseSchema):
    sprechen_feedback: str | None
