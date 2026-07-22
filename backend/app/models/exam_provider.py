from sqlalchemy import String

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.models.base import BaseModel


class ExamProvider(BaseModel):

    __tablename__ = "exam_providers"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
    )

    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
    )