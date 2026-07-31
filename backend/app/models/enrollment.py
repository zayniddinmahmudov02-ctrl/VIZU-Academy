from sqlalchemy import (
    Boolean,
    ForeignKey,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import BaseModel


class Enrollment(BaseModel):

    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "course_id",
            name="uq_enrollments_user_course",
        ),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    course_id: Mapped[str] = mapped_column(
        ForeignKey(
            "courses.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    user = relationship("User")

    course = relationship("Course")