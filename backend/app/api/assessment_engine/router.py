from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access, require_super_admin
from app.db.session import get_db
from app.models.user import User

from app.schemas.assessment_engine import (
    AnswerResponse,
    AnswerSubmit,
    AssessmentAttemptCreate,
    AssessmentAttemptResponse,
    AssessmentCreate,
    AssessmentFullResponse,
    AssessmentResponse,
    AssessmentResultResponse,
    AssessmentSectionCreate,
    AssessmentSectionResponse,
    AssessmentSectionUpdate,
    AssessmentTaskCreate,
    AssessmentTaskResponse,
    AssessmentTaskUpdate,
    AssessmentUpdate,
    AudioPlayStatusResponse,
    PendingWritingReviewItem,
    PublicAssessment,
    TaskAudioResponse,
    TaskOptionCreate,
    TaskOptionResponse,
    TaskOptionUpdate,
    TaskQuestionCreate,
    TaskQuestionResponse,
    TaskQuestionUpdate,
    TaskValidationResponse,
    TeacherReviewInput,
    WritingEvaluationResponse,
    WritingResultResponse,
    WritingRubricCriterionCreate,
    WritingRubricCriterionResponse,
    WritingRubricCriterionUpdate,
    WritingSubmissionResponse,
    WritingSubmissionSave,
)

from app.services.assessment_engine import (
    attempt_service,
    audio_service,
    crud_service,
    public_service,
    writing_service,
)

router = APIRouter(tags=["Assessment Engine"])


# ============================================================
# Assessments (admin — Super Admin only per spec section 11)
# ============================================================

