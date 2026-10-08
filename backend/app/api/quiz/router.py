from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.api.dependencies.progress import require_lesson_access
from app.db.session import get_db

from app.models.quiz import Quiz
from app.models.user import User

from app.schemas.quiz import (
    QuizResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
)

from app.services.quiz import grade_and_submit

router = APIRouter(
    prefix="/quizzes",
    tags=["Quizzes"],
)


@router.get(
    "",
    response_model=list[QuizResponse],
)
def get_all(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_panel_access),
):
    # Manual quiz authoring was removed from the admin panel (Claude-
    # generated content is inserted directly into the DB instead); this
    # read is kept because the student quiz player still needs it.
    return db.query(Quiz).order_by(Quiz.order_index).all()


@router.get(
    "/lesson/{lesson_id}",
    response_model=list[QuizResponse],
)
def get_lesson_quizzes(
    lesson_id: str,
    quiz_type: str | None = None,
    published_only: bool = False,
    db: Session = Depends(get_db),
    __: User = Depends(require_lesson_access),
):
    """Optionally filtered by quiz_type (GRAMMAR/LESSON) — the lesson
    player uses this to fetch the mid-lesson Grammatik Quiz and the
    end-of-lesson Lesson Quiz as two distinct requests. Sections are no
    longer sequentially gated; require_lesson_access still applies the
    free-3-lessons-per-level / Premium rule."""
    query = db.query(Quiz).filter(Quiz.lesson_id == lesson_id)
    if quiz_type:
        query = query.filter(Quiz.quiz_type == quiz_type)
    if published_only:
        query = query.filter(Quiz.is_published.is_(True))
    return query.order_by(Quiz.order_index).all()


@router.get(
    "/{quiz_id}",
    response_model=QuizResponse,
)
def get_one(
    quiz_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_panel_access),
):
    """Admin panel only (it bypasses the per-lesson access gate); students
    get their quizzes via GET /quizzes/lesson/{id}."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()

    if not quiz:
        raise HTTPException(
            status_code=404,
            detail="Quiz not found",
        )

    return quiz


@router.post(
    "/{quiz_id}/submit",
    response_model=QuizSubmitResponse,
)
def submit_quiz(
    quiz_id: str,
    data: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The only way a student's answers are graded — server-side,
    against questions/options freshly loaded from the DB, never
    trusting anything the client claims about correctness (see
    app/services/quiz/grading_service.py). Replaces the old
    POST /student-quizzes flow, which let the client report any score
    it liked."""
    return grade_and_submit(db, UUID(quiz_id), current_user, data.answers)