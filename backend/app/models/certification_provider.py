from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class CertificationProvider(BaseModel):
    """A certification body (Goethe, TELC, ÖSD, TestDaF, DSH, VIZU, ...).

    Named `CertificationProvider` rather than `Certificate` deliberately —
    `Certificate` already exists (app/models/certificate.py) and means
    something entirely different there: a document a *student* has earned
    by passing a course. This model is the exam *type/brand*, e.g. "Goethe"
    is a CertificationProvider; a student's Goethe B2 pass is unrelated to
    that existing table."""

    __tablename__ = "certification_providers"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    levels = relationship(
        "MockExamLevel",
        back_populates="provider",
        cascade="all, delete-orphan",
        order_by="MockExamLevel.sort_order",
    )
