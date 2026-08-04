from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.kompetenz import Kompetenz
from app.models.mock_question import MockQuestion
from app.models.mock_question_answer import MockQuestionAnswer
from app.models.mock_speaking_submission import MockSpeakingSubmission
from app.models.mock_test_attempt import STATUS_GRADED, STATUS_IN_PROGRESS, MockTestAttempt
from app.models.mock_writing_submission import MockWritingSubmission
from app.models.speaking_task import SpeakingTask
from app.models.teil import Teil
from app.models.writing_task import WritingTask
from app.schemas.mock_exam import (
    MockQuestionAnswerCreate,
    MockSpeakingSubmissionCreate,
    MockSpeakingSubmissionTeacherUpdate,
    MockTestAttemptCreate,
    MockWritingSubmissionCreate,
    MockWritingSubmissionTeacherUpdate,
)
from app.services.mock_exam.ai_service import AIServiceError, evaluate_speaking, evaluate_writing


# ============================================================
# Attempts (admin-visible "Student Results" view)
# ============================================================


def get_attempts(
    db: Session,
    model_test_id: UUID | None = None,
    user_id: UUID | None = None,
):
    query = select(MockTestAttempt).order_by(MockTestAttempt.started_at.desc())
    if model_test_id:
        query = query.where(MockTestAttempt.model_test_id == model_test_id)
    if user_id:
        query = query.where(MockTestAttempt.user_id == user_id)
    return db.scalars(query).all()


def get_attempt(db: Session, attempt_id: UUID):
    return db.get(MockTestAttempt, attempt_id)


