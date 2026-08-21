from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.api.dependencies.progress import require_lesson_access
from app.db.session import get_db

from app.models.quiz import Quiz
from app.models.user import User

from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
    QuizResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
)

from app.services.quiz import QuizService, grade_and_submit

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
):
    return QuizService(db).get_all()


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
):
    quiz = QuizService(db).get(quiz_id)

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
    it liked; that endpoint's CRUD still exists for admin tooling but
    the student player no longer calls it directly."""
    return grade_and_submit(db, UUID(quiz_id), current_user, data.answers)


@router.post(
    "",
    response_model=QuizResponse,
)
def create(
    data: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return QuizService(db).create(data)


@router.put(
    "/{quiz_id}",
    response_model=QuizResponse,
)
def update(
    quiz_id: str,
    data: QuizUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    quiz = QuizService(db).update(
        quiz_id,
        data,
    )

    if not quiz:
        raise HTTPException(
            status_code=404,
            detail="Quiz not found",
        )

    return quiz


@router.delete("/{quiz_id}")
def delete(
    quiz_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    deleted = QuizService(db).delete(
        quiz_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Quiz not found",
        )

    return {
        "message": "Deleted",
    }