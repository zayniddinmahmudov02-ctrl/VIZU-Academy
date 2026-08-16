"""Formerly enforced sequential-section access; sections are now
independently accessible in any order, so these dependencies are
permanent no-ops — kept (rather than stripped from every router) so call
sites don't need to change and Premium/lesson-access checks elsewhere are
unaffected. Deliberately doesn't call SectionGateService at all anymore
(unlike a version that just made `is_unlocked` return True): that would
still pay for a full DB round-trip every request only to get a constant
back."""

from uuid import UUID

from fastapi import Depends

from app.api.dependencies.auth import get_current_user
from app.models.user import User


def _require_section_unlocked(section: str):
    async def _dependency(
        # Kept as a path param so a malformed lesson_id still 400s here,
        # same as before this dependency stopped enforcing anything else.
        lesson_id: UUID,
        current_user: User = Depends(get_current_user),
    ) -> User:
        return current_user

    return _dependency


require_grammar_unlocked = _require_section_unlocked("grammatik")
require_grammar_quiz_unlocked = _require_section_unlocked("grammatik_quiz")
require_lesen_unlocked = _require_section_unlocked("lesen")
require_lesson_quiz_unlocked = _require_section_unlocked("lesson_quiz")
