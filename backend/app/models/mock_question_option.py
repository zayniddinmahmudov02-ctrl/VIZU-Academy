from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MockQuestionOption(BaseModel):
    """One option/item for a MockQuestion. How the fields are interpreted
    depends on the parent question's `question_type`:

    - SINGLE_CHOICE / MULTIPLE_CHOICE / TRUE_FALSE / DROPDOWN:
      `option_text` is the choice, `is_correct` marks the right one(s).
    - MATCHING: `option_text` is the left-side item, `match_value` is the
      correct right-side pair.
    - ORDERING: `option_text` is the item; `sort_order` IS the correct
      sequence (the admin arranges options in the correct order).
    """

    __tablename__ = "mock_question_options"

    question_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mock_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    match_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    question = relationship("MockQuestion", back_populates="options")
