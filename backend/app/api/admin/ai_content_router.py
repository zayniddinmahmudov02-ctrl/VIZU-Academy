"""AI-assisted content authoring (Feature 3). Every endpoint here only
ever returns a JSON preview — none of them write to the database. An
admin turns a preview into real content by clicking "Übernehmen" on the
frontend, which calls the *existing* manual create endpoints
(quiz-questions/quiz-options for Grammatik, the Assessment Engine's
task/question/option/rubric-criterion endpoints for Lesen/Hören/
Schreiben/Sprechen) exactly as if it had been typed by hand — so "AI
output must not publish automatically" holds structurally, not behind a
flag: there is no code path from "Gemini responded" to "a student can
see this" without two explicit admin actions (Übernehmen, then the
existing publish toggle) in between."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.auth import require_admin_panel_access
from app.models.user import User

from app.schemas.ai_content import (
    AIGenerateRequest,
    AIGrammarQuizPreview,
    AIHoerenPreview,
    AILesenPreview,
    AISchreibenPreview,
    AISprechenPreview,
)

from app.services.ai_content import (
    AIContentError,
    generate_grammar_quiz,
    generate_hoeren,
    generate_lesen,
    generate_schreiben,
    generate_sprechen,
)

router = APIRouter(
    prefix="/admin/ai-content",
    tags=["Admin - AI Content Generation"],
)


@router.post("/grammar-quiz/generate", response_model=AIGrammarQuizPreview)
async def generate_grammar_quiz_preview(
    data: AIGenerateRequest,
    current_user: User = Depends(require_admin_panel_access),
):
    try:
        return await generate_grammar_quiz(data.source_text, data.level, data.count)
    except AIContentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/lesen/generate", response_model=AILesenPreview)
async def generate_lesen_preview(
    data: AIGenerateRequest,
    current_user: User = Depends(require_admin_panel_access),
):
    try:
        return await generate_lesen(data.source_text, data.level, data.count)
    except AIContentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/hoeren/generate", response_model=AIHoerenPreview)
async def generate_hoeren_preview(
    data: AIGenerateRequest,
    current_user: User = Depends(require_admin_panel_access),
):
    try:
        return await generate_hoeren(data.source_text, data.level, data.count)
    except AIContentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


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
