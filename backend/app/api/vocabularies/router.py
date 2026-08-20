import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.api.dependencies.progress import require_lesson_access
from app.db.session import get_db
from app.models.lesson import Lesson
from app.models.user import User
from app.repositories.student_progress import StudentProgressRepository
from app.services.vizu_pay.access import can_access_lesson

from app.schemas.vocabulary import (
    BulkAnalyzeRequest,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkSaveRequest,
    BulkSaveResponse,
    VocabularyCompleteRequest,
    VocabularyCreate,
    VocabularyResponse,
    VocabularyUpdate,
)

from app.services.vocabulary import (
    VocabularyBulkService,
    VocabularyService,
    normalize_word_list,
    sync_vocabulary_test,
)


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
    created = service.create(payload.model_dump())
    sync_vocabulary_test(db, payload.lesson_id)
    return created


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

    updated = service.update(
        vocabulary,
        payload.model_dump(exclude_unset=True),
    )
    sync_vocabulary_test(db, updated.lesson_id)
    return updated


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

    published = service.publish(vocabulary)
    sync_vocabulary_test(db, published.lesson_id)
    return published


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

    unpublished = service.unpublish(vocabulary)
    sync_vocabulary_test(db, unpublished.lesson_id)
    return unpublished


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
    lesson_id = vocabulary.lesson_id

    service.delete(vocabulary)
    sync_vocabulary_test(db, lesson_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.post("/bulk/delete", response_model=BulkDeleteResponse)
async def bulk_delete_vocabulary(
    payload: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    """One request for however many words are selected — not one DELETE
    per row. Scoped to lesson_id server-side (see
    VocabularyBulkService.bulk_delete) so a stale/tampered ID list can
    never delete a word belonging to a different lesson."""

    service = VocabularyBulkService(db)
    deleted_count = await service.bulk_delete(payload.lesson_id, payload.vocabulary_ids)
    sync_vocabulary_test(db, payload.lesson_id)
    return BulkDeleteResponse(deleted_count=deleted_count)


# ==========================
# Bulk generator
# ==========================


@router.post("/bulk/analyze")
async def bulk_analyze_vocabulary(
    payload: BulkAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    """Streams newline-delimited JSON — progress updates while Gemini
    TEXT enrichment runs (article/plural/translation/example — never
    audio), then one line per preview row, then a final {"type": "done"}.
    Nothing is written to the database here; see POST /bulk/save for
    that. A native fetch() reader on the frontend, not axios, consumes
    this (see bulk-vocabulary-dialog.tsx) — StreamingResponse's body
    never completes until every word has been processed."""

    words = normalize_word_list("\n".join(payload.words))
    service = VocabularyBulkService(db)

    async def ndjson():
        async for event in service.analyze_stream(
            payload.lesson_id,
            words,
            payload.auto_complete,
        ):
            yield json.dumps(event) + "\n"

    return StreamingResponse(ndjson(), media_type="application/x-ndjson")


@router.post("/bulk/save", response_model=BulkSaveResponse)
async def bulk_save_vocabulary(
    payload: BulkSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = VocabularyBulkService(db)
    result = await service.bulk_save(
        payload.lesson_id,
        [item.model_dump() for item in payload.items],
    )
    sync_vocabulary_test(db, payload.lesson_id)
    return BulkSaveResponse(**result)