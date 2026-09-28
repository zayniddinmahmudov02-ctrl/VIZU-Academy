from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.api.dependencies.progress import require_lesson_access
from app.db.session import get_db
from app.models.lesson import Lesson
from app.models.user import User
from app.repositories.student_progress import StudentProgressRepository
from app.services.vizu_pay.access import can_access_lesson

from app.schemas.vocabulary import (
    VocabularyCompleteRequest,
    VocabularyResponse,
)

from app.services.vocabulary import VocabularyService

# Read-only apart from the Wortschatz Test completion below: vocabulary
# create/update/publish/delete, the bulk generator and the AI enrichment
# were removed from the admin panel (vocabulary content is produced
# externally and imported straight into the database).


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
    current_user: User = Depends(require_admin_panel_access),
):
    # Unscoped across every lesson — admin CMS content table only; students
    # always go through GET /vocabularies/lesson/{id}.
    service = VocabularyService(db)
    return service.get_all()


@router.get(
    "/{vocabulary_id}",
    response_model=VocabularyResponse,
)
def get_vocabulary(
    vocabulary_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = VocabularyService(db)
    vocabulary = service.get(vocabulary_id)

    if not vocabulary:
        raise HTTPException(status_code=404, detail="Vocabulary not found")

    # Same gate as GET /vocabularies/lesson/{lesson_id} — direct-by-ID must
    # not bypass the free-3-lessons/Premium rule.
    lesson = db.get(Lesson, vocabulary.lesson_id)
    if lesson is None or not can_access_lesson(current_user, lesson):
        raise HTTPException(status_code=403, detail="PREMIUM_REQUIRED")

    return vocabulary


@router.get(
    "/lesson/{lesson_id}",
    response_model=list[VocabularyResponse],
)
def get_lesson_vocabularies(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    __: object = Depends(require_lesson_access),
):
    """Published-only — a DRAFT vocabulary item must never reach a
    student, regardless of what the admin-only list/detail endpoints
    return. require_lesson_access enforces the free-3-lessons / Premium
    rule, same as every other lesson-content endpoint. Sections are
    independently accessible in any order (no sequential video-first
    requirement) — see project memory on section-gate removal."""

    service = VocabularyService(db)
    return service.get_by_lesson(
        lesson_id,
        published_only=True,
    )


@router.post("/lesson/{lesson_id}/complete")
def complete_lesson_vocabulary(
    lesson_id: UUID,
    payload: VocabularyCompleteRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    __: object = Depends(require_lesson_access),
):
    """Marks Wortschatz reviewed for this lesson — same simple
    StudentProgress-flag pattern as video completion (see
    StudentProgressRepository.mark_video_completed), feeding the
    Wortschatz component of the 100-point lesson score. An optional
    percentage (from the interactive exercise session) is stored
    alongside the binary flag so LessonScoringService can award partial
    credit; callers that omit it keep the old all-or-nothing behavior."""

    repo = StudentProgressRepository(db)
    progress = repo.get_or_create(str(current_user.id), str(lesson_id))
    percentage = payload.percentage if payload else None
    repo.mark_vocabulary_completed(progress, percentage=percentage)

    return {"vocabulary_completed": True, "vocabulary_score": progress.vocabulary_score}