def create_attempt(db: Session, user_id: UUID, data: MockTestAttemptCreate) -> MockTestAttempt:
    attempt = MockTestAttempt(
        model_test_id=data.model_test_id,
        user_id=user_id,
        status=STATUS_IN_PROGRESS,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def finalize_attempt(db: Session, attempt_id: UUID, time_spent_seconds: int) -> MockTestAttempt | None:
    """Sums points_earned across question answers plus AI/teacher scores
    from writing and speaking submissions to produce total_score, and the
    configured Teil points for the whole Model Test as max_score."""
    attempt = db.get(MockTestAttempt, attempt_id)
    if attempt is None:
        return None

    question_points = db.scalar(
        select(func.coalesce(func.sum(MockQuestionAnswer.points_earned), 0)).where(
            MockQuestionAnswer.attempt_id == attempt_id
        )
    )
    writing_points = db.scalar(
        select(
            func.coalesce(
                func.sum(func.coalesce(MockWritingSubmission.teacher_score, MockWritingSubmission.ai_score, 0)),
                0,
            )
        ).where(MockWritingSubmission.attempt_id == attempt_id)
    )
    speaking_points = db.scalar(
        select(
            func.coalesce(
                func.sum(func.coalesce(MockSpeakingSubmission.teacher_score, MockSpeakingSubmission.ai_score, 0)),
                0,
            )
        ).where(MockSpeakingSubmission.attempt_id == attempt_id)
    )

    max_score = db.scalar(
        select(func.coalesce(func.sum(Teil.points), 0))
        .join(Kompetenz, Teil.kompetenz_id == Kompetenz.id)
        .where(Kompetenz.model_test_id == attempt.model_test_id)
    )

    attempt.total_score = int(question_points) + int(writing_points) + int(speaking_points)
    attempt.max_score = int(max_score)
    attempt.status = STATUS_GRADED
    attempt.submitted_at = datetime.now(timezone.utc)
    attempt.time_spent_seconds = time_spent_seconds

    db.commit()
    db.refresh(attempt)
    return attempt


# ============================================================
# Question Answers
# ============================================================


def submit_question_answer(db: Session, data: MockQuestionAnswerCreate) -> MockQuestionAnswer:
    """Auto-grades option-based question types on submission; FILL_BLANK is
    graded by exact (case-insensitive) text match. `answer_data` is a JSON
    string whose shape depends on question_type — see MockQuestion's
    docstring."""
    import json

    question = db.get(MockQuestion, data.question_id)

    is_correct = None
    points_earned = 0

    if question is not None and data.answer_data:
        try:
            parsed = json.loads(data.answer_data)
        except (ValueError, TypeError):
            parsed = None

        if question.question_type == "FILL_BLANK":
            if isinstance(parsed, str) and question.correct_text_answer:
                is_correct = parsed.strip().lower() == question.correct_text_answer.strip().lower()
        elif isinstance(parsed, list):
            correct_ids = {str(o.id) for o in question.options if o.is_correct}
            submitted_ids = {str(v) for v in parsed}
            is_correct = correct_ids == submitted_ids

        if is_correct:
            points_earned = question.points

    answer = MockQuestionAnswer(
        attempt_id=data.attempt_id,
        question_id=data.question_id,
        answer_data=data.answer_data,
        is_correct=is_correct,
        points_earned=points_earned,
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


# ============================================================
# Writing Submissions (+ AI evaluation)
# ============================================================


def get_writing_submissions(db: Session, attempt_id: UUID | None = None):
    query = select(MockWritingSubmission).order_by(MockWritingSubmission.submitted_at.desc())
    if attempt_id:
        query = query.where(MockWritingSubmission.attempt_id == attempt_id)
    return db.scalars(query).all()


def create_writing_submission(db: Session, data: MockWritingSubmissionCreate) -> MockWritingSubmission:
    word_count = len(data.answer_text.split())
    submission = MockWritingSubmission(
        attempt_id=data.attempt_id,
        writing_task_id=data.writing_task_id,
        answer_text=data.answer_text,
        word_count=word_count,
        time_spent_seconds=data.time_spent_seconds,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


async def run_writing_ai_evaluation(db: Session, submission_id: UUID) -> MockWritingSubmission | None:
    submission = db.get(MockWritingSubmission, submission_id)
    if submission is None:
        return None

    task = db.get(WritingTask, submission.writing_task_id)
    if task is None:
        raise AIServiceError("Writing task not found for this submission.")

    result = await evaluate_writing(
        task_text=task.task_text,
        answer_text=submission.answer_text,
        rubric=task.evaluation_rubric,
        max_points=task.max_points,
    )

    submission.ai_grammar_score = result["grammar_score"]
    submission.ai_vocabulary_score = result["vocabulary_score"]
    submission.ai_structure_score = result["structure_score"]
    submission.ai_task_achievement_score = result["task_achievement_score"]
    submission.ai_coherence_score = result["coherence_score"]
    submission.ai_score = result["overall_score"]
    submission.ai_feedback = result["feedback"]
    submission.ai_evaluated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(submission)
    return submission


def update_writing_teacher_review(
    db: Session, submission_id: UUID, data: MockWritingSubmissionTeacherUpdate
) -> MockWritingSubmission | None:
    submission = db.get(MockWritingSubmission, submission_id)
    if submission is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(submission, key, value)
    db.commit()
    db.refresh(submission)
    return submission


# ============================================================
# Speaking Submissions (+ AI evaluation)
# ============================================================


def get_speaking_submissions(db: Session, attempt_id: UUID | None = None):
    query = select(MockSpeakingSubmission).order_by(MockSpeakingSubmission.submitted_at.desc())
    if attempt_id:
        query = query.where(MockSpeakingSubmission.attempt_id == attempt_id)
    return db.scalars(query).all()


def create_speaking_submission(db: Session, data: MockSpeakingSubmissionCreate) -> MockSpeakingSubmission:
    submission = MockSpeakingSubmission(
        attempt_id=data.attempt_id,
        speaking_task_id=data.speaking_task_id,
        audio_url=data.audio_url,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


async def run_speaking_ai_evaluation(db: Session, submission_id: UUID) -> MockSpeakingSubmission | None:
    submission = db.get(MockSpeakingSubmission, submission_id)
    if submission is None:
        return None

    task = db.get(SpeakingTask, submission.speaking_task_id)
    if task is None:
        raise AIServiceError("Speaking task not found for this submission.")

    result = await evaluate_speaking(task_text=task.task_text, audio_url=submission.audio_url)

    submission.transcript = result["transcript"]
    submission.ai_score = result["score"]
    submission.ai_feedback = result["feedback"]
    submission.ai_evaluated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(submission)
    return submission


def update_speaking_teacher_review(
    db: Session, submission_id: UUID, data: MockSpeakingSubmissionTeacherUpdate
) -> MockSpeakingSubmission | None:
    submission = db.get(MockSpeakingSubmission, submission_id)
    if submission is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(submission, key, value)
    db.commit()
    db.refresh(submission)
    return submission
