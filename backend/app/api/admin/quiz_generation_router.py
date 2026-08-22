"""Deterministic (no AI) quiz question generation — see
app/services/quiz_generation/quiz_generation_service.py. Unlike
ai_content_router.py, generation here writes directly to the database
(no separate preview/apply step): the template engine is
correctness-guaranteed by construction (exactly 1 correct answer per
question, no external content to hallucinate), so there is nothing an
admin needs to fact-check before it exists as a draft — it still starts
unpublished (is_published=False), same as every other creation path,
until an admin reviews and publishes through the existing UI."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db
from app.models.user import User
from app.schemas.quiz_generation import (
    QuizGenerationRequest,
    QuizGenerationResponse,
    QuizGenerationTopicsResponse,
)
from app.services.quiz_generation import (
    QuizGenerationError,
    generate_quiz,
    list_topics_for_lesson,
)

router = APIRouter(
    prefix="/admin/quiz-generation",
    tags=["Admin - Deterministic Quiz Generation"],
)


@router.get("/topics", response_model=QuizGenerationTopicsResponse)
def get_topics(
    lesson_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    try:
        return list_topics_for_lesson(db, lesson_id)
    except QuizGenerationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/generate", response_model=QuizGenerationResponse)
def generate(
    data: QuizGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    try:
        result = generate_quiz(
            db,
            quiz_id=data.quiz_id,
            lesson_id=data.lesson_id,
            topic=data.topic,
            count=data.count,
            question_types=data.question_types,
            seed=data.seed,
        )
    except QuizGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return QuizGenerationResponse(
        quiz_id=result.quiz_id,
        created_count=result.created_count,
        requested_count=result.requested_count,
        shortfall=result.shortfall,
        message=result.message,
    )
