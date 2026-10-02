from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseSchema

from .schema import VizuMultilevelAnswerSubmit, VizuMultilevelQuestionPublic


class VizuMultilevelHoerenTaskPublic(BaseSchema):
    """One Hören Aufgabe for the student: its questions/options and whether
    an audio exists. Deliberately NO audio url / file name / storage path,
    NO transcript and NO CEFR level — the audio is streamed through an
    authenticated endpoint."""

    id: UUID
    skill: str
    order_index: int
    passage_text: str | None
    has_audio: bool
    questions: list[VizuMultilevelQuestionPublic]


class VizuMultilevelHoerenSubmitRequest(BaseSchema):
    answers: list[VizuMultilevelAnswerSubmit]


class VizuMultilevelHoerenDraftSave(BaseSchema):
    answers: list[VizuMultilevelAnswerSubmit]


class VizuMultilevelHoerenDraft(BaseSchema):
    """question_id -> selected option_id (autosaved answers)."""

    answers: dict[str, str]


class VizuMultilevelHoerenResult(BaseSchema):
    attempt_id: UUID
    total_points: float
    max_points: float
    correct: int
    wrong: int
    unanswered: int
    # Determined by the server from the total score (same thresholds as
    # Lesen: 20/40/60/75/90 %). null = below A1.
    hoeren_level: str | None
    below_a1: bool


class VizuMultilevelHoerenAudioSlot(BaseSchema):
    """Admin view of one Aufgabe's audio slot (always 5 slots)."""

    aufgabe_number: int
    audio_id: UUID | None
    has_audio: bool
    file_name: str | None
    content_type: str | None
    duration_seconds: int | None
    is_active: bool
    updated_at: datetime | None


class VizuMultilevelHoerenDiagnosticsAufgabe(BaseSchema):
    aufgabe_number: int
    task_exists: bool
    is_published: bool
    questions: int
    expected_questions: int
    options: int
    has_audio: bool


class VizuMultilevelHoerenDiagnostics(BaseSchema):
    aufgaben: list[VizuMultilevelHoerenDiagnosticsAufgabe]
    tasks: int
    expected_tasks: int
    questions: int
    expected_questions: int
    options: int
    expected_options: int
    audio: int
    complete: bool
