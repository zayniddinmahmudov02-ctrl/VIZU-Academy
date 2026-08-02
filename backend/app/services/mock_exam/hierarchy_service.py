from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.certification_provider import CertificationProvider
from app.models.kompetenz import Kompetenz
from app.models.mock_exam_level import MockExamLevel
from app.models.model_test import ModelTest
from app.models.teil import Teil
from app.schemas.mock_exam import (
    CertificationProviderCreate,
    CertificationProviderUpdate,
    KompetenzCreate,
    KompetenzUpdate,
    MockExamLevelCreate,
    MockExamLevelUpdate,
    ModelTestCreate,
    ModelTestUpdate,
    TeilCreate,
    TeilUpdate,
)


# ============================================================
# Certification Provider
# ============================================================


def get_providers(db: Session):
    return db.scalars(
        select(CertificationProvider).order_by(CertificationProvider.sort_order)
    ).all()


def create_provider(db: Session, data: CertificationProviderCreate):
    existing = db.scalar(
        select(CertificationProvider).where(CertificationProvider.code == data.code)
    )
    if existing:
        raise HTTPException(status_code=409, detail="A certification provider with this code already exists.")

    provider = CertificationProvider(**data.model_dump())
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


def update_provider(db: Session, provider_id: UUID, data: CertificationProviderUpdate):
    provider = db.get(CertificationProvider, provider_id)
    if provider is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(provider, key, value)
    db.commit()
    db.refresh(provider)
    return provider


def delete_provider(db: Session, provider_id: UUID) -> bool:
    provider = db.get(CertificationProvider, provider_id)
    if provider is None:
        return False
    db.delete(provider)
    db.commit()
    return True


# ============================================================
# Mock Exam Level
# ============================================================


def get_levels(db: Session, provider_id: UUID | None = None):
    query = select(MockExamLevel).order_by(MockExamLevel.sort_order)
    if provider_id:
        query = query.where(MockExamLevel.provider_id == provider_id)
    return db.scalars(query).all()


def create_level(db: Session, data: MockExamLevelCreate):
    level = MockExamLevel(**data.model_dump())
    db.add(level)
    db.commit()
    db.refresh(level)
    return level


def update_level(db: Session, level_id: UUID, data: MockExamLevelUpdate):
    level = db.get(MockExamLevel, level_id)
    if level is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(level, key, value)
    db.commit()
    db.refresh(level)
    return level


def delete_level(db: Session, level_id: UUID) -> bool:
    level = db.get(MockExamLevel, level_id)
    if level is None:
        return False
    db.delete(level)
    db.commit()
    return True


# ============================================================
# Model Test
# ============================================================


def get_model_tests(db: Session, level_id: UUID | None = None):
    query = select(ModelTest).order_by(ModelTest.sort_order)
    if level_id:
        query = query.where(ModelTest.level_id == level_id)
    return db.scalars(query).all()


def create_model_test(db: Session, data: ModelTestCreate):
    model_test = ModelTest(**data.model_dump())
    db.add(model_test)
    db.commit()
    db.refresh(model_test)
    return model_test


def update_model_test(db: Session, model_test_id: UUID, data: ModelTestUpdate):
    model_test = db.get(ModelTest, model_test_id)
    if model_test is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(model_test, key, value)
    db.commit()
    db.refresh(model_test)
    return model_test


def delete_model_test(db: Session, model_test_id: UUID) -> bool:
    model_test = db.get(ModelTest, model_test_id)
    if model_test is None:
        return False
    db.delete(model_test)
    db.commit()
    return True


def calculate_model_test_score(db: Session, model_test_id: UUID) -> dict:
    """Sums Teil.points grouped by Kompetenz — computed on every call so it
    can never drift from the actual configured Teil points (Scoring
    requirement: "Every Kompetenz auto calculates. Whole Model Test auto
    calculates.")."""
    rows = db.execute(
        select(Kompetenz.id, Kompetenz.type, func.coalesce(func.sum(Teil.points), 0))
        .outerjoin(Teil, Teil.kompetenz_id == Kompetenz.id)
        .where(Kompetenz.model_test_id == model_test_id)
        .group_by(Kompetenz.id, Kompetenz.type)
    ).all()

    kompetenz_points = {str(row[1]): int(row[2]) for row in rows}
    total_points = sum(kompetenz_points.values())

    return {
        "model_test_id": model_test_id,
        "total_points": total_points,
        "kompetenz_points": kompetenz_points,
    }


# ============================================================
# Kompetenz
# ============================================================


def get_kompetenzen(db: Session, model_test_id: UUID | None = None):
    query = select(Kompetenz).order_by(Kompetenz.sort_order)
    if model_test_id:
        query = query.where(Kompetenz.model_test_id == model_test_id)
    return db.scalars(query).all()


def create_kompetenz(db: Session, data: KompetenzCreate):
    kompetenz = Kompetenz(**data.model_dump())
    db.add(kompetenz)
    db.commit()
    db.refresh(kompetenz)
    return kompetenz


def update_kompetenz(db: Session, kompetenz_id: UUID, data: KompetenzUpdate):
    kompetenz = db.get(Kompetenz, kompetenz_id)
    if kompetenz is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(kompetenz, key, value)
    db.commit()
    db.refresh(kompetenz)
    return kompetenz


def delete_kompetenz(db: Session, kompetenz_id: UUID) -> bool:
    kompetenz = db.get(Kompetenz, kompetenz_id)
    if kompetenz is None:
        return False
    db.delete(kompetenz)
    db.commit()
    return True


# ============================================================
# Teil
# ============================================================


def get_teile(db: Session, kompetenz_id: UUID | None = None):
    query = select(Teil).order_by(Teil.sort_order)
    if kompetenz_id:
        query = query.where(Teil.kompetenz_id == kompetenz_id)
    return db.scalars(query).all()


def create_teil(db: Session, data: TeilCreate):
    teil = Teil(**data.model_dump())
    db.add(teil)
    db.commit()
    db.refresh(teil)
    return teil


def update_teil(db: Session, teil_id: UUID, data: TeilUpdate):
    teil = db.get(Teil, teil_id)
    if teil is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(teil, key, value)
    db.commit()
    db.refresh(teil)
    return teil


def delete_teil(db: Session, teil_id: UUID) -> bool:
    teil = db.get(Teil, teil_id)
    if teil is None:
        return False
    db.delete(teil)
    db.commit()
    return True
