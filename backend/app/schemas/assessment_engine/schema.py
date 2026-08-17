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
    "WRITING",
    "SPEAKING",
]
AttemptStatus = Literal["IN_PROGRESS", "SUBMITTED", "GRADED"]
EvaluationMode = Literal["AI_ONLY", "TEACHER_ONLY", "AI_AND_TEACHER"]
WritingSubmissionStatus = Literal["DRAFT", "SUBMITTED", "PENDING_REVIEW", "GRADED"]
EvaluatorType = Literal["AI", "TEACHER"]
SpeakingSubmissionStatus = Literal["PENDING_REVIEW", "REVIEWED", "FINAL"]


# ============================================================
# Assessment
# ============================================================

class AssessmentCreate(BaseSchema):
    title: str
    description: str | None = None
    assessment_type: AssessmentType
    lesson_id: str | None = None
    model_test_id: str | None = None
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
    model_test_id: str | None = None
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
    model_test_id: UUID | None
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
# Writing rubric criterion (SCHREIBEN) — configurable, never hardcoded
# ============================================================

class WritingRubricCriterionCreate(BaseSchema):
    # Optional — injected from the URL path (POST /tasks/{task_id}/rubric-criteria).
    task_id: str | None = None
    name: str
    max_score: int = 5
    sort_order: int = 1


class WritingRubricCriterionUpdate(BaseSchema):
    name: str | None = None
    max_score: int | None = None
    sort_order: int | None = None


class WritingRubricCriterionResponse(BaseSchema):
    id: UUID
    task_id: UUID
    name: str
    max_score: int
    sort_order: int

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
    status: AssessmentStatus = "DRAFT"
    # Audio play policy — only meaningful for HOEREN tasks; harmless
    # defaults for every other type, which simply never has audio attached.
    audio_play_limit: int | None = None
    allow_pause: bool = True
    allow_seek: bool = True
    allow_replay: bool = True
    allow_speed_change: bool = True
    # Writing config — only meaningful for WRITING tasks.
    image_url: str | None = None
    min_words: int | None = None
    max_words: int | None = None
    time_limit_minutes: int | None = None
    evaluation_mode: EvaluationMode = "AI_ONLY"
    # Speaking config — only meaningful for SPEAKING tasks.
    prep_seconds: int | None = None
    speak_seconds: int | None = None


class AssessmentTaskUpdate(BaseSchema):
    title: str | None = None
    instructions: str | None = None
    content: str | None = None
    config: str | None = None
    max_points: int | None = None
    sort_order: int | None = None
    status: AssessmentStatus | None = None
    audio_play_limit: int | None = None
    allow_pause: bool | None = None
    allow_seek: bool | None = None
    allow_replay: bool | None = None
    allow_speed_change: bool | None = None
    image_url: str | None = None
    min_words: int | None = None
    max_words: int | None = None
    time_limit_minutes: int | None = None
    evaluation_mode: EvaluationMode | None = None
    prep_seconds: int | None = None
    speak_seconds: int | None = None


class TaskReorderRequest(BaseSchema):
    # Full ordered list of task ids for the section — position in this
    # list becomes the new sort_order, explicit rather than inferred.
    task_ids: list[str]


class TaskAudioResponse(BaseSchema):
    id: UUID
    task_id: UUID
    filename: str
    format: str
    duration_seconds: int | None
    file_size_bytes: int

    model_config = ConfigDict(from_attributes=True, extra="ignore")


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
    status: str
    audio_play_limit: int | None
    allow_pause: bool
    allow_seek: bool
    allow_replay: bool
    allow_speed_change: bool
    image_url: str | None
    min_words: int | None
    max_words: int | None
    time_limit_minutes: int | None
    evaluation_mode: str
    prep_seconds: int | None
    speak_seconds: int | None
    audio: TaskAudioResponse | None = None
    questions: list[TaskQuestionResponse] = Field(default_factory=list)
    rubric_criteria: list[WritingRubricCriterionResponse] = Field(default_factory=list)

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


class PublicWritingRubricCriterion(BaseSchema):
    id: UUID
    name: str
    max_score: int
    sort_order: int


