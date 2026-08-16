"""Server-side sequential-section gates — direct-URL/direct-API access to
a locked section must fail the same as the frontend hiding its button
(see section 18 of the spec this backs). Admin/staff always bypass, same
`ADMIN_PANEL_ROLES` check used by every other bypass in this codebase
(app.services.vizu_pay.access.has_premium_bypass)."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.security.roles import UserRole
from app.db.session import get_db
from app.models.user import User
from app.services.lesson_progress import SectionGateService


def _require_section_unlocked(section: str):
    async def _dependency(
        lesson_id: UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if current_user.role in UserRole.ADMIN_PANEL_ROLES:
            return current_user

        if not SectionGateService(db).is_unlocked(current_user.id, lesson_id, section):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="LESSON_SECTION_LOCKED",
            )

        return current_user

    return _dependency


require_grammar_unlocked = _require_section_unlocked("grammatik")
require_grammar_quiz_unlocked = _require_section_unlocked("grammatik_quiz")
require_lesen_unlocked = _require_section_unlocked("lesen")
require_lesson_quiz_unlocked = _require_section_unlocked("lesson_quiz")
