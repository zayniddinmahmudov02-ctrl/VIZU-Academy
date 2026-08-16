"""Computes each of a lesson's 9 content sections' completion state for a
given student — used to render progress/checkmarks (lesson results, admin
per-student view). Sections are no longer sequentially locked (students
may complete them in any order); `unlocked` is kept in the returned shape
only for API/frontend compatibility and is always `True`. The gating
dependencies in app/api/dependencies/section_gate.py consume this too,
so `is_unlocked` always passing means those endpoints no longer enforce
an access order either.

Lesen/Hören are each one half of the same bundled Universal-Assessment-
Engine Assessment (no separate "Lesen Quiz" content exists — see project
memory) so "Lesen done" means every LESEN TaskQuestion has a recorded
Answer, not a separate submission step.

Deliberately does not touch the Assessment Engine's own attempt/scoring
logic (shared with Vorbereitung/MockTest) — this only *reads* Answer/
WritingSubmission/SpeakingSubmission rows that already exist from the
student answering/submitting normally through that engine.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.answer import Answer
from app.models.assessment import TYPE_COURSE, Assessment
from app.models.assessment_attempt import AssessmentAttempt
from app.models.assessment_section import (
    SKILL_HOEREN,
    SKILL_LESEN,
    SKILL_SCHREIBEN,
    SKILL_SPRECHEN,
    AssessmentSection,
)
from app.models.assessment_task import AssessmentTask
from app.models.quiz import QUIZ_TYPE_GRAMMAR, QUIZ_TYPE_LESSON, Quiz
from app.models.speaking_submission import SpeakingSubmission
from app.models.student_progress import StudentProgress
from app.models.student_quiz import StudentQuiz
from app.models.task_attempt import TaskAttempt
from app.models.task_question import TaskQuestion
from app.models.writing_submission import STATUS_DRAFT, WritingSubmission

SECTION_ORDER = [
    "video",
    "wortschatz",
    "grammatik",
    "grammatik_quiz",
    "lesen",
    "hoeren",
    "schreiben",
    "sprechen",
    "lesson_quiz",
]


class SectionGateService:
    def __init__(self, db: Session):
        self.db = db

    def _quiz_submitted(self, user_id: UUID, lesson_id: UUID, quiz_type: str) -> bool:
        quiz = (
            self.db.query(Quiz)
            .filter(Quiz.lesson_id == str(lesson_id), Quiz.quiz_type == quiz_type, Quiz.is_published.is_(True))
            .first()
        )
        if quiz is None:
            return False
        return (
            self.db.query(StudentQuiz)
            .filter(StudentQuiz.user_id == str(user_id), StudentQuiz.quiz_id == str(quiz.id))
            .first()
            is not None
        )

    def _latest_attempt(self, user_id: UUID, lesson_id: UUID) -> tuple[Assessment | None, AssessmentAttempt | None]:
        assessment = (
            self.db.query(Assessment)
            .filter(Assessment.assessment_type == TYPE_COURSE, Assessment.lesson_id == lesson_id)
            .first()
        )
        if assessment is None:
            return None, None
        attempt = (
            self.db.query(AssessmentAttempt)
            .filter(AssessmentAttempt.assessment_id == assessment.id, AssessmentAttempt.user_id == user_id)
            .order_by(AssessmentAttempt.started_at.desc())
            .first()
        )
        return assessment, attempt

    def _skill_all_answered(self, assessment: Assessment, attempt: AssessmentAttempt | None, skill: str) -> bool:
        """LESEN/HOEREN: every TaskQuestion under this skill's section(s)
        has a recorded Answer within the student's latest attempt. Real,
        already-graded-per-question signal (see attempt_service.
        submit_answer) — doesn't require the whole attempt to be
        submitted/graded, only unchanged by this feature either way."""
        question_ids = {
            row[0]
            for row in self.db.query(TaskQuestion.id)
            .join(AssessmentTask, TaskQuestion.task_id == AssessmentTask.id)
            .join(AssessmentSection, AssessmentTask.section_id == AssessmentSection.id)
            .filter(AssessmentSection.assessment_id == assessment.id, AssessmentSection.skill == skill)
            .all()
        }
        if not question_ids:
            return False  # no content published for this skill yet
        if attempt is None:
            return False

        answered_ids = {
            row[0]
            for row in self.db.query(Answer.question_id)
            .join(TaskAttempt, Answer.task_attempt_id == TaskAttempt.id)
            .filter(TaskAttempt.assessment_attempt_id == attempt.id, Answer.question_id.in_(question_ids))
            .all()
        }
        return question_ids.issubset(answered_ids)

    def _writing_submitted(self, assessment: Assessment, attempt: AssessmentAttempt | None) -> bool:
        if attempt is None:
            return False
        return (
            self.db.query(WritingSubmission)
            .join(AssessmentSection, WritingSubmission.section_id == AssessmentSection.id)
            .filter(
                WritingSubmission.attempt_id == attempt.id,
                AssessmentSection.skill == SKILL_SCHREIBEN,
                WritingSubmission.status != STATUS_DRAFT,
            )
            .first()
            is not None
        )

    def _speaking_submitted(self, assessment: Assessment, attempt: AssessmentAttempt | None) -> bool:
        if attempt is None:
            return False
        return (
            self.db.query(SpeakingSubmission)
            .join(AssessmentSection, SpeakingSubmission.section_id == AssessmentSection.id)
            .filter(SpeakingSubmission.attempt_id == attempt.id, AssessmentSection.skill == SKILL_SPRECHEN)
            .first()
            is not None
        )

    def get_state(self, user_id: UUID, lesson_id: UUID) -> dict:
        progress = (
            self.db.query(StudentProgress)
            .filter(StudentProgress.user_id == str(user_id), StudentProgress.lesson_id == str(lesson_id))
            .first()
        )

        video_done = bool(progress and progress.video_completed)
        wortschatz_done = bool(progress and progress.vocabulary_completed)
        grammatik_done = bool(progress and progress.grammar_completed)
        grammatik_quiz_done = self._quiz_submitted(user_id, lesson_id, QUIZ_TYPE_GRAMMAR)

        assessment, attempt = self._latest_attempt(user_id, lesson_id)
        lesen_done = bool(assessment) and self._skill_all_answered(assessment, attempt, SKILL_LESEN)
        hoeren_done = bool(assessment) and self._skill_all_answered(assessment, attempt, SKILL_HOEREN)
        schreiben_done = bool(assessment) and self._writing_submitted(assessment, attempt)
        sprechen_done = bool(assessment) and self._speaking_submitted(assessment, attempt)

        lesson_quiz_done = self._quiz_submitted(user_id, lesson_id, QUIZ_TYPE_LESSON)

        completed = {
            "video": video_done,
            "wortschatz": wortschatz_done,
            "grammatik": grammatik_done,
            "grammatik_quiz": grammatik_quiz_done,
            "lesen": lesen_done,
            "hoeren": hoeren_done,
            "schreiben": schreiben_done,
            "sprechen": sprechen_done,
            "lesson_quiz": lesson_quiz_done,
        }

        # Sections are independently accessible — no sequential lock.
        # `unlocked` is always True; kept in the shape for API/frontend
        # compatibility (see module docstring).
        return {
            key: {"unlocked": True, "completed": completed[key]}
            for key in SECTION_ORDER
        }

    def is_unlocked(self, user_id: UUID, lesson_id: UUID, section: str) -> bool:
        return True
