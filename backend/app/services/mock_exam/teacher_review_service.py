from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.certification_provider import CertificationProvider
from app.models.kompetenz import Kompetenz
from app.models.mock_exam_level import MockExamLevel
from app.models.mock_speaking_submission import MockSpeakingSubmission
from app.models.mock_test_attempt import MockTestAttempt
from app.models.mock_writing_submission import MockWritingSubmission
from app.models.model_test import ModelTest
from app.models.speaking_task import SpeakingTask
from app.models.teil import Teil
from app.models.user import User
from app.models.writing_task import WritingTask

# Every Modelltest Schreiben/Sprechen submission joined back to its full
# Zertifikat breadcrumb (Provider -> Level -> Modelltest -> Teil) and its
# author, so the Teacher Panel can group "Vorbereitung" submissions the
# same way it groups "Lektionen" ones by course/level — never a flat,
# unlabeled list (see frontend/src/app/teacher/schreiben(|sprechen)/page.tsx).


def list_writing_for_teacher(db: Session) -> list[dict]:
    rows = db.execute(
        select(
            MockWritingSubmission,
            User.username,
            User.email,
            CertificationProvider.name,
            MockExamLevel.level,
            ModelTest.title,
            Teil.title,
            WritingTask.task_text,
            WritingTask.word_limit,
        )
        .join(MockTestAttempt, MockWritingSubmission.attempt_id == MockTestAttempt.id)
        .join(User, MockTestAttempt.user_id == User.id)
        .join(WritingTask, MockWritingSubmission.writing_task_id == WritingTask.id)
        .join(Teil, WritingTask.teil_id == Teil.id)
        .join(Kompetenz, Teil.kompetenz_id == Kompetenz.id)
        .join(ModelTest, Kompetenz.model_test_id == ModelTest.id)
        .join(MockExamLevel, ModelTest.level_id == MockExamLevel.id)
        .join(CertificationProvider, MockExamLevel.provider_id == CertificationProvider.id)
        .order_by(MockWritingSubmission.submitted_at.desc())
    ).all()

    return [
        {
            "submission": submission,
            "student_username": username,
            "student_email": email,
            "provider_name": provider_name,
            "level_code": level_code,
            "model_test_title": model_test_title,
            "teil_title": teil_title,
            "task_text": task_text,
            "word_limit": word_limit,
        }
        for (
            submission,
            username,
            email,
            provider_name,
            level_code,
            model_test_title,
            teil_title,
            task_text,
            word_limit,
        ) in rows
    ]


def list_speaking_for_teacher(db: Session) -> list[dict]:
    rows = db.execute(
        select(
            MockSpeakingSubmission,
            User.username,
            User.email,
            CertificationProvider.name,
            MockExamLevel.level,
            ModelTest.title,
            Teil.title,
            SpeakingTask.task_text,
        )
        .join(MockTestAttempt, MockSpeakingSubmission.attempt_id == MockTestAttempt.id)
        .join(User, MockTestAttempt.user_id == User.id)
        .join(SpeakingTask, MockSpeakingSubmission.speaking_task_id == SpeakingTask.id)
        .join(Teil, SpeakingTask.teil_id == Teil.id)
        .join(Kompetenz, Teil.kompetenz_id == Kompetenz.id)
        .join(ModelTest, Kompetenz.model_test_id == ModelTest.id)
        .join(MockExamLevel, ModelTest.level_id == MockExamLevel.id)
        .join(CertificationProvider, MockExamLevel.provider_id == CertificationProvider.id)
        .order_by(MockSpeakingSubmission.submitted_at.desc())
    ).all()

    return [
        {
            "submission": submission,
            "student_username": username,
            "student_email": email,
            "provider_name": provider_name,
            "level_code": level_code,
            "model_test_title": model_test_title,
            "teil_title": teil_title,
            "task_text": task_text,
        }
        for (
            submission,
            username,
            email,
            provider_name,
            level_code,
            model_test_title,
            teil_title,
            task_text,
        ) in rows
    ]
