"""Computes a student's 100-point score for one lesson, reusing existing
progress/quiz infrastructure end to end — nothing here invents a new
grading algorithm:

  Video        (10 pts) <- StudentProgress.video_completed
  Lesen        (15 pts) <- Universal Assessment Engine, SectionResult(skill=LESEN)
  Hören        (15 pts) <- Universal Assessment Engine, SectionResult(skill=HOEREN)
  Schreiben    (20 pts) <- StudentWriting.score, ONLY once a teacher GRADED it
  Sprechen     (20 pts) <- StudentSpeaking.score, ONLY once a teacher GRADED it
  Wortschatz   (10 pts) <- StudentProgress.vocabulary_score (the Wortschatz
                           Test's server-graded result)
  Yakuniy Test (10 pts) <- StudentQuiz.score of the lesson's LESSON-type Quiz
                -------
                100 pts total (never exceeds this — each component is
                individually clamped to its own max before summing)

Grammatik is no longer part of the lesson and contributes nothing.

Schreiben/Sprechen: a merely SUBMITTED answer earns no points and is
reported with status "pending" (shown to the student as not yet graded),
never as a silent 0.
"""

from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.assessment import TYPE_COURSE, Assessment
from app.models.assessment_attempt import STATUS_GRADED, AssessmentAttempt
from app.models.assessment_section import (
    SKILL_HOEREN,
    SKILL_LESEN,
    AssessmentSection,
)
from app.models.quiz import QUIZ_TYPE_LESSON, QUIZ_TYPE_VOCABULARY, Quiz
from app.models.section_result import SectionResult
from app.models.speaking import Speaking
from app.models.student_progress import StudentProgress
from app.models.student_quiz import StudentQuiz
from app.models.student_speaking import (
    STATUS_GRADED as SPEAKING_STATUS_GRADED,
    STATUS_SUBMITTED as SPEAKING_STATUS_SUBMITTED,
    StudentSpeaking,
)
from app.models.student_writing import (
    STATUS_GRADED as WRITING_STATUS_GRADED,
    STATUS_SUBMITTED as WRITING_STATUS_SUBMITTED,
    StudentWriting,
)
from app.models.writing import Writing
from app.repositories.student_progress import StudentProgressRepository

MAX_VIDEO = 10
MAX_LESEN = 15
MAX_HOEREN = 15
MAX_SCHREIBEN = 20
MAX_SPRECHEN = 20
MAX_WORTSCHATZ = 10
MAX_YAKUNIY_TEST = 10
MAX_TOTAL = MAX_VIDEO + MAX_LESEN + MAX_HOEREN + MAX_SCHREIBEN + MAX_SPRECHEN + MAX_WORTSCHATZ + MAX_YAKUNIY_TEST
assert MAX_TOTAL == 100

# "final": the points shown are what the student has earned so far.
# "pending": a submission exists that a teacher hasn't graded yet.
STATUS_FINAL = "final"
STATUS_PENDING = "pending"

# Ordered so a 100 checks the first (highest) range it satisfies.
_FEEDBACK_RANGES: list[tuple[int, int, str]] = [
    (90, 100, "Sehr gut! Du beherrschst diese Lektion sehr sicher."),
    (80, 89, "Sehr gut! Einige Bereiche können noch verbessert werden."),
    (70, 79, "Gut gemacht! Wiederhole die schwächeren Bereiche."),
    (60, 69, "Du hast die Grundlagen verstanden. Weitere Übung wird empfohlen."),
    (40, 59, "Wiederhole die Lektion und übe die schwächeren Bereiche erneut."),
    (0, 39, "Die Lektion sollte noch einmal gründlich bearbeitet werden."),
]

# A component counts as a "strength" at 70%+ of its own max, "weak"
# below that — matches the feedback tier boundary at 70 for consistency.
_WEAK_AREA_THRESHOLD = 0.7


def _feedback_for(total: int) -> str:
    for lo, hi, message in _FEEDBACK_RANGES:
        if lo <= total <= hi:
            return message
    return _FEEDBACK_RANGES[-1][2]


