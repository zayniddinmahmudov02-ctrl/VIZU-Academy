"""Real sequential-section access enforcement, for routes shaped with
`lesson_id` as a path parameter — a student can't open a gated endpoint
via a direct API call before the section-gate says it's unlocked (see
app/services/lesson_progress/section_gate.py, the single source of
truth this delegates to). Lesen/Hören/Schreiben/Sprechen's submission
endpoints are keyed by attempt_id/task_id instead (no lesson_id path
param), so their equivalent gate is enforced inline in
attempt_service.submit_answer / writing_service.submit_submission /
speaking_service.upload_submission; the legacy Quiz system's equivalent
lives in app/services/quiz/grading_service.py. All four call the same
underlying SectionGateService.is_unlocked check — one source of truth,
different call sites to match each route's shape."""

from uuid import UUID

from fastapi import Depends, HTTPException

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.lesson_progress.section_gate import SectionGateService
from sqlalchemy.orm import Session


def _require_section_unlocked(section: str):
    async def _dependency(
        lesson_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not SectionGateService(db).is_unlocked(current_user.id, lesson_id, section):
            raise HTTPException(status_code=403, detail="SECTION_LOCKED")
        return current_user

    return _dependency


require_grammar_unlocked = _require_section_unlocked("grammatik")
require_grammar_quiz_unlocked = _require_section_unlocked("grammatik_quiz")
require_lesen_unlocked = _require_section_unlocked("lesen")
require_lesson_quiz_unlocked = _require_section_unlocked("lesson_quiz")
