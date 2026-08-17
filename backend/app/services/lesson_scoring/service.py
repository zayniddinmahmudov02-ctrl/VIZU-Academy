"""Computes a student's 100-point score for one lesson, reusing existing
progress/assessment infrastructure end to end — nothing here invents a
new grading algorithm:

  Video        (10 pts) <- StudentProgress.video_completed
  Wortschatz   (10 pts) <- StudentProgress.vocabulary_completed
  Grammatik Quiz(10 pts) <- StudentQuiz.score for the lesson's GRAMMAR-type Quiz
  Lesen        (15 pts) <- Universal Assessment Engine, SectionResult(skill=LESEN)
  Hören        (15 pts) <- Universal Assessment Engine, SectionResult(skill=HOEREN)
  Schreiben    (20 pts) <- Universal Assessment Engine, SectionResult(skill=SCHREIBEN)
  Sprechen     (20 pts) <- Universal Assessment Engine, SectionResult(skill=SPRECHEN)
                -------
                100 pts total (never exceeds this — each component is
                individually clamped to its own max before summing)

The separate "Lesson Quiz" (a lesson's LESSON-type Quiz) is reported
alongside but deliberately excluded from the 100-point total, per spec.
"""

from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.assessment import TYPE_COURSE, Assessment
from app.models.assessment_attempt import STATUS_GRADED, AssessmentAttempt
from app.models.assessment_section import (
    SKILL_HOEREN,
    SKILL_LESEN,
    SKILL_SCHREIBEN,
    SKILL_SPRECHEN,
    AssessmentSection,
)
from app.models.quiz import QUIZ_TYPE_GRAMMAR, QUIZ_TYPE_LESSON, Quiz
from app.models.section_result import SectionResult
from app.models.student_progress import StudentProgress
from app.models.student_quiz import StudentQuiz
from app.repositories.student_progress import StudentProgressRepository

MAX_VIDEO = 10
MAX_WORTSCHATZ = 10
MAX_GRAMMATIK_QUIZ = 10
MAX_LESEN = 15
MAX_HOEREN = 15
MAX_SCHREIBEN = 20
MAX_SPRECHEN = 20
MAX_TOTAL = MAX_VIDEO + MAX_WORTSCHATZ + MAX_GRAMMATIK_QUIZ + MAX_LESEN + MAX_HOEREN + MAX_SCHREIBEN + MAX_SPRECHEN
assert MAX_TOTAL == 100

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

    def compute(self, user_id: UUID, lesson_id: UUID) -> dict:
        progress = (
            self.db.query(StudentProgress)
            .filter(StudentProgress.user_id == str(user_id), StudentProgress.lesson_id == str(lesson_id))
            .first()
        )

        video_points = MAX_VIDEO if (progress and progress.video_completed) else 0
        wortschatz_points = MAX_WORTSCHATZ if (progress and progress.vocabulary_completed) else 0

        grammar_pct, _ = self._quiz_percentage(user_id, lesson_id, QUIZ_TYPE_GRAMMAR)
        lesen_pct, _ = self._skill_percentage(user_id, lesson_id, SKILL_LESEN)
        hoeren_pct, _ = self._skill_percentage(user_id, lesson_id, SKILL_HOEREN)
        schreiben_pct, _ = self._skill_percentage(user_id, lesson_id, SKILL_SCHREIBEN)
        sprechen_pct, _ = self._skill_percentage(user_id, lesson_id, SKILL_SPRECHEN)

        breakdown = {
            "video": {"label": "Video", "points": video_points, "max_points": MAX_VIDEO},
            "wortschatz": {"label": "Wortschatz", "points": wortschatz_points, "max_points": MAX_WORTSCHATZ},
            "grammatik_quiz": {
                "label": "Grammatik Quiz",
                "points": round(grammar_pct * MAX_GRAMMATIK_QUIZ / 100),
                "max_points": MAX_GRAMMATIK_QUIZ,
            },
            "lesen": {"label": "Lesen", "points": round(lesen_pct * MAX_LESEN / 100), "max_points": MAX_LESEN},
            "hoeren": {"label": "Hören", "points": round(hoeren_pct * MAX_HOEREN / 100), "max_points": MAX_HOEREN},
            "schreiben": {
                "label": "Schreiben",
                "points": round(schreiben_pct * MAX_SCHREIBEN / 100),
                "max_points": MAX_SCHREIBEN,
            },
            "sprechen": {
                "label": "Sprechen",
                "points": round(sprechen_pct * MAX_SPRECHEN / 100),
                "max_points": MAX_SPRECHEN,
            },
        }

        # Each component is already individually clamped to its own max
        # above, so this sum can never exceed 100 — the min() is a
        # belt-and-suspenders guarantee, not something expected to bite.
        total = min(sum(item["points"] for item in breakdown.values()), MAX_TOTAL)

        strengths = [
            key for key, item in breakdown.items() if item["points"] / item["max_points"] >= _WEAK_AREA_THRESHOLD
        ]
        weak_areas = [
            key for key, item in breakdown.items() if item["points"] / item["max_points"] < _WEAK_AREA_THRESHOLD
        ]

        lesson_quiz_pct, lesson_quiz_has_result = self._quiz_percentage(user_id, lesson_id, QUIZ_TYPE_LESSON)

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
            "lesson_quiz": {
                "percentage": lesson_quiz_pct,
                "has_result": lesson_quiz_has_result,
            },
        }
