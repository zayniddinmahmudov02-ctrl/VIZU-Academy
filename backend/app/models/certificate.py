from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import BaseModel


class Certificate(BaseModel):

    __tablename__ = "certificates"

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

    certificate_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    verification_code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        default="VIZU",
    )

    level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    lesen_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    hoeren_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    schreiben_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    sprechen_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    pdf_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    qr_code_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    issued_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    user = relationship(
        "User",
    )

    course = relationship(
        "Course",
    )