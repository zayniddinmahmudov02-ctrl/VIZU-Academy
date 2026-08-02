from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.language import Language
from app.schemas.language import LanguageCreate, LanguageUpdate


def get_languages(db: Session):
    return db.scalars(
        select(Language)
    ).all()


def create_language(
    db: Session,
    data: LanguageCreate,
):
    existing = db.scalar(
        select(Language).where(Language.code == data.code)
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="A language with this code already exists.",
        )

    language = Language(**data.model_dump())

    db.add(language)
    db.commit()
    db.refresh(language)

    return language


def update_language(
    db: Session,
    language_id: UUID,
    data: LanguageUpdate,
):
    language = db.get(Language, language_id)

    if language is None:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(language, key, value)

    db.commit()
    db.refresh(language)

    return language
