from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.vizu_multilevel import (
    VizuMultilevelAttemptResponse,
    VizuMultilevelAttemptResult,
    VizuMultilevelAttemptState,
    VizuMultilevelAvailability,
    VizuMultilevelCertificate,
    VizuMultilevelCompleteResponse,
    VizuMultilevelHoerenDraft,
    VizuMultilevelHoerenDraftSave,
    VizuMultilevelHoerenResult,
    VizuMultilevelHoerenSubmitRequest,
    VizuMultilevelHoerenTaskPublic,
    VizuMultilevelLesenResult,
    VizuMultilevelLesenSubmitRequest,
    VizuMultilevelSectionState,
    VizuMultilevelSpeakingEvaluation,
    VizuMultilevelSpeakingSubmissionPublic,
    VizuMultilevelSpeakingSubmitAllResponse,
    VizuMultilevelSpeakingTaskPublic,
    VizuMultilevelTaskPublic,
    VizuMultilevelWritingEvaluation,
    VizuMultilevelWritingSaveRequest,
    VizuMultilevelWritingSubmissionPublic,
    VizuMultilevelWritingSubmitAllResponse,
    VizuMultilevelWritingTaskPublic,
)
from app.services.vizu_multilevel import (
    certificate_pdf,
    certificate_service,
    hoeren_audio_service,
    hoeren_json_import_service,
    hoeren_service,
    lesen_service,
    schreiben_content,
    schreiben_evaluation_service,
    schreiben_service,
    service,
    sprechen_content,
    sprechen_evaluation_service,
    sprechen_service,
)
from app.services.vizu_multilevel.schreiben_service import SectionTimeUpError, WritingAlreadySubmittedError
from app.services.vizu_multilevel.service import SectionFlowError
from app.services.vizu_multilevel.sprechen_service import SectionTimeUpError as SpeakingTimeUpError

router = APIRouter(prefix="/vizu-multilevel", tags=["VIZU-Multilevel"])


