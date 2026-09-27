"""AI-assisted content authoring (Feature 3) — Schreiben/Sprechen only.
Grammar-quiz/Lesen/Hören preview generation was removed along with their
manual "Übernehmen" target endpoints (Lesen/Hören/quiz question authoring
is no longer done in the admin panel). Every endpoint here still only
ever returns a JSON preview — none of them write to the database. An
admin turns a preview into real content by clicking "Übernehmen" on the
frontend, which calls the *existing* manual create endpoints (the
Assessment Engine's task/rubric-criterion endpoints for Schreiben/
Sprechen) exactly as if it had been typed by hand — so "AI output must
not publish automatically" holds structurally, not behind a flag: there
is no code path from "Gemini responded" to "a student can see this"
without two explicit admin actions (Übernehmen, then the existing
publish toggle) in between."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.auth import require_admin_panel_access
from app.models.user import User

from app.schemas.ai_content import (
    AIGenerateRequest,
    AISchreibenPreview,
    AISprechenPreview,
)

from app.services.ai_content import (
    AIContentError,
    generate_schreiben,
    generate_sprechen,
)

router = APIRouter(
    prefix="/admin/ai-content",
    tags=["Admin - AI Content Generation"],
)


@router.post("/schreiben/generate", response_model=AISchreibenPreview)
async def generate_schreiben_preview(
    data: AIGenerateRequest,
    current_user: User = Depends(require_admin_panel_access),
):
    try:
        return await generate_schreiben(data.source_text, data.level)
    except AIContentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/sprechen/generate", response_model=AISprechenPreview)
async def generate_sprechen_preview(
    data: AIGenerateRequest,
    current_user: User = Depends(require_admin_panel_access),
):
    try:
        return await generate_sprechen(data.source_text, data.level)
    except AIContentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
