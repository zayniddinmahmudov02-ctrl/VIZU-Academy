from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field

from app.schemas.base import BaseSchema

AssessmentType = Literal["COURSE", "PREPARATION", "MOCK_TEST"]
AssessmentStatus = Literal["DRAFT", "PUBLISHED", "ARCHIVED"]
SectionSkill = Literal["LESEN", "HOEREN", "SCHREIBEN", "SPRECHEN"]
TaskType = Literal[
    "TRUE_FALSE",
    "MULTIPLE_CHOICE",
    "MULTIPLE_SELECT",
    "CLOZE_TEXT",
    "HEADING_MATCHING",
    "ADVERTISEMENT_MATCHING",
    "TEXT_MATCHING",
    "SENTENCE_ORDERING",
    "SHORT_ANSWER",
    "GAP_MATCHING",
    "DRAG_DROP",
    "CATEGORY_SORTING",
    "IMAGE_SELECTION",
]
AttemptStatus = Literal["IN_PROGRESS", "SUBMITTED", "GRADED"]


# ============================================================
# Assessment
# ============================================================

class AssessmentCreate(BaseSchema):
    title: str
    description: str | None = None
    assessment_type: AssessmentType
    lesson_id: str | None = None
    language_id: str | None = None
    level: str | None = None
    attempt_limit: int | None = None
    allow_retry: bool = True
    allow_edit: bool = True
    allow_resubmit: bool = False
    show_correct_answers: bool = True
    show_score: bool = True
    show_feedback: bool = True


class AssessmentUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    status: AssessmentStatus | None = None
    lesson_id: str | None = None
    language_id: str | None = None
    level: str | None = None
    attempt_limit: int | None = None
    allow_retry: bool | None = None
    allow_edit: bool | None = None
    allow_resubmit: bool | None = None
    show_correct_answers: bool | None = None
    show_score: bool | None = None
    show_feedback: bool | None = None


class AssessmentResponse(BaseSchema):
    id: UUID
    title: str
    description: str | None
    assessment_type: str
    status: str
    lesson_id: UUID | None
    language_id: UUID | None
    level: str | None
    attempt_limit: int | None
    allow_retry: bool
    allow_edit: bool
    allow_resubmit: bool
    show_correct_answers: bool
    show_score: bool
    show_feedback: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="ignore")


# ============================================================
# Section
# ============================================================

class AssessmentSectionCreate(BaseSchema):
    # Optional here because the router injects it from the URL path
    # (POST /assessments/{assessment_id}/sections) — the request body
    # itself never needs to repeat it.
    assessment_id: str | None = None
    skill: SectionSkill
    title: str
    instructions: str | None = None
    sort_order: int = 1


class AssessmentSectionUpdate(BaseSchema):
    skill: SectionSkill | None = None
    title: str | None = None
    instructions: str | None = None
    sort_order: int | None = None


class AssessmentSectionResponse(BaseSchema):
    id: UUID
    assessment_id: UUID
    skill: str
    title: str
    instructions: str | None
    sort_order: int

    model_config = ConfigDict(from_attributes=True, extra="ignore")


# ============================================================
# Task Option
# ============================================================

class TaskOptionCreate(BaseSchema):
    # Optional — injected from the URL path (POST /questions/{question_id}/options).
    question_id: str | None = None
    option_text: str
    match_value: str | None = None
    is_correct: bool = False
    sort_order: int = 1


class TaskOptionUpdate(BaseSchema):
    option_text: str | None = None
    match_value: str | None = None
    is_correct: bool | None = None
    sort_order: int | None = None


class TaskOptionResponse(BaseSchema):
    id: UUID
    question_id: UUID
    option_text: str
    match_value: str | None
    is_correct: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True, extra="ignore")


# ============================================================
# Task Question
# ============================================================

class TaskQuestionCreate(BaseSchema):
    # Optional — injected from the URL path (POST /tasks/{task_id}/questions).
    task_id: str | None = None
    prompt: str = ""
    correct_text_answer: str | None = None
    alternative_answers: str | None = None
    case_sensitive: bool = False
    points: int = 1
    sort_order: int = 1


