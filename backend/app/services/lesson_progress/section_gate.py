"""Computes each of a lesson's content sections' real state for a given
student — the single source of truth for completion, applicability, and
(no longer) sequential unlocking. Used by: the student/admin section-gate
API (app/api/lessons/router.py), lesson completion (LessonFlowService /
LessonProgressService, both now delegate to is_lesson_completed here
instead of each re-deriving it), and the server-side submission gates in
app/api/dependencies/section_gate.py + grading_service.py.

Three signals per section:
  - applicable: does this LESSON actually have this kind of content at
    all (a published Video, published Vocabulary, a published Quiz of
    the matching type, an Assessment section with tasks for that
    skill)? A lesson missing a section type never blocks on it and it's
    never counted toward "lesson completed" — this is what makes the
    same code work unmodified across A1-C1: nothing here branches on
    level, it only ever looks at what content actually exists.
  - completed: real evaluated-completion, not "merely opened/submitted"
    — Lesen/Hören require every question in that skill answered;
    Schreiben/Sprechen require the submission to have reached its final
    reviewed status (STATUS_GRADED / STATUS_FINAL), not just SUBMITTED/
    PENDING_REVIEW/REVIEWED; quizzes (Grammatik/Lesson/Wortschatz) are
    graded synchronously on submit, so a StudentQuiz row existing always
    means fully graded.
  - unlocked: ALWAYS True for every section, unconditionally (see
    _compute_unlocked). There is no sequential gate anymore — a section
    being incomplete never blocks any other section, applicable or not.
    This field is kept (rather than removed from the API/frontend
    contract) purely for backward compatibility with every consumer
    already reading it; it simply never evaluates to False.

Lesen/Hören/Schreiben/Sprechen are LEGACY-backed: "applicable" for these
four is real existence of a Reading/Listening/Writing/Speaking row for
this lesson — *any* row, regardless of its own is_published (mirrors
exactly how the Assessment Engine's task-existence check behaved before
this switch: a task's/row's own status never gated the nav tab, only
the actual content-fetch endpoint's published_only filter did). The
Assessment Engine is no longer the student-facing source for these four
skills at all (see frontend/src/constants/lesson-sections.ts and
reading/listening/writing/speaking-section.tsx) — a lesson's real
content now lives in the `readings`/`listenings`/`writings`/`speakings`
tables, the same ones the admin's "(Legacy)" CMS tabs already manage.

completed for lesen/hoeren/schreiben/sprechen still reads the Assessment
Engine's Answer/WritingSubmission/SpeakingSubmission rows below —
deliberately left as-is (harmless, just permanently False going forward
since the student frontend no longer starts Assessment Engine attempts
for these skills) rather than removed, so any real historical completion
data for a lesson that had genuine Assessment Engine content isn't lost
from the API response. This is exactly why all four are also excluded
from GATED_ORDER now: there is no legacy completion signal to replace it
with, and leaving them gated-but-permanently-uncompletable would make
is_lesson_completed() unreachable for every such lesson.

lesson_quiz (Lesson Quiz) is excluded from GATED_ORDER — same treatment
as "grammatik" and homework — because it has been removed from student
navigation entirely (see frontend/src/constants/lesson-sections.ts): a
lesson with a published-but-unreachable Lesson Quiz must never be stuck
"incomplete" forever. Its applicable/completed signals are still computed
(the admin CMS's content-status view and per-student progression list
still read them), only its membership in the gated/required set changed.

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
from app.models.grammar import Grammar
from app.models.listening import Listening
from app.models.quiz import QUIZ_TYPE_GRAMMAR, QUIZ_TYPE_LESSON, QUIZ_TYPE_VOCABULARY, Quiz
from app.models.reading import Reading
from app.models.speaking import Speaking
from app.models.speaking_submission import STATUS_FINAL as SPEAKING_STATUS_FINAL, SpeakingSubmission
from app.models.student_progress import StudentProgress
from app.models.student_quiz import StudentQuiz
from app.models.task_attempt import TaskAttempt
from app.models.task_question import TaskQuestion
from app.models.video import Video
from app.models.vocabulary import Vocabulary
from app.models.writing import Writing
from app.models.writing_submission import STATUS_GRADED as WRITING_STATUS_GRADED, WritingSubmission

SECTION_ORDER = [
    "video",
    "wortschatz",
    "wortschatz_quiz",
    "grammatik",
    "grammatik_quiz",
    "lesen",
    "hoeren",
    "schreiben",
    "sprechen",
    "lesson_quiz",
]

# The "required for lesson completion" set — used only by
# is_lesson_completed now (no sequential gating exists anymore, see
# _compute_unlocked). "grammatik" and "lesson_quiz" excluded (see module
# docstring); "lesen"/"hoeren"/"schreiben"/"sprechen" excluded too, now
# that they're legacy-backed with no completion signal to gate on (see
# module docstring); "homework"/"hausaufgabe" were never section_gate
# keys to begin with, so there's nothing to exclude for them.
_LEGACY_BACKED_SKILLS = ("lesen", "hoeren", "schreiben", "sprechen")
GATED_ORDER = [
    key for key in SECTION_ORDER if key not in ("grammatik", "lesson_quiz", *_LEGACY_BACKED_SKILLS)
]


class SectionGateService:
    def __init__(self, db: Session):
        self.db = db

    # ==========================
    # Completion signals
    # ==========================

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
        # Nothing enforces at most one COURSE assessment per lesson at the
        # DB level (no unique constraint on lesson_id+assessment_type) —
        # the admin builder's own "get-or-create on first task" flow
        # (LesenAssessmentManager.ensureAssessmentAndSection) can end up
        # creating a second one if two skill tabs are used before the
        # first tab's assessment list has loaded (each tab holds its own
        # query, keyed by skill, that doesn't know about the others).
        # Ordering by created_at desc — matching crud_service.
        # list_assessments' own ordering, which is what the admin UI's
        # `assessments?.[0]` already relies on — keeps this in sync with
        # whichever assessment the admin is actually looking at, instead
        # of an arbitrary DB-order pick that could land on an older,
        # incomplete duplicate.
        assessment = (
            self.db.query(Assessment)
            .filter(Assessment.assessment_type == TYPE_COURSE, Assessment.lesson_id == lesson_id)
            .order_by(Assessment.created_at.desc())
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
        submit_answer)."""
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

    def _writing_evaluated(self, assessment: Assessment, attempt: AssessmentAttempt | None) -> bool:
        """Only STATUS_GRADED counts — SUBMITTED/PENDING_REVIEW mean a
        human/AI decision is still pending (see writing_submission.py)."""
        if attempt is None:
            return False
        return (
            self.db.query(WritingSubmission)
            .join(AssessmentSection, WritingSubmission.section_id == AssessmentSection.id)
            .filter(
                WritingSubmission.attempt_id == attempt.id,
                AssessmentSection.skill == SKILL_SCHREIBEN,
                WritingSubmission.status == WRITING_STATUS_GRADED,
            )
            .first()
            is not None
        )

    def _speaking_evaluated(self, assessment: Assessment, attempt: AssessmentAttempt | None) -> bool:
        """Only STATUS_FINAL counts — PENDING_REVIEW/REVIEWED mean the
        teacher hasn't finalized/released the score yet (see
        speaking_submission.py)."""
        if attempt is None:
            return False
        return (
            self.db.query(SpeakingSubmission)
            .join(AssessmentSection, SpeakingSubmission.section_id == AssessmentSection.id)
            .filter(
                SpeakingSubmission.attempt_id == attempt.id,
                AssessmentSection.skill == SKILL_SPRECHEN,
                SpeakingSubmission.status == SPEAKING_STATUS_FINAL,
            )
            .first()
            is not None
        )

    # ==========================
    # Applicability signals
    # ==========================

    def _video_applicable(self, lesson_id: UUID) -> bool:
        return (
            self.db.query(Video).filter(Video.lesson_id == lesson_id, Video.is_published.is_(True)).first()
            is not None
        )

    def _wortschatz_applicable(self, lesson_id: UUID) -> bool:
        return (
            self.db.query(Vocabulary)
            .filter(Vocabulary.lesson_id == str(lesson_id), Vocabulary.is_published.is_(True))
            .first()
            is not None
        )

    def _grammar_applicable(self, lesson_id: UUID) -> bool:
        return (
            self.db.query(Grammar)
            .filter(Grammar.lesson_id == str(lesson_id), Grammar.is_published.is_(True))
            .first()
            is not None
        )

    def _quiz_applicable(self, lesson_id: UUID, quiz_type: str) -> bool:
        return (
            self.db.query(Quiz)
            .filter(Quiz.lesson_id == str(lesson_id), Quiz.quiz_type == quiz_type, Quiz.is_published.is_(True))
            .first()
            is not None
        )

    def _reading_applicable(self, lesson_id: UUID) -> bool:
        # Existence only, no is_published filter — matches how the
        # Assessment Engine's task-existence check behaved before this
        # switch (a row's own status never gated the nav tab; only the
        # student content-fetch endpoint's published_only filter did —
        # see GET /readings/lesson/{id}).
        return self.db.query(Reading).filter(Reading.lesson_id == lesson_id).first() is not None

    def _listening_applicable(self, lesson_id: UUID) -> bool:
        # Same existence-only rule — a Listening row with no real
        # audio_url yet (see seed_lesson_1.py) still makes the tab
        # applicable; the empty/no-audio state is handled inside the
        # section component, not by hiding the tab.
        return (
            self.db.query(Listening).filter(Listening.lesson_id == str(lesson_id)).first() is not None
        )

    def _writing_applicable(self, lesson_id: UUID) -> bool:
        return self.db.query(Writing).filter(Writing.lesson_id == str(lesson_id)).first() is not None

    def _speaking_applicable(self, lesson_id: UUID) -> bool:
        return self.db.query(Speaking).filter(Speaking.lesson_id == str(lesson_id)).first() is not None

    # ==========================
    # Public API
    # ==========================

    def get_state(self, user_id: UUID, lesson_id: UUID) -> dict:
        progress = (
            self.db.query(StudentProgress)
            .filter(StudentProgress.user_id == str(user_id), StudentProgress.lesson_id == str(lesson_id))
            .first()
        )

        assessment, attempt = self._latest_attempt(user_id, lesson_id)

        completed = {
            "video": bool(progress and progress.video_completed),
            "wortschatz": bool(progress and progress.vocabulary_completed),
            # Derived, not a new column: the Wortschatz Quiz is the only
            # writer of vocabulary_score, so a non-null score means the
            # quiz was taken.
            "wortschatz_quiz": bool(progress and progress.vocabulary_score is not None),
            "grammatik": bool(progress and progress.grammar_completed),
            "grammatik_quiz": self._quiz_submitted(user_id, lesson_id, QUIZ_TYPE_GRAMMAR),
            "lesen": bool(assessment) and self._skill_all_answered(assessment, attempt, SKILL_LESEN),
            "hoeren": bool(assessment) and self._skill_all_answered(assessment, attempt, SKILL_HOEREN),
            "schreiben": bool(assessment) and self._writing_evaluated(assessment, attempt),
            "sprechen": bool(assessment) and self._speaking_evaluated(assessment, attempt),
            "lesson_quiz": self._quiz_submitted(user_id, lesson_id, QUIZ_TYPE_LESSON),
        }

        applicable = {
            "video": self._video_applicable(lesson_id),
            "wortschatz": self._wortschatz_applicable(lesson_id),
            "wortschatz_quiz": self._quiz_applicable(lesson_id, QUIZ_TYPE_VOCABULARY),
            # Visible whenever the lesson has published Grammar content —
            # not hardcoded False anymore (see GrammarSection/GET
            # /grammars/lesson/{id}, both of which already existed and
            # expected this). Still excluded from GATED_ORDER below: it
            # has no separate points/required-for-completion role.
            "grammatik": self._grammar_applicable(lesson_id),
            "grammatik_quiz": self._quiz_applicable(lesson_id, QUIZ_TYPE_GRAMMAR),
            # Legacy-backed now — see module docstring. Existence only,
            # any publish status; content is-published gating happens at
            # the GET .../lesson/{id} endpoints instead.
            "lesen": self._reading_applicable(lesson_id),
            "hoeren": self._listening_applicable(lesson_id),
            "schreiben": self._writing_applicable(lesson_id),
            "sprechen": self._speaking_applicable(lesson_id),
            "lesson_quiz": self._quiz_applicable(lesson_id, QUIZ_TYPE_LESSON),
        }

        unlocked = self._compute_unlocked()

        return {
            key: {"unlocked": unlocked[key], "completed": completed[key], "applicable": applicable[key]}
            for key in SECTION_ORDER
        }

    def _compute_unlocked(self) -> dict[str, bool]:
        """No sequential gate: every section is always open, regardless
        of what else has or hasn't been completed. Takes no input on
        purpose — unlocking no longer depends on applicable/completed at
        all, which is itself the proof there's no hidden ordering logic
        left. completed/applicable (progress bars, checkmarks,
        is_lesson_completed) are computed independently in get_state and
        are entirely unaffected by this."""
        return {key: True for key in SECTION_ORDER}

    def is_unlocked(self, user_id: UUID, lesson_id: UUID, section: str) -> bool:
        state = self.get_state(user_id, lesson_id)
        entry = state.get(section)
        return True if entry is None else entry["unlocked"]

    def is_lesson_completed(self, user_id: UUID, lesson_id: UUID) -> bool:
        """LESSON COMPLETED = every applicable, gated section is
        completed. A lesson with zero applicable sections is vacuously
        complete — not expected in practice (every lesson has at least
        a video), but not a special case to guard against either."""
        state = self.get_state(user_id, lesson_id)
        return all(state[key]["completed"] for key in GATED_ORDER if state[key]["applicable"])
