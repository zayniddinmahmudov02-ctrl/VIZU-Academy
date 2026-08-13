import json
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.api.dependencies.progress import require_lesson_access, require_video_completed
from app.core.config import settings
from app.db.session import get_db
from app.models.lesson import Lesson
from app.models.user import User
from app.services.vizu_pay.access import can_access_lesson

from app.schemas.vocabulary import (
    AudioQueueStatusResponse,
    BulkAnalyzeRequest,
    BulkSaveRequest,
    BulkSaveResponse,
    MissingAudioWord,
    SaveRecordedAudioResponse,
    VocabularyCreate,
    VocabularyResponse,
    VocabularyUpdate,
)

from app.services.vocabulary import VocabularyBulkService, VocabularyService, normalize_word_list
from app.services.vocabulary import audio_processing


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
    return BulkSaveResponse(**result)


# ==========================
# Personal voice recording — no AI-generated audio anywhere below.
# The admin records the word once; process() cleans + repeats it 3x
# (see audio_processing.py); save() persists the already-processed
# result against one existing Vocabulary row.
# ==========================


_MAX_UPLOAD_BYTES = settings.VOCAB_AUDIO_MAX_UPLOAD_MB * 1024 * 1024


def _validate_audio_upload(content_type: str | None, raw: bytes) -> None:
    if content_type and not (content_type.startswith("audio/") or content_type == "application/octet-stream"):
        raise HTTPException(status_code=400, detail=f"Invalid content type: {content_type}")
    if not raw:
        raise HTTPException(status_code=400, detail="Empty audio upload")
    if len(raw) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Audio upload exceeds {settings.VOCAB_AUDIO_MAX_UPLOAD_MB}MB limit",
        )


@router.post("/audio/process")
async def process_vocabulary_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin_panel_access),
):
    """Takes one raw microphone recording (whatever MediaRecorder
    produced — typically audio/webm;codecs=opus) and returns the final
    cleaned + 3x-repeated WAV directly as the response body. Nothing is
    written to disk or the database here — this is the "preview" step;
    the admin's own voice never touches permanent storage until they
    press Speichern (see POST /{vocabulary_id}/audio/save)."""

    raw = await file.read()
    _validate_audio_upload(file.content_type, raw)

    try:
        wav_bytes = await audio_processing.process_recording(raw)
    except audio_processing.AudioProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return Response(content=wav_bytes, media_type="audio/wav")


@router.post(
    "/{vocabulary_id}/audio/save",
    response_model=SaveRecordedAudioResponse,
)
async def save_vocabulary_audio(
    vocabulary_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    """Persists the already-processed WAV from POST /audio/process
    against one existing Vocabulary row — never creates a new row, never
    touches word/article/plural/translation/example/order_index. New
    file stored and committed before the old one (if any) is deleted."""

    vocab_service = VocabularyService(db)
    vocabulary = vocab_service.get(vocabulary_id)

    if vocabulary is None:
        raise HTTPException(status_code=404, detail="Vocabulary not found")

    wav_bytes = await file.read()
    _validate_audio_upload(file.content_type, wav_bytes)

    bulk_service = VocabularyBulkService(db)
    try:
        new_url = await bulk_service.save_recorded_audio(vocabulary, wav_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SaveRecordedAudioResponse(audio_url=new_url)


# ==========================
# Missing-audio queue ("Audio nacheinander aufnehmen")
# ==========================


@router.get(
    "/lesson/{lesson_id}/audio-queue",
    response_model=AudioQueueStatusResponse,
)
def get_audio_queue_status(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    """Read-only — lists words in this lesson still missing a recording
    (audio_status != GENERATED), for the "Audio: ❌ Fehlt" column and the
    "Audio nacheinander aufnehmen" sequential recording workflow."""

    service = VocabularyBulkService(db)
    missing = service.get_missing_audio(lesson_id)

    return AudioQueueStatusResponse(
        lesson_id=lesson_id,
        missing=[MissingAudioWord.model_validate(v) for v in missing],
        total_missing=len(missing),
    )