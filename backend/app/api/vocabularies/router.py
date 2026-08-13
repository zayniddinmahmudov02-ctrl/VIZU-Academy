from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.api.dependencies.progress import require_lesson_access, require_video_completed
from app.db.session import get_db
from app.models.user import User

from app.schemas.vocabulary import (
    VocabularyCreate,
    VocabularyResponse,
    VocabularyUpdate,
)

from app.services.vocabulary import VocabularyService


router = APIRouter(
    prefix="/vocabularies",
    tags=["Vocabularies"],
)


@router.get(
    "/",
    response_model=list[VocabularyResponse],
)
def get_vocabularies(
    db: Session = Depends(get_db),
):
    service = VocabularyService(db)
    return service.get_all()


@router.get(
    "/{vocabulary_id}",
    response_model=VocabularyResponse,
)
def get_vocabulary(
    vocabulary_id: UUID,
    db: Session = Depends(get_db),
):
    service = VocabularyService(db)
    return service.get(vocabulary_id)


@router.get(
    "/lesson/{lesson_id}",
    response_model=list[VocabularyResponse],
)
def get_lesson_vocabularies(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    _: object = Depends(require_video_completed),
    __: object = Depends(require_lesson_access),
):
    """Requires the caller to have completed this lesson's video first —
    Vocabulary is the activity right after Video in the lesson flow.
    Published-only — a DRAFT vocabulary item must never reach a student,
    regardless of what the admin-only list/detail endpoints return.
    require_lesson_access additionally enforces the free-3-lessons /
    Premium rule, same as every other lesson-content endpoint."""

    service = VocabularyService(db)
    return service.get_by_lesson(
        lesson_id,
        published_only=True,
    )


@router.post(
    "/",
    response_model=VocabularyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vocabulary(
    payload: VocabularyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = VocabularyService(db)
    return service.create(payload.model_dump())


@router.put(
    "/{vocabulary_id}",
    response_model=VocabularyResponse,
)
def update_vocabulary(
    vocabulary_id: UUID,
    payload: VocabularyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = VocabularyService(db)

    vocabulary = service.get(vocabulary_id)

    return service.update(
        vocabulary,
        payload.model_dump(exclude_unset=True),
    )


@router.patch(
    "/{vocabulary_id}/publish",
    response_model=VocabularyResponse,
)
def publish_vocabulary(
    vocabulary_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = VocabularyService(db)

    vocabulary = service.get(vocabulary_id)

    return service.publish(vocabulary)


@router.patch(
    "/{vocabulary_id}/unpublish",
    response_model=VocabularyResponse,
)
def unpublish_vocabulary(
    vocabulary_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = VocabularyService(db)

    vocabulary = service.get(vocabulary_id)

    return service.unpublish(vocabulary)


@router.delete(
    "/{vocabulary_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_vocabulary(
    vocabulary_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = VocabularyService(db)

    vocabulary = service.get(vocabulary_id)

    service.delete(vocabulary)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )