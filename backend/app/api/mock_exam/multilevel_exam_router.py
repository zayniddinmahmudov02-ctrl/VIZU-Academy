"""Multilevel exam mode — rules in app/services/mock_exam/multilevel_exam_service.py.

Student (`get_current_user`, own attempts only; someone else's attempt is a 404): /multilevel-exam/...
Staff: results + recordings + statistics `require_teacher_panel_access` (teachers grade Schreiben / Sprechen),
preview `require_admin_panel_access`, scoring settings read `require_admin_panel_access` / write `require_super_admin`."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Path, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access, require_super_admin, require_teacher_panel_access
from app.db.session import get_db
from app.models.user import User
from app.services.mock_exam import multilevel_exam_service as svc

router = APIRouter(prefix="/multilevel-exam", tags=["Multilevel exam (student)"])
admin_router = APIRouter(prefix="/admin/multilevel-exam", tags=["Multilevel exam (staff)"])

SectionType = Path(pattern="^(LESEN|HOEREN|SCHREIBEN|SPRECHEN)$")


class StartAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_test_id: UUID


class AnswerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: UUID
    option_ids: list[UUID] = Field(default_factory=list, max_length=20)


class WritingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer_text: str = Field(default="", max_length=svc.MAX_TEXT)


class GradeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    score: int = Field(ge=0, le=svc.SECTION_MAX)
    feedback: str | None = Field(default=None, max_length=5000)


class SettingsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    score_50: str = Field(pattern="^(UNGEKLAERT|B1|B2)$")
    overall_rule: str = Field(pattern="^(UNCONFIRMED|AVERAGE|LOWEST)$")


def _private_audio(path, media_type: str) -> FileResponse:
    return FileResponse(path, media_type=media_type, headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


# ── student ────────────────────────────────────────────────────


@router.get("/exams")
def list_exams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.list_exams(db, user)


@router.get("/history")
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.history(db, user)


@router.post("/attempts")
def start_attempt(data: StartAttempt, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    attempt = svc.start_attempt(db, user, data.model_test_id)
    return svc.attempt_view(db, user, attempt.id)


@router.get("/attempts/{attempt_id}")
def attempt_view(attempt_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.attempt_view(db, user, attempt_id)


@router.post("/attempts/{attempt_id}/sections/{section_type}/start")
def start_section(attempt_id: UUID, section_type: str = SectionType, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    svc.start_section(db, user, attempt_id, section_type)
    return svc.section_paper(db, user, attempt_id, section_type)


@router.get("/attempts/{attempt_id}/sections/{section_type}")
def section_paper(attempt_id: UUID, section_type: str = SectionType, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.section_paper(db, user, attempt_id, section_type)


@router.put("/attempts/{attempt_id}/sections/{section_type}/answers")
def save_answer(attempt_id: UUID, data: AnswerIn, section_type: str = SectionType, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    return svc.save_answer(db, user, attempt_id, section_type, data.question_id, data.option_ids)


@router.put("/attempts/{attempt_id}/writing/{writing_task_id}")
def save_writing(attempt_id: UUID, writing_task_id: UUID, data: WritingIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.save_writing(db, user, attempt_id, writing_task_id, data.answer_text)


@router.post("/attempts/{attempt_id}/speaking/{speaking_task_id}")
async def upload_recording(attempt_id: UUID, speaking_task_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db),
                           user: User = Depends(get_current_user)):
    return await svc.upload_recording(db, user, attempt_id, speaking_task_id, file)


@router.post("/attempts/{attempt_id}/sections/{section_type}/submit")
def submit_section(attempt_id: UUID, section_type: str = SectionType, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.submit_section(db, user, attempt_id, section_type)


@router.post("/attempts/{attempt_id}/finish")
def finish_attempt(attempt_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.finish_attempt(db, user, attempt_id)


@router.get("/attempts/{attempt_id}/results")
def results(attempt_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.results(db, user, attempt_id)


@router.get("/recordings/{submission_id}")
def own_recording(submission_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _private_audio(*svc.recording_file(db, user, submission_id, staff=False))


# ── staff ──────────────────────────────────────────────────────


@admin_router.get("/attempts")
def admin_attempts(model_test_id: UUID | None = None, status: str | None = None, db: Session = Depends(get_db),
                   _: User = Depends(require_teacher_panel_access)):
    return svc.admin_attempts(db, model_test_id, status)


@admin_router.get("/attempts/{attempt_id}")
def admin_attempt(attempt_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_teacher_panel_access)):
    return svc.admin_attempt_detail(db, attempt_id)


@admin_router.put("/attempts/{attempt_id}/sections/{section_type}/grade")
def grade_section(attempt_id: UUID, data: GradeIn, section_type: str = SectionType, db: Session = Depends(get_db),
                  user: User = Depends(require_teacher_panel_access)):
    return svc.grade_section(db, user, attempt_id, section_type, data.score, data.feedback)


@admin_router.get("/recordings/{submission_id}")
def staff_recording(submission_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_teacher_panel_access)):
    return _private_audio(*svc.recording_file(db, user, submission_id, staff=True))


@admin_router.get("/statistics")
def statistics(db: Session = Depends(get_db), _: User = Depends(require_teacher_panel_access)):
    return svc.statistics(db)


@admin_router.get("/model-tests/{model_test_id}/preview")
def preview(model_test_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return svc.admin_preview(db, model_test_id)


@admin_router.get("/settings")
def get_settings(db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return svc.get_settings(db) | {"score_50_choices": list(svc.SCORE_50_CHOICES), "overall_rules": list(svc.OVERALL_RULES)}


@admin_router.put("/settings")
def put_settings(data: SettingsIn, db: Session = Depends(get_db), user: User = Depends(require_super_admin)):
    return svc.update_settings(db, user, data.score_50, data.overall_rule)
