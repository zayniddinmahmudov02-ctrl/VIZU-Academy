"""What a non-staff caller may read of the legacy quiz tables (GET /quiz-questions, /quiz-options).

Until 2026-11-14 these lists returned every question / option of every lesson to anyone (keys stripped), so the
test content of paid lessons was readable without a purchase. Now a caller gets only items of PUBLISHED quizzes whose
lesson they may open — the one LMS gate (`lms.access.lesson_access`: free first lesson, purchase, staff). `quiz_id`
narrows the list to one quiz (what the lesson player asks for); a closed quiz then answers with the gate's own error.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lesson import Lesson
from app.models.quiz import Quiz
from app.models.quiz_option import QuizOption
from app.models.quiz_question import QuizQuestion
from app.models.user import User
from app.services.lms.access import ensure_lesson_open, lesson_access


def open_quiz_ids(db: Session, user: User | None, quiz_id: UUID | None = None) -> set:
    """Ids of published quizzes in lessons the caller may open. With `quiz_id`: that quiz or a 404 / 403."""
    if quiz_id is not None:
        quiz = db.get(Quiz, quiz_id)
        lesson = db.get(Lesson, quiz.lesson_id) if quiz is not None and quiz.is_published else None
        if lesson is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Quiz not found")
        ensure_lesson_open(db, user, lesson)
        return {quiz.id}
    rows = db.execute(select(Quiz.id, Quiz.lesson_id).where(Quiz.is_published.is_(True))).all()
    lessons = {lesson.id: lesson for lesson in db.scalars(select(Lesson).where(Lesson.id.in_({r.lesson_id for r in rows})))} if rows else {}
    open_lessons = {lid for lid, lesson in lessons.items() if lesson_access(db, user, lesson).unlocked}
    return {r.id for r in rows if r.lesson_id in open_lessons}


def visible_questions(db: Session, user: User | None, quiz_id: UUID | None = None) -> list[QuizQuestion]:
    ids = open_quiz_ids(db, user, quiz_id)
    if not ids:
        return []
    return list(db.scalars(select(QuizQuestion).where(QuizQuestion.quiz_id.in_(ids), QuizQuestion.is_published.is_(True))
                           .order_by(QuizQuestion.order_index)))


def visible_options(db: Session, user: User | None, quiz_id: UUID | None = None) -> list[QuizOption]:
    ids = open_quiz_ids(db, user, quiz_id)
    if not ids:
        return []
    return list(db.scalars(select(QuizOption).join(QuizQuestion, QuizOption.question_id == QuizQuestion.id)
                           .where(QuizQuestion.quiz_id.in_(ids), QuizQuestion.is_published.is_(True)).order_by(QuizOption.order_index)))


def ensure_question_open(db: Session, user: User | None, question: QuizQuestion) -> None:
    """One question by id: published, in a published quiz of a lesson the caller may open (else 404 / 403)."""
    from fastapi import HTTPException

    if not question.is_published:
        raise HTTPException(status_code=404, detail="Question not found")
    open_quiz_ids(db, user, question.quiz_id)