class LessonScoringService:
    def __init__(self, db: Session):
        self.db = db
        self.progress_repo = StudentProgressRepository(db)

    def _quiz_percentage(self, user_id: UUID, lesson_id: UUID, quiz_type: str) -> tuple[int, bool]:
        """Returns (percentage 0-100, has_a_result). Uses this student's
        most recent submission for the lesson's quiz of this type —
        StudentQuiz.score is already 0-100 (same scale as Quiz.passing_score)."""
        quiz = (
            self.db.query(Quiz)
            .filter(
                Quiz.lesson_id == str(lesson_id),
                Quiz.quiz_type == quiz_type,
                Quiz.is_published.is_(True),
            )
            .order_by(Quiz.order_index)
            .first()
        )
        if quiz is None:
            return 0, False

        attempt = (
            self.db.query(StudentQuiz)
            .filter(StudentQuiz.user_id == str(user_id), StudentQuiz.quiz_id == str(quiz.id))
            .order_by(desc(StudentQuiz.created_at))
            .first()
        )
        if attempt is None:
            return 0, False

        return max(0, min(100, attempt.score)), True

    def _skill_percentage(self, user_id: UUID, lesson_id: UUID, skill: str) -> tuple[int, bool]:
        """Returns (percentage 0-100, has_a_result) for one skill section
        of this lesson's Universal Assessment Engine assessment, from this
        student's most recently graded attempt."""
        assessment = (
            self.db.query(Assessment)
            .filter(Assessment.assessment_type == TYPE_COURSE, Assessment.lesson_id == lesson_id)
            .first()
        )
        if assessment is None:
            return 0, False

        section = (
            self.db.query(AssessmentSection)
            .filter(AssessmentSection.assessment_id == assessment.id, AssessmentSection.skill == skill)
            .first()
        )
        if section is None:
            return 0, False

        attempt = (
            self.db.query(AssessmentAttempt)
            .filter(
                AssessmentAttempt.assessment_id == assessment.id,
                AssessmentAttempt.user_id == user_id,
                AssessmentAttempt.status == STATUS_GRADED,
            )
            .order_by(desc(AssessmentAttempt.submitted_at))
            .first()
        )
        if attempt is None:
            return 0, False

        result = (
            self.db.query(SectionResult)
            .filter(SectionResult.assessment_attempt_id == attempt.id, SectionResult.section_id == section.id)
            .first()
        )
        if result is None:
            return 0, False

        return max(0, min(100, round(result.percentage))), True

    def _graded_task_percentage(
        self, task_scores: dict[str, tuple[str | None, int | None]], task_ids: list[str]
    ) -> tuple[int, str]:
        """Shared Schreiben/Sprechen rule. `task_scores` maps task id ->
        (submission status, score); a task counts only when GRADED, the
        percentage is the mean over the lesson's published tasks, and the
        status is "pending" while any submission still awaits grading."""
        if not task_ids:
            return 0, STATUS_FINAL
        total = 0
        pending = False
        for task_id in task_ids:
            status, score = task_scores.get(task_id, (None, None))
            if status in (WRITING_STATUS_GRADED, SPEAKING_STATUS_GRADED) and score is not None:
                total += max(0, min(100, score))
            elif status in (WRITING_STATUS_SUBMITTED, SPEAKING_STATUS_SUBMITTED):
                pending = True
        return round(total / len(task_ids)), (STATUS_PENDING if pending else STATUS_FINAL)

    def _writing_percentage(self, user_id: UUID, lesson_id: UUID) -> tuple[int, str]:
        task_ids = [
            str(row[0])
            for row in self.db.query(Writing.id)
            .filter(Writing.lesson_id == str(lesson_id), Writing.is_published.is_(True))
            .all()
        ]
        if not task_ids:
            return 0, STATUS_FINAL
        rows = (
            self.db.query(StudentWriting.writing_id, StudentWriting.status, StudentWriting.score)
            .filter(StudentWriting.user_id == str(user_id), StudentWriting.writing_id.in_(task_ids))
            .all()
        )
        return self._graded_task_percentage({str(r[0]): (r[1], r[2]) for r in rows}, task_ids)

    def _speaking_percentage(self, user_id: UUID, lesson_id: UUID) -> tuple[int, str]:
        task_ids = [
            str(row[0])
            for row in self.db.query(Speaking.id)
            .filter(Speaking.lesson_id == str(lesson_id), Speaking.is_published.is_(True))
            .all()
        ]
        if not task_ids:
            return 0, STATUS_FINAL
        rows = (
            self.db.query(StudentSpeaking.speaking_id, StudentSpeaking.status, StudentSpeaking.score)
            .filter(StudentSpeaking.user_id == user_id, StudentSpeaking.speaking_id.in_(task_ids))
            .all()
        )
        return self._graded_task_percentage({str(r[0]): (r[1], r[2]) for r in rows}, task_ids)

    def compute(self, user_id: UUID, lesson_id: UUID) -> dict:
        progress = (
            self.db.query(StudentProgress)
            .filter(StudentProgress.user_id == str(user_id), StudentProgress.lesson_id == str(lesson_id))
            .first()
        )

        video_points = MAX_VIDEO if (progress and progress.video_completed) else 0

        has_vocab_quiz = (
            self.db.query(Quiz)
            .filter(Quiz.lesson_id == str(lesson_id), Quiz.quiz_type == QUIZ_TYPE_VOCABULARY)
            .first()
            is not None
        )

        if progress and progress.vocabulary_score is not None:
            wortschatz_points = round(max(0, min(100, progress.vocabulary_score)) * MAX_WORTSCHATZ / 100)
        elif progress and progress.vocabulary_completed and not has_vocab_quiz:
            # Only lessons with no separate Wortschatz Quiz (B1-C1, where
            # completing the exercises IS the whole Wortschatz component)
            # get full credit from vocabulary_completed alone. For A1
            # lessons with a Quiz, vocabulary_completed only means the
            # learning step is done — no credit until vocabulary_score
            # exists (see vocabulary-learn-section.tsx / test-section.tsx).
            wortschatz_points = MAX_WORTSCHATZ
        else:
            wortschatz_points = 0

        lesen_pct, _ = self._skill_percentage(user_id, lesson_id, SKILL_LESEN)
        hoeren_pct, _ = self._skill_percentage(user_id, lesson_id, SKILL_HOEREN)
        schreiben_pct, schreiben_status = self._writing_percentage(user_id, lesson_id)
        sprechen_pct, sprechen_status = self._speaking_percentage(user_id, lesson_id)
        yakuniy_pct, _ = self._quiz_percentage(user_id, lesson_id, QUIZ_TYPE_LESSON)

        def component(label: str, points: int, max_points: int, status: str = STATUS_FINAL) -> dict:
            return {"label": label, "points": points, "max_points": max_points, "status": status}

        breakdown = {
            "video": component("Video", video_points, MAX_VIDEO),
            "lesen": component("Lesen", round(lesen_pct * MAX_LESEN / 100), MAX_LESEN),
            "hoeren": component("Hören", round(hoeren_pct * MAX_HOEREN / 100), MAX_HOEREN),
            "schreiben": component(
                "Schreiben", round(schreiben_pct * MAX_SCHREIBEN / 100), MAX_SCHREIBEN, schreiben_status
            ),
            "sprechen": component(
                "Sprechen", round(sprechen_pct * MAX_SPRECHEN / 100), MAX_SPRECHEN, sprechen_status
            ),
            "wortschatz": component("Wortschatz", wortschatz_points, MAX_WORTSCHATZ),
            "yakuniy_test": component(
                "Yakuniy Test", round(yakuniy_pct * MAX_YAKUNIY_TEST / 100), MAX_YAKUNIY_TEST
            ),
        }

        # Each component is already individually clamped to its own max
        # above, so this sum can never exceed 100 — the min() is a
        # belt-and-suspenders guarantee, not something expected to bite.
        total = min(sum(item["points"] for item in breakdown.values()), MAX_TOTAL)

        # A component still awaiting a teacher's grade is neither a
        # strength nor a weak area — it simply isn't decided yet.
        decided = {key: item for key, item in breakdown.items() if item["status"] != STATUS_PENDING}
        strengths = [
            key for key, item in decided.items() if item["points"] / item["max_points"] >= _WEAK_AREA_THRESHOLD
        ]
        weak_areas = [
            key for key, item in decided.items() if item["points"] / item["max_points"] < _WEAK_AREA_THRESHOLD
        ]

        # Cache the total on StudentProgress (an existing, previously-
        # unpopulated field) so the dashboard/overview can read it
        # cheaply without recomputing across every lesson.
        if progress is None:
            progress = self.progress_repo.get_or_create(str(user_id), str(lesson_id))
        progress.total_score = total
        self.db.commit()

        return {
            "lesson_id": lesson_id,
            "total_score": total,
            "max_score": MAX_TOTAL,
            "percentage": total,  # max is always 100, so these coincide
            "breakdown": breakdown,
            "feedback": _feedback_for(total),
            "strengths": strengths,
            "weak_areas": weak_areas,
        }