def _own_attempt(db: Session, user: User, attempt_id: UUID):
    attempt = service.get_own_attempt(db, user.id, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    return attempt


def _flow_error(exc: SectionFlowError) -> HTTPException:
    return HTTPException(status_code=409, detail=exc.code)


# ============================================================
# Attempts / flow state
# ============================================================


@router.post("/attempts", response_model=VizuMultilevelAttemptResponse, status_code=201)
def create_attempt(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """One attempt per student, ever — a second call is a 409
    ATTEMPT_ALREADY_EXISTS (use GET /attempts/current instead)."""
    try:
        return service.create_attempt(db, current_user.id)
    except SectionFlowError as exc:
        raise _flow_error(exc)


@router.get("/attempts/current", response_model=VizuMultilevelAttemptResponse)
def get_current_attempt(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The student's single attempt (404 if not started yet)."""
    attempt = service.get_current_attempt(db, current_user.id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="No attempt yet.")
    return attempt


@router.get("/availability", response_model=VizuMultilevelAvailability)
def get_availability(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """How many items each competency has — lets the start page show an
    empty state instead of a blank test when no content exists."""
    return service.availability(db)


@router.get("/attempts", response_model=list[VizuMultilevelAttemptResponse])
def list_my_attempts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_attempts(db, current_user.id)


@router.get("/attempts/{attempt_id}", response_model=VizuMultilevelAttemptResponse)
def get_my_attempt(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _own_attempt(db, current_user, attempt_id)


@router.get("/attempts/{attempt_id}/state", response_model=VizuMultilevelAttemptState)
def get_attempt_state(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_state(_own_attempt(db, current_user, attempt_id))


@router.post("/attempts/{attempt_id}/{skill}/start", response_model=VizuMultilevelSectionState)
def start_section(
    attempt_id: UUID,
    skill: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Server-side start of a competency's 20-minute window. Idempotent —
    a reload returns the same deadline, never a fresh timer."""
    attempt = _own_attempt(db, current_user, attempt_id)
    try:
        service.start_section(db, attempt, skill)
    except SectionFlowError as exc:
        raise _flow_error(exc)
    return next(s for s in service.get_state(attempt)["sections"] if s["skill"] == skill)


@router.get("/attempts/{attempt_id}/result", response_model=VizuMultilevelAttemptResult)
def get_attempt_result(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.build_result(db, _own_attempt(db, current_user, attempt_id))


@router.post("/attempts/{attempt_id}/complete", response_model=VizuMultilevelCompleteResponse)
def complete_my_attempt(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Finishes the attempt. A result below A1 is returned once but not
    kept in the student's history (`saved: false`)."""
    try:
        outcome = service.complete_attempt(db, current_user.id, attempt_id)
    except SectionFlowError as exc:
        raise _flow_error(exc)
    if outcome is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    return outcome


@router.get("/attempts/{attempt_id}/certificate", response_model=VizuMultilevelCertificate)
def get_certificate(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Certificate data — only for the caller's own completed attempt whose
    overall result is final and at least A1. Anything else is a 404."""
    attempt = _own_attempt(db, current_user, attempt_id)
    try:
        cert = certificate_service.build_certificate(db, attempt, current_user)
    except certificate_service.CertificateUnavailable as exc:
        raise HTTPException(status_code=404, detail=f"NO_CERTIFICATE_{exc.reason}")
    return {
        "attempt_id": attempt.id,
        "student_name": cert.student_name,
        "issued_at": attempt.completed_at,
        "overall_level": cert.level,
        "competencies": service.build_result(db, attempt)["competencies"],
        "certificate_number": cert.certificate_number,
        "total_score": cert.total_score,
    }


@router.get("/attempts/{attempt_id}/certificate/pdf")
def download_certificate_pdf(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The official PDF certificate (A4 landscape). Every value comes from
    the database for the caller's OWN attempt — nothing is read from the
    request except the attempt id, and another student's id is a 404."""
    attempt = _own_attempt(db, current_user, attempt_id)
    try:
        data = certificate_service.build_certificate(db, attempt, current_user)
    except certificate_service.CertificateUnavailable as exc:
        raise HTTPException(status_code=404, detail=f"NO_CERTIFICATE_{exc.reason}")
    return certificate_pdf.certificate_pdf_response(data)


# ============================================================
# Lesen
# ============================================================


@router.get("/lesen/tasks", response_model=list[VizuMultilevelTaskPublic])
def get_lesen_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return lesen_service.list_lesen_tasks(db)


@router.post("/attempts/{attempt_id}/lesen/submit", response_model=VizuMultilevelLesenResult)
def submit_lesen_answers(
    attempt_id: UUID,
    data: VizuMultilevelLesenSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = _own_attempt(db, current_user, attempt_id)
    try:
        return lesen_service.submit_lesen(db, attempt, data.answers)
    except SectionFlowError as exc:
        raise _flow_error(exc)


@router.get("/attempts/{attempt_id}/lesen/result", response_model=VizuMultilevelLesenResult)
def get_lesen_result(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return lesen_service.get_lesen_result(db, _own_attempt(db, current_user, attempt_id))


# ============================================================
# Hören
# ============================================================


@router.get("/hoeren/tasks", response_model=list[VizuMultilevelHoerenTaskPublic])
def get_hoeren_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Never serve an empty Hören page: if no question exists at all, load the
    # bundled standard content first (see ensure_content for why this is safe).
    hoeren_json_import_service.ensure_content(db)
    return hoeren_service.list_hoeren_tasks(db)


@router.get("/attempts/{attempt_id}/hoeren/answers", response_model=VizuMultilevelHoerenDraft)
def get_hoeren_draft(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Autosaved answers, restored after a refresh."""
    return {"answers": hoeren_service.get_draft(_own_attempt(db, current_user, attempt_id))}


@router.put("/attempts/{attempt_id}/hoeren/answers", response_model=VizuMultilevelHoerenDraft)
def save_hoeren_draft(
    attempt_id: UUID,
    data: VizuMultilevelHoerenDraftSave,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = _own_attempt(db, current_user, attempt_id)
    try:
        return {"answers": hoeren_service.save_draft(db, attempt, data.answers)}
    except SectionFlowError as exc:
        raise _flow_error(exc)


@router.get("/attempts/{attempt_id}/hoeren/aufgabe/{aufgabe_number}/audio")
def stream_hoeren_audio(
    attempt_id: UUID,
    aufgabe_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The only way a student gets Hören audio bytes: the student's own
    attempt, with the Hören section opened (not yet submitted). No public
    URL, no file name, no storage path ever reaches the client."""
    attempt = _own_attempt(db, current_user, attempt_id)
    if attempt.hoeren_started_at is None or attempt.hoeren_submitted_at is not None:
        raise HTTPException(status_code=404, detail="Audio not found.")
    audio = hoeren_audio_service.get_for_aufgabe(db, aufgabe_number)
    if audio is None:
        raise HTTPException(status_code=404, detail="Audio not found.")
    path = hoeren_audio_service.resolve_path(audio)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio not found.")
    return FileResponse(path=path, media_type=audio.content_type, headers={"Cache-Control": "private, no-store"})


@router.post("/attempts/{attempt_id}/hoeren/submit", response_model=VizuMultilevelHoerenResult)
def submit_hoeren_answers(
    attempt_id: UUID,
    data: VizuMultilevelHoerenSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = _own_attempt(db, current_user, attempt_id)
    try:
        return hoeren_service.submit_hoeren(db, attempt, data.answers)
    except SectionFlowError as exc:
        raise _flow_error(exc)


@router.get("/attempts/{attempt_id}/hoeren/result", response_model=VizuMultilevelHoerenResult)
def get_hoeren_result(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return hoeren_service.get_hoeren_result(db, _own_attempt(db, current_user, attempt_id))


# ============================================================
# Schreiben
# ============================================================


@router.get("/schreiben/tasks", response_model=list[VizuMultilevelWritingTaskPublic])
def get_schreiben_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Never serve an empty Schreiben screen: create any of the 5 standard
    # Aufgaben that does not exist yet (see schreiben_content.ensure_content).
    schreiben_content.ensure_content(db)
    return schreiben_service.list_writing_tasks(db)


@router.get("/attempts/{attempt_id}/schreiben/submissions", response_model=list[VizuMultilevelWritingSubmissionPublic])
def get_schreiben_submissions(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = _own_attempt(db, current_user, attempt_id)
    return schreiben_service.get_own_submissions(db, attempt.id)


@router.put("/attempts/{attempt_id}/schreiben/save", response_model=VizuMultilevelWritingSubmissionPublic)
def save_schreiben_draft(
    attempt_id: UUID,
    data: VizuMultilevelWritingSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = _own_attempt(db, current_user, attempt_id)
    try:
        return schreiben_service.save_draft(db, attempt, data.task_id, data.content)
    except WritingAlreadySubmittedError:
        raise HTTPException(status_code=409, detail="SECTION_ALREADY_SUBMITTED")
    except SectionTimeUpError:
        raise HTTPException(status_code=409, detail="SECTION_TIME_UP")
    except SectionFlowError as exc:
        raise _flow_error(exc)
    except LookupError:
        raise HTTPException(status_code=404, detail="Writing task not found.")


@router.post("/attempts/{attempt_id}/schreiben/submit", response_model=VizuMultilevelWritingSubmitAllResponse)
def submit_schreiben(
    attempt_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Final submission: all 5 Aufgaben required (MIN_ANSWERS_REQUIRED
    otherwise), answers are locked, a second call is 409
    SECTION_ALREADY_SUBMITTED. The AI evaluation then runs server-side in
    the background — poll GET .../schreiben/evaluation."""
    attempt = _own_attempt(db, current_user, attempt_id)
    try:
        attempt = schreiben_service.submit_all(db, attempt)
    except SectionFlowError as exc:
        raise _flow_error(exc)
    background_tasks.add_task(schreiben_evaluation_service.run_for_attempt, attempt.id)
    return {"attempt_id": attempt.id, "schreiben_submitted_at": attempt.schreiben_submitted_at}


@router.get("/attempts/{attempt_id}/schreiben/evaluation", response_model=VizuMultilevelWritingEvaluation)
def get_schreiben_evaluation(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Evaluation state and — once DONE — the per-Aufgabe scores, verified
    errors with corrections, feedback and the overall summary. Read-only:
    there is no way for a client to send or change points."""
    attempt = _own_attempt(db, current_user, attempt_id)
    return schreiben_evaluation_service.build_student_result(db, attempt)


@router.post("/attempts/{attempt_id}/schreiben/evaluation/retry", response_model=VizuMultilevelWritingEvaluation)
def retry_schreiben_evaluation(
    attempt_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-queues Aufgaben whose evaluation FAILED (e.g. AI temporarily
    unavailable). Never re-scores Aufgaben that are already DONE."""
    attempt = _own_attempt(db, current_user, attempt_id)
    result = schreiben_evaluation_service.build_student_result(db, attempt)
    if result["status"] != "FAILED":
        raise HTTPException(status_code=409, detail="EVALUATION_NOT_FAILED")
    background_tasks.add_task(schreiben_evaluation_service.run_for_attempt, attempt.id)
    return result


# ============================================================
# Sprechen
# ============================================================


@router.get("/sprechen/tasks", response_model=list[VizuMultilevelSpeakingTaskPublic])
def get_sprechen_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The 5 Aufgaben a student gets (ladder; no level exposed). Never serve
    an empty Sprechen screen: missing standard variants are created first."""
    sprechen_content.ensure_content(db)
    return sprechen_service.assigned_tasks(db)


@router.get("/attempts/{attempt_id}/sprechen/tasks", response_model=list[VizuMultilevelSpeakingTaskPublic])
def get_attempt_sprechen_tasks(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """This attempt's 5 Aufgaben (answered ones keep their task)."""
    attempt = _own_attempt(db, current_user, attempt_id)
    sprechen_content.ensure_content(db)
    return sprechen_service.attempt_tasks(db, attempt.id)


@router.get("/attempts/{attempt_id}/sprechen/submissions", response_model=list[VizuMultilevelSpeakingSubmissionPublic])
def get_sprechen_submissions(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = _own_attempt(db, current_user, attempt_id)
    return sprechen_service.get_own_submissions(db, attempt.id)


@router.post("/attempts/{attempt_id}/sprechen/upload", response_model=VizuMultilevelSpeakingSubmissionPublic)
async def upload_sprechen_recording(
    attempt_id: UUID,
    background_tasks: BackgroundTasks,
    task_id: UUID = Form(...),
    duration_seconds: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """"Antwort speichern": stores the audio once (409 ANSWER_ALREADY_SAVED
    on a second save, 409 PREVIOUS_TASK_REQUIRED out of order) and starts
    speech-to-text + AI evaluation in the background."""
    attempt = _own_attempt(db, current_user, attempt_id)
    try:
        submission = await sprechen_service.upload_recording(db, attempt, task_id, file, duration_seconds)
    except SpeakingTimeUpError:
        raise HTTPException(status_code=409, detail="SECTION_TIME_UP")
    except SectionFlowError as exc:
        raise _flow_error(exc)
    background_tasks.add_task(sprechen_evaluation_service.process_submission, submission.id)
    return submission


@router.get("/attempts/{attempt_id}/sprechen/submissions/{submission_id}/audio")
def get_sprechen_audio(
    attempt_id: UUID,
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Owner-only playback of the student's own recording — 404 for any
    other student's attempt/submission, exactly like a nonexistent id."""
    attempt = _own_attempt(db, current_user, attempt_id)
    submission = sprechen_service.get_own_submission(db, attempt.id, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Recording not found.")
    path = sprechen_service.resolve_audio_path(submission)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file missing on disk.")
    return FileResponse(path=path, media_type=submission.content_type)


@router.post("/attempts/{attempt_id}/sprechen/submit", response_model=VizuMultilevelSpeakingSubmitAllResponse)
def submit_sprechen(
    attempt_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = _own_attempt(db, current_user, attempt_id)
    try:
        attempt = sprechen_service.submit_all(db, attempt)
    except SectionFlowError as exc:
        raise _flow_error(exc)
    # Finishes anything still pending (and the Sprechen result once all 5 are evaluated).
    background_tasks.add_task(sprechen_evaluation_service.run_pending, attempt.id)
    return {"attempt_id": attempt.id, "sprechen_submitted_at": attempt.sprechen_submitted_at}


@router.get("/attempts/{attempt_id}/sprechen/evaluation", response_model=VizuMultilevelSpeakingEvaluation)
def get_sprechen_evaluation(
    attempt_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Per-answer pipeline progress while the test runs; after the final
    submit the full result (score /100, level, 5 Aufgaben with feedback).
    Self-healing: answers stuck without a live worker are re-queued."""
    attempt = _own_attempt(db, current_user, attempt_id)
    if attempt.sprechen_submitted_at is not None and any(
        s.status != sprechen_service.FAILED
        for s in sprechen_service.get_own_submissions(db, attempt.id)
        if s.id in sprechen_evaluation_service.pending_submission_ids(db, attempt.id)
    ):
        background_tasks.add_task(sprechen_evaluation_service.run_pending, attempt.id)
    return sprechen_evaluation_service.build_student_result(db, attempt)


@router.post("/attempts/{attempt_id}/sprechen/evaluation/retry", response_model=VizuMultilevelSpeakingEvaluation)
def retry_sprechen_evaluation(
    attempt_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-runs only answers whose processing FAILED (audio is never lost).
    409 if nothing failed. Students cannot influence scores here."""
    attempt = _own_attempt(db, current_user, attempt_id)
    failed = [s for s in sprechen_service.get_own_submissions(db, attempt.id) if s.status == sprechen_service.FAILED]
    if not failed:
        raise HTTPException(status_code=409, detail="NOTHING_TO_RETRY")
    background_tasks.add_task(sprechen_evaluation_service.run_pending, attempt.id)
    return sprechen_evaluation_service.build_student_result(db, attempt)


# ============================================================
# Legacy alias: /vizu-mock/attempts*
#
# The module was renamed VIZU-Mock -> VIZU-Multilevel, but a frontend build
# that predates the rename still calls /api/v1/vizu-mock/attempts. These
# four routes reuse the SAME handlers (same auth, same owner scoping), so
# no logic is duplicated; they are hidden from the OpenAPI schema.
# ============================================================

legacy_router = APIRouter(prefix="/vizu-mock", tags=["VIZU-Mock (legacy alias)"], include_in_schema=False)
legacy_router.add_api_route("/attempts", create_attempt, methods=["POST"], response_model=VizuMultilevelAttemptResponse, status_code=201)
legacy_router.add_api_route("/attempts", list_my_attempts, methods=["GET"], response_model=list[VizuMultilevelAttemptResponse])
legacy_router.add_api_route("/availability", get_availability, methods=["GET"], response_model=VizuMultilevelAvailability)
legacy_router.add_api_route("/attempts/current", get_current_attempt, methods=["GET"], response_model=VizuMultilevelAttemptResponse)
legacy_router.add_api_route("/attempts/{attempt_id}", get_my_attempt, methods=["GET"], response_model=VizuMultilevelAttemptResponse)
legacy_router.add_api_route(
    "/attempts/{attempt_id}/complete", complete_my_attempt, methods=["POST"], response_model=VizuMultilevelCompleteResponse
)
# Hören under the legacy /vizu-mock prefix — the SAME handlers (same
# owner-scoping, protected audio streaming, autosave, server-side grading),
# so /vizu-mock/hoeren/* and /vizu-multilevel/hoeren/* can never diverge.
legacy_router.add_api_route("/attempts/{attempt_id}/state", get_attempt_state, methods=["GET"], response_model=VizuMultilevelAttemptState)
legacy_router.add_api_route(
    "/attempts/{attempt_id}/{skill}/start", start_section, methods=["POST"], response_model=VizuMultilevelSectionState
)
legacy_router.add_api_route("/hoeren/tasks", get_hoeren_tasks, methods=["GET"], response_model=list[VizuMultilevelHoerenTaskPublic])
legacy_router.add_api_route(
    "/attempts/{attempt_id}/hoeren/answers", get_hoeren_draft, methods=["GET"], response_model=VizuMultilevelHoerenDraft
)
legacy_router.add_api_route(
    "/attempts/{attempt_id}/hoeren/answers", save_hoeren_draft, methods=["PUT"], response_model=VizuMultilevelHoerenDraft
)
legacy_router.add_api_route("/attempts/{attempt_id}/hoeren/aufgabe/{aufgabe_number}/audio", stream_hoeren_audio, methods=["GET"])
legacy_router.add_api_route(
    "/attempts/{attempt_id}/hoeren/submit", submit_hoeren_answers, methods=["POST"], response_model=VizuMultilevelHoerenResult
)
legacy_router.add_api_route(
    "/attempts/{attempt_id}/hoeren/result", get_hoeren_result, methods=["GET"], response_model=VizuMultilevelHoerenResult
)

legacy_router.add_api_route(
    "/attempts/{attempt_id}/schreiben/evaluation",
    get_schreiben_evaluation,
    methods=["GET"],
    response_model=VizuMultilevelWritingEvaluation,
)
