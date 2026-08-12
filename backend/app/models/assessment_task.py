from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.assessment import STATUS_ARCHIVED, STATUS_DRAFT, STATUS_PUBLISHED

# Re-exported for callers that only need task-level statuses — same three
# values as Assessment.status (app/models/assessment.py), reused rather
# than redefined so the two never drift apart.
ALL_TASK_STATUSES = {STATUS_DRAFT, STATUS_PUBLISHED, STATUS_ARCHIVED}

TYPE_TRUE_FALSE = "TRUE_FALSE"
TYPE_MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
TYPE_MULTIPLE_SELECT = "MULTIPLE_SELECT"
TYPE_CLOZE_TEXT = "CLOZE_TEXT"
TYPE_HEADING_MATCHING = "HEADING_MATCHING"
TYPE_ADVERTISEMENT_MATCHING = "ADVERTISEMENT_MATCHING"
TYPE_TEXT_MATCHING = "TEXT_MATCHING"
TYPE_SENTENCE_ORDERING = "SENTENCE_ORDERING"
TYPE_SHORT_ANSWER = "SHORT_ANSWER"
TYPE_GAP_MATCHING = "GAP_MATCHING"
TYPE_DRAG_DROP = "DRAG_DROP"
TYPE_CATEGORY_SORTING = "CATEGORY_SORTING"
TYPE_IMAGE_SELECTION = "IMAGE_SELECTION"
TYPE_WRITING = "WRITING"
TYPE_SPEAKING = "SPEAKING"

ALL_TASK_TYPES = {
    TYPE_TRUE_FALSE,
    TYPE_MULTIPLE_CHOICE,
    TYPE_MULTIPLE_SELECT,
    TYPE_CLOZE_TEXT,
    TYPE_HEADING_MATCHING,
    TYPE_ADVERTISEMENT_MATCHING,
    TYPE_TEXT_MATCHING,
    TYPE_SENTENCE_ORDERING,
    TYPE_SHORT_ANSWER,
    TYPE_GAP_MATCHING,
    TYPE_DRAG_DROP,
    TYPE_CATEGORY_SORTING,
    TYPE_IMAGE_SELECTION,
    TYPE_WRITING,
    TYPE_SPEAKING,
}

EVAL_MODE_AI_ONLY = "AI_ONLY"
EVAL_MODE_TEACHER_ONLY = "TEACHER_ONLY"
EVAL_MODE_AI_AND_TEACHER = "AI_AND_TEACHER"
ALL_EVALUATION_MODES = {EVAL_MODE_AI_ONLY, EVAL_MODE_TEACHER_ONLY, EVAL_MODE_AI_AND_TEACHER}


class AssessmentTask(BaseModel):
    """One task ("Aufgabe") within a Section. `content` holds the rich-text
    passage/cloze-text/ad-texts body (task_type dependent); `config` holds
    any structured, task-type-specific data that doesn't fit the generic
    TaskQuestion/TaskOption shape, stored as JSON text (same
    JSON-as-text convention as MockQuestionAnswer.answer_data) rather than
    JSONB, matching this codebase's existing style."""

    __tablename__ = "assessment_tasks"

    section_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # Per-task publish state — finer-grained than Assessment.status (which
    # gates the whole assessment). A task only reaches the public API when
    # BOTH its own status AND its parent Assessment's status are PUBLISHED.
    status: Mapped[str] = mapped_column(
        String(20), default=STATUS_DRAFT, server_default=STATUS_DRAFT, nullable=False, index=True
    )

    # Audio play policy — only meaningful for HOEREN-skill tasks (i.e. ones
    # with an attached TaskAudio), but kept on the generic table rather
    # than a HOEREN-only side table since it's just 5 small columns and
    # every other task type simply ignores them, same as e.g. `content`
    # being unused by option-only task types.
    audio_play_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1, 2, or NULL = unlimited
    allow_pause: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    allow_seek: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    allow_replay: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    allow_speed_change: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    # Writing (SCHREIBEN) config — only meaningful for task_type=WRITING,
    # kept on the generic table for the same reason as the audio-policy
    # columns above: a handful of nullable/defaulted columns every other
    # task type simply ignores, instead of a WRITING-only side table.
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    min_words: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_words: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evaluation_mode: Mapped[str] = mapped_column(
        String(20), default=EVAL_MODE_AI_ONLY, server_default=EVAL_MODE_AI_ONLY, nullable=False
    )

    # Speaking (SPRECHEN) config — only meaningful for task_type=SPEAKING.
    # `image_url`, `evaluation_mode`, and `rubric_criteria` above are
    # already generic enough to be reused as-is (Sprechen tasks are simply
    # created with evaluation_mode="TEACHER_ONLY" and rubric criteria of
    # their own); only the prep/speak timers are genuinely new.
    prep_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speak_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    section = relationship("AssessmentSection", back_populates="tasks")
    questions = relationship(
        "TaskQuestion",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskQuestion.sort_order",
    )
    audio = relationship(
        "TaskAudio",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
    )
    rubric_criteria = relationship(
        "WritingRubricCriterion",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="WritingRubricCriterion.sort_order",
    )