class PublicAssessmentTask(BaseSchema):
    id: UUID
    task_type: str
    title: str
    instructions: str | None
    content: str | None
    config: str | None
    max_points: int
    sort_order: int
    # Audio is never a direct URL here — only enough for the player to
    # decide whether to render itself and how to behave. The actual
    # bytes are fetched from GET /audio/{task_id}, which re-checks
    # permission on every request; nothing here is a capability by itself.
    has_audio: bool = False
    audio_duration_seconds: int | None = None
    audio_play_limit: int | None = None
    allow_pause: bool = True
    allow_seek: bool = True
    allow_replay: bool = True
    allow_speed_change: bool = True
    # Writing (SCHREIBEN) — the rubric's criteria/max-scores are
    # descriptive, not a "correct answer", so they're safe to expose here
    # (a student seeing "Grammatik: /5" doesn't leak anything gradeable).
    image_url: str | None = None
    min_words: int | None = None
    max_words: int | None = None
    time_limit_minutes: int | None = None
    prep_seconds: int | None = None
    speak_seconds: int | None = None
    rubric_criteria: list[PublicWritingRubricCriterion] = Field(default_factory=list)
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
    # Exposed so the client can correctly gray out editing controls (e.g.
    # the Schreiben two-pane editor) — the backend is still the real
    # enforcement point on every write endpoint regardless of what the UI
    # shows.
    allow_edit: bool = True
    allow_resubmit: bool = False
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


class AudioPlayStatusResponse(BaseSchema):
    task_id: str
    play_limit: int | None
    plays_used: int
    plays_remaining: int | None
    can_play: bool
    allow_pause: bool
    allow_seek: bool
    allow_replay: bool
    allow_speed_change: bool


# ============================================================
# Writing (SCHREIBEN) submissions / evaluations
# ============================================================

class WritingSubmissionSave(BaseSchema):
    """Body for both Speichern (draft) and Abgeben (submit) — the router
    endpoint (not this schema) decides which status transition happens."""
    content: str


class WritingSubmissionResponse(BaseSchema):
    id: UUID
    user_id: UUID
    assessment_id: UUID
    section_id: UUID
    task_id: UUID
    attempt_id: UUID
    content: str
    word_count: int
    character_count: int
    status: WritingSubmissionStatus
    submitted_at: datetime | None
    final_score: int | None
    notified: bool = False

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class WritingEvaluationResponse(BaseSchema):
    id: UUID
    submission_id: UUID
    evaluator_type: EvaluatorType
    reviewed_by_id: UUID | None
    rubric_scores: dict[str, int] = Field(default_factory=dict)
    total_score: int
    feedback: str | None
    strengths: str | None
    errors: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class WritingResultResponse(BaseSchema):
    """The student-facing 'Ergebnisse -> Schreiben' payload — submission
    plus whichever evaluations exist. feedback/rubric are omitted
    server-side (not just hidden client-side) when the assessment's
    show_feedback policy is off."""
    submission: WritingSubmissionResponse
    evaluations: list[WritingEvaluationResponse] = Field(default_factory=list)
    show_feedback: bool


class TeacherReviewInput(BaseSchema):
    """Rubric scores keyed by WritingRubricCriterion id (as a string) —
    validated server-side against each criterion's max_score and the
    task's max_points; never trusted as-is."""
    rubric_scores: dict[str, int]
    feedback: str | None = None


class PendingWritingReviewItem(BaseSchema):
    """One row in the teacher's review queue."""
    submission: WritingSubmissionResponse
    task_title: str
    student_name: str
    lesson_title: str = ""
    level: str = "A1"
    skill: str = "SCHREIBEN"
    rubric_criteria: list[WritingRubricCriterionResponse] = Field(default_factory=list)
    ai_evaluation: WritingEvaluationResponse | None = None


# ============================================================
# Speaking (SPRECHEN) submissions / evaluations
# ============================================================

class SpeakingSubmissionResponse(BaseSchema):
    id: UUID
    user_id: UUID
    assessment_id: UUID
    section_id: UUID
    task_id: UUID
    attempt_id: UUID
    filename: str
    format: str
    duration_seconds: int | None
    file_size_bytes: int
    status: SpeakingSubmissionStatus
    submitted_at: datetime
    final_score: int | None
    notified: bool = False

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class SpeakingEvaluationResponse(BaseSchema):
    id: UUID
    submission_id: UUID
    reviewed_by_id: UUID | None
    rubric_scores: dict[str, int] = Field(default_factory=dict)
    total_score: int
    feedback: str | None
    has_audio_feedback: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class SpeakingResultResponse(BaseSchema):
    submission: SpeakingSubmissionResponse
    evaluations: list[SpeakingEvaluationResponse] = Field(default_factory=list)
    show_feedback: bool


class SpeakingReviewInput(BaseSchema):
    rubric_scores: dict[str, int]
    feedback: str | None = None
    # False -> saves as REVIEWED (teacher can come back and adjust later);
    # True -> FINAL, locks it in and folds the score into the attempt result.
    finalize: bool = True


class PendingSpeakingReviewItem(BaseSchema):
    submission: SpeakingSubmissionResponse
    task_title: str
    student_name: str
    lesson_title: str = ""
    level: str = "A1"
    skill: str = "SPRECHEN"
    rubric_criteria: list[WritingRubricCriterionResponse] = Field(default_factory=list)