@router.get("/assessments", response_model=list[AssessmentResponse])
def list_assessments(
    assessment_type: str | None = None,
    status: str | None = None,
    lesson_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return crud_service.list_assessments(db, assessment_type, status, lesson_id)


@router.post("/assessments", response_model=AssessmentResponse, status_code=201)
def create_assessment(
    data: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return crud_service.create_assessment(db, data, current_user)


@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    assessment = crud_service.get_assessment(db, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    return assessment


@router.get("/assessments/{assessment_id}/full", response_model=AssessmentFullResponse)
def get_assessment_full(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Assessment with every section -> task -> question -> option eagerly
    loaded, for the builder UI (avoids N+1 waterfall requests)."""
    assessment = crud_service.get_assessment_with_sections(db, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    return assessment


@router.put("/assessments/{assessment_id}", response_model=AssessmentResponse)
def update_assessment(
    assessment_id: str,
    data: AssessmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    assessment = crud_service.update_assessment(db, assessment_id, data)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    return assessment


@router.delete("/assessments/{assessment_id}", status_code=204)
async def delete_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    if not await crud_service.delete_assessment(db, assessment_id):
        raise HTTPException(status_code=404, detail="Assessment not found.")


# ============================================================
# Sections
# ============================================================

@router.get("/assessments/{assessment_id}/sections", response_model=list[AssessmentSectionResponse])
def list_sections(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return crud_service.list_sections(db, assessment_id)


@router.post("/assessments/{assessment_id}/sections", response_model=AssessmentSectionResponse, status_code=201)
def create_section(
    assessment_id: str,
    data: AssessmentSectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    payload = data.model_copy(update={"assessment_id": assessment_id})
    return crud_service.create_section(db, payload)


@router.put("/sections/{section_id}", response_model=AssessmentSectionResponse)
def update_section(
    section_id: str,
    data: AssessmentSectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    section = crud_service.update_section(db, section_id, data)
    if section is None:
        raise HTTPException(status_code=404, detail="Section not found.")
    return section


@router.delete("/sections/{section_id}", status_code=204)
async def delete_section(
    section_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    if not await crud_service.delete_section(db, section_id):
        raise HTTPException(status_code=404, detail="Section not found.")


# ============================================================
# Tasks
# ============================================================

@router.get("/sections/{section_id}/tasks", response_model=list[AssessmentTaskResponse])
def list_tasks(
    section_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return crud_service.list_tasks(db, section_id)


@router.post("/sections/{section_id}/tasks", response_model=AssessmentTaskResponse, status_code=201)
def create_task(
    section_id: str,
    data: AssessmentTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    payload = data.model_copy(update={"section_id": section_id})
    return crud_service.create_task(db, payload)


@router.get("/tasks/{task_id}", response_model=AssessmentTaskResponse)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    task = crud_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


@router.put("/tasks/{task_id}", response_model=AssessmentTaskResponse)
def update_task(
    task_id: str,
    data: AssessmentTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    task = crud_service.update_task(db, task_id, data)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    if not await crud_service.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Task not found.")


@router.get("/tasks/{task_id}/validate", response_model=TaskValidationResponse)
def validate_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Called by the builder before allowing Publish — e.g. a
    MULTIPLE_CHOICE question with zero correct options, or a CLOZE_TEXT
    gap with no correct answer set."""
    errors = crud_service.validate_task(db, task_id)
    return {"task_id": task_id, "is_publishable": len(errors) == 0, "errors": errors}


# ============================================================
# Audio (HOEREN) — admin upload/replace/delete, secure serving,
# server-enforced play count
# ============================================================

@router.post("/tasks/{task_id}/audio", response_model=TaskAudioResponse, status_code=201)
async def upload_task_audio(
    task_id: str,
    file: UploadFile = File(...),
    duration_seconds: int | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Upload or replace this task's audio in one call — a second upload
    always removes the previous file first (see audio_service.upload_audio)."""
    return await audio_service.upload_audio(db, task_id, file, duration_seconds)


@router.delete("/tasks/{task_id}/audio", status_code=204)
async def delete_task_audio(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    if not await audio_service.delete_audio(db, task_id):
        raise HTTPException(status_code=404, detail="No audio for this task.")


@router.get("/audio/{task_id}")
def get_task_audio(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The only real way to fetch audio bytes — not a public URL, not the
    /uploads static mount. Re-checks permission on every single request:
    super admin, or a PUBLISHED assessment (and, for MOCK_TEST, an
    existing attempt on it) — see audio_service.authorize_audio_access."""
    audio = audio_service.authorize_audio_access(db, task_id, current_user)
    path = audio_service.resolve_audio_path(audio)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file missing on disk.")
    return FileResponse(path=path, media_type=audio.content_type, filename=audio.filename)


@router.get("/tasks/{task_id}/audio-status", response_model=AudioPlayStatusResponse)
def get_audio_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return audio_service.get_play_status(db, task_id, current_user)


@router.post("/tasks/{task_id}/audio-play", response_model=AudioPlayStatusResponse)
def register_audio_play(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Called once per actual playback start (not per frontend render) —
    increments the server-side play count and re-validates the limit.
    The frontend disabling its own button is a UX nicety, not the
    security boundary; this endpoint is."""
    return audio_service.register_play(db, task_id, current_user)


# ============================================================
# Questions
# ============================================================

@router.post("/tasks/{task_id}/questions", response_model=TaskQuestionResponse, status_code=201)
def create_question(
    task_id: str,
    data: TaskQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    payload = data.model_copy(update={"task_id": task_id})
    return crud_service.create_question(db, payload)


@router.put("/questions/{question_id}", response_model=TaskQuestionResponse)
def update_question(
    question_id: str,
    data: TaskQuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    question = crud_service.update_question(db, question_id, data)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found.")
    return question


@router.delete("/questions/{question_id}", status_code=204)
def delete_question(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    if not crud_service.delete_question(db, question_id):
        raise HTTPException(status_code=404, detail="Question not found.")


# ============================================================
# Options
# ============================================================

@router.post("/questions/{question_id}/options", response_model=TaskOptionResponse, status_code=201)
def create_option(
    question_id: str,
    data: TaskOptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    payload = data.model_copy(update={"question_id": question_id})
    return crud_service.create_option(db, payload)


@router.put("/options/{option_id}", response_model=TaskOptionResponse)
def update_option(
    option_id: str,
    data: TaskOptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    option = crud_service.update_option(db, option_id, data)
    if option is None:
        raise HTTPException(status_code=404, detail="Option not found.")
    return option


@router.delete("/options/{option_id}", status_code=204)
def delete_option(
    option_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    if not crud_service.delete_option(db, option_id):
        raise HTTPException(status_code=404, detail="Option not found.")


# ============================================================
# Writing rubric criteria (SCHREIBEN) — admin builder
# ============================================================

@router.post("/tasks/{task_id}/rubric-criteria", response_model=WritingRubricCriterionResponse, status_code=201)
def create_rubric_criterion(
    task_id: str,
    data: WritingRubricCriterionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    payload = data.model_copy(update={"task_id": task_id})
    return crud_service.create_rubric_criterion(db, payload)


@router.put("/rubric-criteria/{criterion_id}", response_model=WritingRubricCriterionResponse)
def update_rubric_criterion(
    criterion_id: str,
    data: WritingRubricCriterionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    criterion = crud_service.update_rubric_criterion(db, criterion_id, data)
    if criterion is None:
        raise HTTPException(status_code=404, detail="Rubric criterion not found.")
    return criterion


@router.delete("/rubric-criteria/{criterion_id}", status_code=204)
def delete_rubric_criterion(
    criterion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    if not crud_service.delete_rubric_criterion(db, criterion_id):
        raise HTTPException(status_code=404, detail="Rubric criterion not found.")


# ============================================================
# Public (published-only — any authenticated user)
# ============================================================

@router.get("/public/assessments/{assessment_id}", response_model=PublicAssessment)
def get_public_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assessment = public_service.get_published_assessment(db, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found or not published.")
    return public_service.to_public_schema(assessment)


@router.get("/public/lessons/{lesson_id}/assessment", response_model=PublicAssessment | None)
def get_public_lesson_assessment(
    lesson_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns null (not 404) when no PUBLISHED assessment exists for this
    lesson yet — the frontend renders the empty state
    ("Für diese Lektion sind noch keine Aufgaben verfügbar.") rather than
    treating it as an error."""
    assessment = public_service.get_published_assessment_for_lesson(db, lesson_id)
    if assessment is None:
        return None
    return public_service.to_public_schema(assessment)


# ============================================================
# Attempts
# ============================================================

@router.post("/attempts", response_model=AssessmentAttemptResponse, status_code=201)
def start_attempt(
    data: AssessmentAttemptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return attempt_service.start_attempt(db, data.assessment_id, current_user)


@router.post("/attempts/{attempt_id}/answers", response_model=AnswerResponse)
def submit_answer(
    attempt_id: str,
    data: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return attempt_service.submit_answer(db, attempt_id, current_user, data)


@router.post("/attempts/{attempt_id}/submit", response_model=AssessmentAttemptResponse)
def submit_attempt(
    attempt_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return attempt_service.submit_attempt(db, attempt_id, current_user)


@router.get("/attempts/{attempt_id}/result", response_model=AssessmentResultResponse)
def get_attempt_result(
    attempt_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return attempt_service.get_result(db, attempt_id, current_user)


# ============================================================
# Writing (SCHREIBEN) submissions — Speichern / Abgeben / results
# ============================================================

@router.get("/attempts/{attempt_id}/writing/{task_id}", response_model=WritingSubmissionResponse | None)
def get_writing_submission(
    attempt_id: str,
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return writing_service.get_submission(db, attempt_id, task_id, current_user)


@router.put("/attempts/{attempt_id}/writing/{task_id}", response_model=WritingSubmissionResponse)
def save_writing_draft(
    attempt_id: str,
    task_id: str,
    data: WritingSubmissionSave,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Speichern — creates or updates the DRAFT in place."""
    return writing_service.save_draft(db, attempt_id, task_id, current_user, data.content)


@router.post("/attempts/{attempt_id}/writing/{task_id}/submit", response_model=WritingSubmissionResponse)
async def submit_writing(
    attempt_id: str,
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Abgeben — locks in the current draft content, validates
    min/max words, and (per the task's evaluation_mode) synchronously
    triggers AI evaluation before returning."""
    return await writing_service.submit_submission(db, attempt_id, task_id, current_user)


@router.get("/attempts/{attempt_id}/writing/{task_id}/result", response_model=WritingResultResponse)
def get_writing_result(
    attempt_id: str,
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return writing_service.get_writing_result(db, attempt_id, task_id, current_user)


# ============================================================
# Teacher review — AI_AND_TEACHER / TEACHER_ONLY evaluation modes
# ============================================================

@router.get("/writing/pending-review", response_model=list[PendingWritingReviewItem])
def list_pending_writing_reviews(
    assessment_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return writing_service.list_pending_reviews(db, assessment_id)


@router.post("/writing/{submission_id}/review", response_model=WritingEvaluationResponse)
def review_writing_submission(
    submission_id: str,
    data: TeacherReviewInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    """Teacher sees the AI's preliminary score/feedback (via
    pending-review) plus the student's text, and can override the score —
    this is what actually finalizes it. Every criterion score is
    re-validated against its own max_score server-side; the frontend's
    numbers are never trusted as-is."""
    return writing_service.submit_teacher_review(
        db, submission_id, current_user, data.rubric_scores, data.feedback
    )
