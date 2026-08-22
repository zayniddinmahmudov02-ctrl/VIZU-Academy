"""Server-side grading for the legacy Quiz/QuizQuestion/QuizOption
system (GRAMMAR/LESSON/VOCABULARY quiz_types) — replaces the previous
100%-client-side grading, which structurally required the correct
answer to be present in what the frontend fetched. The comparison
rules per question_type mirror exactly what quiz-section.tsx used to
compute locally; only where that computation happens has moved.

Scoring is a plain correct/total percentage, matching the pre-existing
client-side behavior exactly (QuizQuestion.points is not weighted into
the score — it never was, even before this change; preserving that
observable behavior rather than "fixing" it here).
"""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.lesson import Lesson
from app.models.quiz import QUIZ_TYPE_VOCABULARY, Quiz
from app.models.quiz_question import QuizQuestion
from app.models.student_progress import StudentProgress
from app.models.user import User

from app.schemas.quiz import (
    QuizAnswerResult,
    QuizAnswerSubmit,
    QuizSubmitResponse,
)
from app.schemas.student_quiz import StudentQuizCreate

from app.services.student_quiz import StudentQuizService
from app.services.vizu_pay.access import can_access_lesson

TEXT_ANSWER_TYPES = {"CLOZE_TEXT", "SENTENCE_COMPLETION"}
ORDERING_TYPES = {"SENTENCE_ORDERING"}
MATCHING_TYPES = {"MATCHING"}


def _normalize(text: str) -> str:
    return text.strip().lower()


def _grade_question(question: QuizQuestion, answer: QuizAnswerSubmit | None) -> tuple[bool | None, QuizAnswerResult]:
    """Returns (is_correct_or_None_if_skipped, reveal_result)."""

    options = list(question.options)

    if question.question_type in TEXT_ANSWER_TYPES:
        correct_text = question.correct_text_answer or ""
        result = QuizAnswerResult(question_id=question.id, is_correct=False, correct_text_answer=correct_text)
        if answer is None or not (answer.text_answer or "").strip():
            return None, result
        is_correct = _normalize(answer.text_answer or "") == _normalize(correct_text)
        result.is_correct = is_correct
        return is_correct, result

    if question.question_type in ORDERING_TYPES:
        correct_order = [o.id for o in sorted(options, key=lambda o: o.order_index)]
        result = QuizAnswerResult(question_id=question.id, is_correct=False, correct_order_option_ids=correct_order)
        if answer is None or not answer.ordered_option_ids:
            return None, result
        is_correct = answer.ordered_option_ids == correct_order
        result.is_correct = is_correct
        return is_correct, result

    if question.question_type in MATCHING_TYPES:
        correct_matches = {str(o.id): (o.match_value or "") for o in options}
        result = QuizAnswerResult(question_id=question.id, is_correct=False, correct_matches=correct_matches)
        if answer is None or not answer.matches:
            return None, result
        is_correct = all(answer.matches.get(option_id) == value for option_id, value in correct_matches.items())
        result.is_correct = is_correct
        return is_correct, result

    # MULTIPLE_CHOICE / TRUE_FALSE / ERROR_FINDING — pick-the-correct-option.
    correct_option = next((o for o in options if o.is_correct), None)
    result = QuizAnswerResult(
        question_id=question.id,
        is_correct=False,
        correct_option_id=correct_option.id if correct_option else None,
    )
    if answer is None or answer.option_id is None:
        return None, result
    is_correct = correct_option is not None and answer.option_id == correct_option.id
    result.is_correct = is_correct
    return is_correct, result


def grade_and_submit(
    db: Session,
    quiz_id: UUID,
    user: User,
    answers: list[QuizAnswerSubmit],
) -> QuizSubmitResponse:
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")

    lesson = db.get(Lesson, quiz.lesson_id)
    if lesson is None or not can_access_lesson(user, lesson):
        raise HTTPException(status_code=403, detail="PREMIUM_REQUIRED")

    if quiz.quiz_type == QUIZ_TYPE_VOCABULARY:
        # Narrow, quiz-local gate (not a revival of the old sequential
        # section lock): the Wortschatz Quiz requires its own vocabulary
        # learning step to be done first, enforced server-side so it
        # can't be bypassed via a direct API call.
        progress = (
            db.query(StudentProgress)
            .filter(StudentProgress.user_id == str(user.id), StudentProgress.lesson_id == str(lesson.id))
            .first()
        )
        if not (progress and progress.vocabulary_completed):
            raise HTTPException(status_code=403, detail="VOCABULARY_NOT_COMPLETED")

    questions = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.quiz_id == quiz.id, QuizQuestion.is_published.is_(True))
        .order_by(QuizQuestion.order_index)
        .all()
    )
    answers_by_question = {a.question_id: a for a in answers}

    correct = 0
    wrong = 0
    skipped = 0
    results: list[QuizAnswerResult] = []

    for question in questions:
        is_correct, result = _grade_question(question, answers_by_question.get(question.id))
        results.append(result)
        if is_correct is None:
            skipped += 1
        elif is_correct:
            correct += 1
        else:
            wrong += 1

    total = len(questions)
    score = round(correct / total * 100) if total > 0 else 0
    passed = score >= quiz.passing_score

    StudentQuizService(db).create(
        StudentQuizCreate(
            user_id=str(user.id),
            quiz_id=str(quiz.id),
            correct_answers=correct,
            wrong_answers=wrong,
            skipped_answers=skipped,
            score=score,
            passed=passed,
        )
    )

    return QuizSubmitResponse(
        score=score,
        correct_answers=correct,
        wrong_answers=wrong,
        skipped_answers=skipped,
        passed=passed,
        results=results,
    )
