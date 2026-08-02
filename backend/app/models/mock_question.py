from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

TYPE_SINGLE_CHOICE = "SINGLE_CHOICE"
TYPE_MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
TYPE_TRUE_FALSE = "TRUE_FALSE"
TYPE_MATCHING = "MATCHING"
TYPE_ORDERING = "ORDERING"
TYPE_FILL_BLANK = "FILL_BLANK"
TYPE_DROPDOWN = "DROPDOWN"
ALL_QUESTION_TYPES = {
    TYPE_SINGLE_CHOICE,
    TYPE_MULTIPLE_CHOICE,
    TYPE_TRUE_FALSE,
    TYPE_MATCHING,
    TYPE_ORDERING,
    TYPE_FILL_BLANK,
    TYPE_DROPDOWN,
}
# Types backed by MockQuestionOption rows (is_correct / order_index /
# match_value carry the answer). FILL_BLANK is the one exception — it has
# no discrete options, just `correct_text_answer` below.
OPTION_BASED_TYPES = ALL_QUESTION_TYPES - {TYPE_FILL_BLANK}


class MockQuestion(BaseModel):
    """A single question, belonging to either a ReadingContent or a
    ListeningContent (exactly one of the two FKs is set — Hören questions
    are "identical to Lesen" per spec, hence the shared table rather than
    two near-duplicate ones).

    Correct-answer data (`options.is_correct`, `correct_text_answer`) is
    only ever serialized into the ADMIN response schema. Any future
    student-facing "take the exam" schema must use a stripped-down
    response model that omits both — enforced at the schema layer when
    that surface is built (out of scope this phase per "do not start
    Courses yet").
    """

    __tablename__ = "mock_questions"

    reading_content_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reading_contents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    listening_content_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("listening_contents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    question_type: Mapped[str] = mapped_column(String(30), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    # FILL_BLANK only — the exact-match correct text answer.
    correct_text_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    options = relationship(
        "MockQuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="MockQuestionOption.sort_order",
    )
