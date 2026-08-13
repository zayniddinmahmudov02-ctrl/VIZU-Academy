from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema

# ============================================================
# Certification Provider (Goethe, TELC, ÖSD, ...)
# ============================================================


class CertificationProviderBase(BaseSchema):
    name: str
    code: str
    logo_url: str | None = None
    description: str | None = None
    color: str | None = None
    is_active: bool = True
    sort_order: int = 1


class CertificationProviderCreate(CertificationProviderBase):
    pass


class CertificationProviderUpdate(BaseSchema):
    name: str | None = None
    code: str | None = None
    logo_url: str | None = None
    description: str | None = None
    color: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class CertificationProviderResponse(CertificationProviderBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Mock Exam Level (A1-C2 within a provider)
# ============================================================


class MockExamLevelBase(BaseSchema):
    level: str
    title: str | None = None
    description: str | None = None
    sort_order: int = 1
    is_active: bool = True


class MockExamLevelCreate(MockExamLevelBase):
    provider_id: UUID


class MockExamLevelUpdate(BaseSchema):
    level: str | None = None
    title: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class MockExamLevelResponse(MockExamLevelBase):
    id: UUID
    provider_id: UUID
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Model Test ("Modelltest 1")
# ============================================================


class ModelTestBase(BaseSchema):
    title: str
    description: str | None = None
    status: str = "DRAFT"
    sort_order: int = 1


class ModelTestCreate(ModelTestBase):
    level_id: UUID


class ModelTestUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    sort_order: int | None = None


class ModelTestResponse(ModelTestBase):
    id: UUID
    level_id: UUID
    model_config = ConfigDict(from_attributes=True)


class ModelTestScoreResponse(BaseSchema):
    """Auto-calculated totals — never stored, always derived at read time
    so they can never drift from the actual Teil/Kompetenz point values."""

    model_test_id: UUID
    total_points: int
    kompetenz_points: dict[str, int]


# ============================================================
# Kompetenz (Lesen / Hören / Schreiben / Sprechen)
# ============================================================


class KompetenzBase(BaseSchema):
    type: str
    title: str
    description: str | None = None
    total_points: int = 0
    duration_minutes: int = 0
    sort_order: int = 1


class KompetenzCreate(KompetenzBase):
    model_test_id: UUID


class KompetenzUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    total_points: int | None = None
    duration_minutes: int | None = None
    sort_order: int | None = None


class KompetenzResponse(KompetenzBase):
    id: UUID
    model_test_id: UUID
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Teil
# ============================================================


class TeilBase(BaseSchema):
    title: str
    description: str | None = None
    instructions: str | None = None
    points: int = 0
    time_limit_minutes: int | None = None
    sort_order: int = 1


class TeilCreate(TeilBase):
    kompetenz_id: UUID


class TeilUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    instructions: str | None = None
    points: int | None = None
    time_limit_minutes: int | None = None
    sort_order: int | None = None


class TeilResponse(TeilBase):
    id: UUID
    kompetenz_id: UUID
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Reading Content (Lesen)
# ============================================================


class ReadingContentBase(BaseSchema):
    content_type: str = "TEXT"
    text: str | None = None
    image_url: str | None = None


class ReadingContentCreate(ReadingContentBase):
    teil_id: UUID


class ReadingContentUpdate(BaseSchema):
    content_type: str | None = None
    text: str | None = None
    image_url: str | None = None


class ReadingContentResponse(ReadingContentBase):
    id: UUID
    teil_id: UUID
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Listening Content (Hören)
# ============================================================


class ListeningContentBase(BaseSchema):
    audio_url: str
    image_url: str | None = None
    transcript: str | None = None


class ListeningContentCreate(ListeningContentBase):
    teil_id: UUID


class ListeningContentUpdate(BaseSchema):
    audio_url: str | None = None
    image_url: str | None = None
    transcript: str | None = None


class ListeningContentResponse(ListeningContentBase):
    id: UUID
    teil_id: UUID
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Writing Task (Schreiben)
# ============================================================


class WritingTaskBase(BaseSchema):
    task_text: str
    image_url: str | None = None
    reference_document_url: str | None = None
    word_limit: int | None = None
    time_limit_minutes: int | None = None
    points: int = 0
    difficulty: str | None = None
    max_points: int = 100
    evaluation_rubric: str | None = None
    passing_score: int = 60


class WritingTaskCreate(WritingTaskBase):
    teil_id: UUID


class WritingTaskUpdate(BaseSchema):
    task_text: str | None = None
    image_url: str | None = None
    reference_document_url: str | None = None
    word_limit: int | None = None
    time_limit_minutes: int | None = None
    points: int | None = None
    difficulty: str | None = None
    max_points: int | None = None
    evaluation_rubric: str | None = None
    passing_score: int | None = None


class WritingTaskResponse(WritingTaskBase):
    id: UUID
    teil_id: UUID
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Speaking Task (Sprechen)
# ============================================================


class SpeakingTaskBase(BaseSchema):
    task_text: str
    image_url: str | None = None
    preparation_time_seconds: int = 60
    speaking_time_seconds: int = 90
    max_recording_duration_seconds: int = 120


class SpeakingTaskCreate(SpeakingTaskBase):
    teil_id: UUID


class SpeakingTaskUpdate(BaseSchema):
    task_text: str | None = None
    image_url: str | None = None
    preparation_time_seconds: int | None = None
    speaking_time_seconds: int | None = None
    max_recording_duration_seconds: int | None = None


class SpeakingTaskResponse(SpeakingTaskBase):
    id: UUID
    teil_id: UUID
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Question Options
# ============================================================


class MockQuestionOptionBase(BaseSchema):
    option_text: str
    match_value: str | None = None
    is_correct: bool = False
    sort_order: int = 1


class MockQuestionOptionCreate(MockQuestionOptionBase):
    question_id: UUID


class MockQuestionOptionUpdate(BaseSchema):
    option_text: str | None = None
    match_value: str | None = None
    is_correct: bool | None = None
    sort_order: int | None = None


class MockQuestionOptionResponse(MockQuestionOptionBase):
    id: UUID
    question_id: UUID
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Questions — admin-facing (includes correct answers). Any future
# student-facing "take the exam" schema must be a separate, stripped-down
# model that omits is_correct/match_value/correct_text_answer/explanation.
# ============================================================


class MockQuestionBase(BaseSchema):
    question_type: str
    question_text: str
    explanation: str | None = None
    correct_text_answer: str | None = None
    points: int = 1
    sort_order: int = 1


class MockQuestionCreate(MockQuestionBase):
    reading_content_id: UUID | None = None
    listening_content_id: UUID | None = None


class MockQuestionUpdate(BaseSchema):
    question_type: str | None = None
    question_text: str | None = None
    explanation: str | None = None
    correct_text_answer: str | None = None
    points: int | None = None
    sort_order: int | None = None


class MockQuestionResponse(MockQuestionBase):
    id: UUID
    reading_content_id: UUID | None = None
    listening_content_id: UUID | None = None
    options: list[MockQuestionOptionResponse] = []
    model_config = ConfigDict(from_attributes=True)


class MockQuestionMoveRequest(BaseSchema):
    """Question Bank: move a question to a different reading/listening
    content block (exactly one of the two must be set)."""

    reading_content_id: UUID | None = None
    listening_content_id: UUID | None = None


# ============================================================
# Student Attempts / Submissions / Results
# ============================================================


class MockTestAttemptCreate(BaseSchema):
    model_test_id: UUID


class MockTestAttemptResponse(BaseSchema):
    id: UUID
    model_test_id: UUID
    user_id: UUID
    status: str
    started_at: datetime
    submitted_at: datetime | None
    total_score: int | None
    max_score: int | None
    time_spent_seconds: int
    model_config = ConfigDict(from_attributes=True)


class MockQuestionAnswerCreate(BaseSchema):
    attempt_id: UUID
    question_id: UUID
    answer_data: str | None = None


class MockQuestionAnswerResponse(BaseSchema):
    id: UUID
    attempt_id: UUID
    question_id: UUID
    answer_data: str | None
    is_correct: bool | None
    points_earned: int
    model_config = ConfigDict(from_attributes=True)


class MockWritingSubmissionCreate(BaseSchema):
    attempt_id: UUID
    writing_task_id: UUID
    answer_text: str
    time_spent_seconds: int = 0


class MockWritingSubmissionTeacherUpdate(BaseSchema):
    teacher_score: int | None = None
    teacher_feedback: str | None = None


class MockWritingSubmissionResponse(BaseSchema):
    id: UUID
    attempt_id: UUID
    writing_task_id: UUID
    answer_text: str
    word_count: int
    time_spent_seconds: int
    ai_score: int | None
    ai_grammar_score: int | None
    ai_vocabulary_score: int | None
    ai_structure_score: int | None
    ai_task_achievement_score: int | None
    ai_coherence_score: int | None
    ai_feedback: str | None
    ai_evaluated_at: datetime | None
    teacher_score: int | None
    teacher_feedback: str | None
    submitted_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MockSpeakingSubmissionCreate(BaseSchema):
    attempt_id: UUID
    speaking_task_id: UUID
    audio_url: str


class MockSpeakingSubmissionTeacherUpdate(BaseSchema):
    teacher_score: int | None = None
    teacher_feedback: str | None = None


class MockSpeakingSubmissionResponse(BaseSchema):
    id: UUID
    attempt_id: UUID
    speaking_task_id: UUID
    audio_url: str
    transcript: str | None
    ai_score: int | None
    ai_feedback: str | None
    ai_evaluated_at: datetime | None
    teacher_score: int | None
    teacher_feedback: str | None
    submitted_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Analytics
# ============================================================


class TeilAnalytics(BaseSchema):
    teil_id: UUID
    title: str
    average_score_percent: float
    attempts: int


class KompetenzAnalytics(BaseSchema):
    kompetenz_id: UUID
    type: str
    title: str
    average_score_percent: float
    attempts: int


class ModelTestAnalytics(BaseSchema):
    model_test_id: UUID
    title: str
    average_score_percent: float
    pass_rate_percent: float
    attempts: int
    kompetenzen: list[KompetenzAnalytics]


class QuestionFailureItem(BaseSchema):
    question_id: UUID
    question_text: str
    times_answered: int
    times_correct: int
    failure_rate_percent: float


class CertificationProviderAnalytics(BaseSchema):
    provider_id: UUID
    name: str
    average_score_percent: float
    pass_rate_percent: float
    total_attempts: int
    model_tests: list[ModelTestAnalytics]
    most_failed_questions: list[QuestionFailureItem]


class DashboardSummary(BaseSchema):
    certificates: int
    levels: int
    model_tests: int
    questions: int
    media_assets: int
    students_attempted: int
    total_attempts: int
    ai_evaluations_used: int


# ============================================================
# Public / Vorbereitung — published-only, no answer keys. See
# app/services/mock_exam/public_service.py for the visibility rules.
# ============================================================


class PublicModelTestResponse(BaseSchema):
    id: UUID
    level_id: UUID
    title: str
    description: str | None
    sort_order: int
    is_locked: bool = False
    model_config = ConfigDict(from_attributes=True)


class PublicKompetenzSummary(BaseSchema):
    """One of the four skill cards on a Modelltest's public page —
    `has_content` is what drives the "Verfügbar" / "Noch nicht verfügbar"
    badge, computed from whether any Teil has been added, not a separate
    status field (Kompetenz/Teil don't carry their own publish state;
    visibility is gated entirely by the parent ModelTest's status)."""

    id: UUID
    type: str
    title: str
    has_content: bool


class PublicModelTestDetailResponse(BaseSchema):
    id: UUID
    level_id: UUID
    title: str
    description: str | None
    kompetenzen: list[PublicKompetenzSummary]


class PublicTeilContent(BaseSchema):
    id: UUID
    title: str
    description: str | None
    instructions: str | None
    reading_content: ReadingContentResponse | None = None
    listening_content: ListeningContentResponse | None = None
    writing_task: WritingTaskResponse | None = None
    speaking_task: SpeakingTaskResponse | None = None


class PublicKompetenzDetailResponse(BaseSchema):
    id: UUID
    model_test_id: UUID
    type: str
    title: str
    description: str | None
    duration_minutes: int
    teile: list[PublicTeilContent]
