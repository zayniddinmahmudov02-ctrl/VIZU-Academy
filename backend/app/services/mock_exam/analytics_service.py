from uuid import UUID

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.orm import Session, aliased

from app.models.certification_provider import CertificationProvider
from app.models.kompetenz import Kompetenz
from app.models.listening_content import ListeningContent
from app.models.media_asset import MediaAsset
from app.models.mock_exam_level import MockExamLevel
from app.models.mock_question import MockQuestion
from app.models.mock_question_answer import MockQuestionAnswer
from app.models.mock_test_attempt import MockTestAttempt
from app.models.model_test import ModelTest
from app.models.reading_content import ReadingContent
from app.models.teil import Teil

PASS_THRESHOLD = 0.6


def get_dashboard_summary(db: Session) -> dict:
    return {
        "certificates": db.scalar(select(func.count()).select_from(CertificationProvider)) or 0,
        "levels": db.scalar(select(func.count()).select_from(MockExamLevel)) or 0,
        "model_tests": db.scalar(select(func.count()).select_from(ModelTest)) or 0,
        "questions": db.scalar(select(func.count()).select_from(MockQuestion)) or 0,
        "media_assets": db.scalar(select(func.count()).select_from(MediaAsset)) or 0,
        "students_attempted": db.scalar(
            select(func.count(func.distinct(MockTestAttempt.user_id)))
        )
        or 0,
        "total_attempts": db.scalar(select(func.count()).select_from(MockTestAttempt)) or 0,
        "ai_evaluations_used": 0,
    }


def _pct(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def _kompetenz_id_for_question_query():
    """A question's Kompetenz can only be reached via one of two paths
    (reading_content -> teil -> kompetenz, or listening_content -> teil ->
    kompetenz) since a question belongs to exactly one content type.
    COALESCE the two possible paths into a single kompetenz_id per row."""
    reading_teil = aliased(Teil)
    listening_teil = aliased(Teil)

    return (
        select(
            MockQuestionAnswer.attempt_id,
            MockQuestionAnswer.is_correct,
            MockQuestionAnswer.points_earned,
            MockQuestion.points,
            func.coalesce(reading_teil.kompetenz_id, listening_teil.kompetenz_id).label(
                "kompetenz_id"
            ),
        )
        .select_from(MockQuestionAnswer)
        .join(MockQuestion, MockQuestionAnswer.question_id == MockQuestion.id)
        .outerjoin(ReadingContent, MockQuestion.reading_content_id == ReadingContent.id)
        .outerjoin(reading_teil, ReadingContent.teil_id == reading_teil.id)
        .outerjoin(ListeningContent, MockQuestion.listening_content_id == ListeningContent.id)
        .outerjoin(listening_teil, ListeningContent.teil_id == listening_teil.id)
    )


def get_model_test_analytics(db: Session, model_test_id: UUID) -> dict | None:
    model_test = db.get(ModelTest, model_test_id)
    if model_test is None:
        return None

    attempts = db.scalars(
        select(MockTestAttempt).where(
            MockTestAttempt.model_test_id == model_test_id,
            MockTestAttempt.status == "GRADED",
        )
    ).all()

    graded = [a for a in attempts if a.total_score is not None and a.max_score]
    avg = _pct(sum(a.total_score for a in graded), sum(a.max_score for a in graded))
    passed = sum(1 for a in graded if a.total_score / a.max_score >= PASS_THRESHOLD)

    kompetenzen = db.scalars(
        select(Kompetenz).where(Kompetenz.model_test_id == model_test_id)
    ).all()

    answer_subquery = _kompetenz_id_for_question_query().subquery()

    kompetenz_analytics = []
    for k in kompetenzen:
        rows = db.execute(
            select(answer_subquery.c.points_earned, answer_subquery.c.points).where(
                answer_subquery.c.kompetenz_id == k.id
            )
        ).all()
        earned = sum(r[0] for r in rows)
        possible = sum(r[1] for r in rows)
        kompetenz_analytics.append(
            {
                "kompetenz_id": k.id,
                "type": k.type,
                "title": k.title,
                "average_score_percent": _pct(earned, possible),
                "attempts": len(attempts),
            }
        )

    return {
        "model_test_id": model_test.id,
        "title": model_test.title,
        "average_score_percent": avg,
        "pass_rate_percent": _pct(passed, len(graded)),
        "attempts": len(attempts),
        "kompetenzen": kompetenz_analytics,
    }


def get_most_failed_questions(db: Session, model_test_ids: list[UUID], limit: int = 10) -> list[dict]:
    if not model_test_ids:
        return []

    answer_subquery = _kompetenz_id_for_question_query().subquery()

    rows = db.execute(
        select(
            MockQuestion.id,
            MockQuestion.question_text,
            func.count(MockQuestionAnswer.id),
            func.coalesce(func.sum(cast(MockQuestionAnswer.is_correct, Integer)), 0),
        )
        .join(MockQuestionAnswer, MockQuestionAnswer.question_id == MockQuestion.id)
        .group_by(MockQuestion.id, MockQuestion.question_text)
        .having(func.count(MockQuestionAnswer.id) > 0)
    ).all()

    items = []
    for question_id, question_text, total, correct in rows:
        failure_rate = _pct(total - correct, total)
        items.append(
            {
                "question_id": question_id,
                "question_text": question_text,
                "times_answered": total,
                "times_correct": correct,
                "failure_rate_percent": failure_rate,
            }
        )

    items.sort(key=lambda x: x["failure_rate_percent"], reverse=True)
    return items[:limit]


def get_provider_analytics(db: Session, provider_id: UUID) -> dict | None:
    provider = db.get(CertificationProvider, provider_id)
    if provider is None:
        return None

    model_test_ids = list(
        db.scalars(
            select(ModelTest.id)
            .join(MockExamLevel, ModelTest.level_id == MockExamLevel.id)
            .where(MockExamLevel.provider_id == provider_id)
        ).all()
    )

    attempts = (
        db.scalars(
            select(MockTestAttempt).where(
                MockTestAttempt.model_test_id.in_(model_test_ids),
                MockTestAttempt.status == "GRADED",
            )
        ).all()
        if model_test_ids
        else []
    )

    graded = [a for a in attempts if a.total_score is not None and a.max_score]
    avg = _pct(sum(a.total_score for a in graded), sum(a.max_score for a in graded))
    passed = sum(1 for a in graded if a.total_score / a.max_score >= PASS_THRESHOLD)

    model_tests = [get_model_test_analytics(db, mt_id) for mt_id in model_test_ids]

    return {
        "provider_id": provider.id,
        "name": provider.name,
        "average_score_percent": avg,
        "pass_rate_percent": _pct(passed, len(graded)),
        "total_attempts": len(attempts),
        "model_tests": [mt for mt in model_tests if mt is not None],
        "most_failed_questions": get_most_failed_questions(db, model_test_ids),
    }