class TaskQuestionUpdate(BaseSchema):
    prompt: str | None = None
    correct_text_answer: str | None = None
    alternative_answers: str | None = None
    case_sensitive: bool | None = None
    points: int | None = None
    sort_order: int | None = None


class TaskQuestionResponse(BaseSchema):
    id: UUID
    task_id: UUID
    prompt: str
    correct_text_answer: str | None
    alternative_answers: str | None
    case_sensitive: bool
    points: int
    sort_order: int
    options: list[TaskOptionResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, extra="ignore")


# ============================================================
# Task
# ============================================================

class AssessmentTaskCreate(BaseSchema):
    # Optional — injected from the URL path (POST /sections/{section_id}/tasks).
    section_id: str | None = None
    task_type: TaskType
    title: str = ""
    instructions: str | None = None
    content: str | None = None
    config: str | None = None
    max_points: int = 0
    sort_order: int = 1


class AssessmentTaskUpdate(BaseSchema):
    title: str | None = None
    instructions: str | None = None
    content: str | None = None
    config: str | None = None
    max_points: int | None = None
    sort_order: int | None = None


class AssessmentTaskResponse(BaseSchema):
    id: UUID
    section_id: UUID
    task_type: str
    title: str
    instructions: str | None
    content: str | None
    config: str | None
    max_points: int
    sort_order: int
    questions: list[TaskQuestionResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class TaskValidationResponse(BaseSchema):
    task_id: str
    is_publishable: bool
    errors: list[str]


class AssessmentSectionWithTasks(AssessmentSectionResponse):
    tasks: list[AssessmentTaskResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class AssessmentFullResponse(AssessmentResponse):
    """AssessmentResponse plus every section -> task -> question -> option
    eagerly nested — for the builder UI (one request instead of a
    waterfall)."""

    sections: list[AssessmentSectionWithTasks] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, extra="ignore")


# ============================================================
# Public (student-facing) — never includes correct-answer data
# ============================================================

class PublicTaskOption(BaseSchema):
    id: UUID
    option_text: str
    sort_order: int


class PublicTaskQuestion(BaseSchema):
    id: UUID
    prompt: str
    points: int
    sort_order: int
    options: list[PublicTaskOption] = Field(default_factory=list)


class PublicAssessmentTask(BaseSchema):
    id: UUID
    task_type: str
    title: str
    instructions: str | None
    content: str | None
    config: str | None
    max_points: int
    sort_order: int
    questions: list[PublicTaskQuestion] = Field(default_factory=list)


class PublicAssessmentSection(BaseSchema):
    id: UUID
    skill: str
    title: str
    instructions: str | None
    sort_order: int
    tasks: list[PublicAssessmentTask] = Field(default_factory=list)


class PublicAssessment(BaseSchema):
    id: UUID
    title: str
    description: str | None
    sections: list[PublicAssessmentSection] = Field(default_factory=list)


# ============================================================
# Attempts / Answers / Results
# ============================================================

class AssessmentAttemptCreate(BaseSchema):
    assessment_id: str


class AssessmentAttemptResponse(BaseSchema):
    id: UUID
    assessment_id: UUID
    user_id: UUID
    status: str
    attempt_number: int
    locked: bool
    started_at: datetime
    submitted_at: datetime | None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class AnswerSubmit(BaseSchema):
    question_id: str
    answer_data: str


class AnswerResponse(BaseSchema):
    id: UUID
    question_id: UUID
    answer_data: str | None
    is_correct: bool | None
    points_earned: int

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class SectionResultResponse(BaseSchema):
    section_id: UUID
    section_score: int
    max_section_score: int
    percentage: float

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class AssessmentResultResponse(BaseSchema):
    attempt_id: str
    total_score: int
    max_score: int
    percentage: float
    section_results: list[SectionResultResponse]
    show_correct_answers: bool
    show_feedback: bool
