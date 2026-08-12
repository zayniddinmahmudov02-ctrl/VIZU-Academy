from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.certification_provider import CertificationProvider
from app.models.kompetenz import Kompetenz
from app.models.mock_exam_level import MockExamLevel
from app.models.model_test import STATUS_PUBLISHED, ModelTest
from app.models.teil import Teil

# ============================================================
# Public / Vorbereitung — published-only, no authentication.
#
# Every query here filters on ModelTest.status == PUBLISHED plus
# is_active on the parent level and provider, so a provider or level
# being deactivated instantly hides everything under it from the
# public site too, not just from its own listing. Never touches
# MockQuestion/MockQuestionOption (answer keys) — this module only
# ever returns the passage/prompt content itself, matching the
# "content preview" scope of this task; the interactive
# question-answering flow is separate, already-existing/upcoming work
# (see attempt_service.py).
# ============================================================


def get_public_providers(db: Session):
    return db.scalars(
        select(CertificationProvider)
        .where(CertificationProvider.is_active.is_(True))
        .order_by(CertificationProvider.sort_order)
    ).all()


def get_public_levels(db: Session, provider_id: UUID):
    return db.scalars(
        select(MockExamLevel)
        .join(CertificationProvider, MockExamLevel.provider_id == CertificationProvider.id)
        .where(
            MockExamLevel.provider_id == provider_id,
            MockExamLevel.is_active.is_(True),
            CertificationProvider.is_active.is_(True),
        )
        .order_by(MockExamLevel.sort_order)
    ).all()


def get_public_model_tests(db: Session, level_id: UUID):
    return db.scalars(
        select(ModelTest)
        .join(MockExamLevel, ModelTest.level_id == MockExamLevel.id)
        .join(CertificationProvider, MockExamLevel.provider_id == CertificationProvider.id)
        .where(
            ModelTest.level_id == level_id,
            ModelTest.status == STATUS_PUBLISHED,
            MockExamLevel.is_active.is_(True),
            CertificationProvider.is_active.is_(True),
        )
        .order_by(ModelTest.sort_order)
    ).all()


def get_public_model_test(db: Session, model_test_id: UUID) -> ModelTest | None:
    """The ModelTest itself plus its Kompetenzen (with Teile eager-loaded
    so the router can compute `has_content` without N+1 queries) — 404s
    if the test, its level, or its provider isn't publicly visible."""
    return db.scalar(
        select(ModelTest)
        .join(MockExamLevel, ModelTest.level_id == MockExamLevel.id)
        .join(CertificationProvider, MockExamLevel.provider_id == CertificationProvider.id)
        .where(
            ModelTest.id == model_test_id,
            ModelTest.status == STATUS_PUBLISHED,
            MockExamLevel.is_active.is_(True),
            CertificationProvider.is_active.is_(True),
        )
        .options(selectinload(ModelTest.kompetenzen).selectinload(Kompetenz.teile))
    )


def get_public_kompetenz(db: Session, kompetenz_id: UUID) -> Kompetenz | None:
    """A Kompetenz's Teile with their content (reading/listening/writing/
    speaking) — gated on the parent ModelTest being PUBLISHED and its
    level/provider active, same as above."""
    return db.scalar(
        select(Kompetenz)
        .join(ModelTest, Kompetenz.model_test_id == ModelTest.id)
        .join(MockExamLevel, ModelTest.level_id == MockExamLevel.id)
        .join(CertificationProvider, MockExamLevel.provider_id == CertificationProvider.id)
        .where(
            Kompetenz.id == kompetenz_id,
            ModelTest.status == STATUS_PUBLISHED,
            MockExamLevel.is_active.is_(True),
            CertificationProvider.is_active.is_(True),
        )
        .options(
            selectinload(Kompetenz.teile).selectinload(Teil.reading_content),
            selectinload(Kompetenz.teile).selectinload(Teil.listening_content),
            selectinload(Kompetenz.teile).selectinload(Teil.writing_task),
            selectinload(Kompetenz.teile).selectinload(Teil.speaking_task),
        )
    )
