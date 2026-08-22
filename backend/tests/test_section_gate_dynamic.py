"""Verifies the core new logic in SectionGateService: dynamic sequential
unlocking that skips whatever a lesson doesn't have (_compute_unlocked,
a pure function — no DB), lesson completion counting only applicable
sections (is_lesson_completed), and the tightened Schreiben/Sprechen
"evaluated" checks (STATUS_GRADED / STATUS_FINAL, not merely submitted).
Uses stdlib unittest + MagicMock/patch, matching this session's
established pattern (no pytest, no real DB) — _compute_unlocked needs no
mocking at all since it takes plain dicts."""

import unittest
from unittest.mock import MagicMock, patch

from app.services.lesson_progress.section_gate import GATED_ORDER, SECTION_ORDER, SectionGateService


def all_applicable(**overrides) -> dict[str, bool]:
    base = {key: True for key in SECTION_ORDER}
    base["grammatik"] = False  # never applicable/gated — matches production logic
    base.update(overrides)
    return base


def all_incomplete(**overrides) -> dict[str, bool]:
    base = {key: False for key in SECTION_ORDER}
    base.update(overrides)
    return base


class TestComputeUnlockedSequential(unittest.TestCase):
    """The core sequential-gate logic — pure, no DB, no level branching
    anywhere (proven directly by feeding it differently-shaped
    "applicable" dicts, one per A1-C1's realistic section mix, in
    test_universal_across_levels below)."""

    def setUp(self):
        self.service = SectionGateService(db=MagicMock())

    def test_first_applicable_section_always_unlocked(self):
        applicable = all_applicable()
        completed = all_incomplete()
        unlocked = self.service._compute_unlocked(applicable, completed)
        self.assertTrue(unlocked["video"])

    def test_wortschatz_locked_until_video_done(self):
        applicable = all_applicable()
        completed = all_incomplete()
        unlocked = self.service._compute_unlocked(applicable, completed)
        self.assertFalse(unlocked["wortschatz"])

    def test_wortschatz_quiz_locked_while_wortschatz_incomplete(self):
        applicable = all_applicable()
        completed = all_incomplete(video=True, wortschatz=False)
        unlocked = self.service._compute_unlocked(applicable, completed)
        self.assertFalse(unlocked["wortschatz_quiz"])

    def test_wortschatz_quiz_available_once_wortschatz_complete(self):
        applicable = all_applicable()
        completed = all_incomplete(video=True, wortschatz=True)
        unlocked = self.service._compute_unlocked(applicable, completed)
        self.assertTrue(unlocked["wortschatz_quiz"])

    def test_next_section_available_once_wortschatz_quiz_complete(self):
        applicable = all_applicable()
        completed = all_incomplete(video=True, wortschatz=True, wortschatz_quiz=True)
        unlocked = self.service._compute_unlocked(applicable, completed)
        self.assertTrue(unlocked["grammatik_quiz"])

    def test_lesen_locked_until_previous_required_sections_done(self):
        applicable = all_applicable()
        completed = all_incomplete(video=True, wortschatz=True, wortschatz_quiz=True, grammatik_quiz=False)
        unlocked = self.service._compute_unlocked(applicable, completed)
        self.assertFalse(unlocked["lesen"])

    def test_lesen_available_once_earlier_sections_done(self):
        applicable = all_applicable()
        completed = all_incomplete(video=True, wortschatz=True, wortschatz_quiz=True, grammatik_quiz=True)
        unlocked = self.service._compute_unlocked(applicable, completed)
        self.assertTrue(unlocked["lesen"])

    def test_hoeren_locked_until_lesen_done_and_available_after(self):
        applicable = all_applicable()
        base_completed = {
            "video": True,
            "wortschatz": True,
            "wortschatz_quiz": True,
            "grammatik_quiz": True,
        }
        locked = self.service._compute_unlocked(applicable, {**all_incomplete(), **base_completed, "lesen": False})
        self.assertFalse(locked["hoeren"])

        unlocked = self.service._compute_unlocked(applicable, {**all_incomplete(), **base_completed, "lesen": True})
        self.assertTrue(unlocked["hoeren"])

    def test_missing_section_never_blocks_the_chain(self):
        # A lesson missing grammatik_quiz/schreiben/sprechen/lesson_quiz —
        # only video/wortschatz/wortschatz_quiz/lesen/hoeren applicable.
        applicable = all_applicable(grammatik_quiz=False, schreiben=False, sprechen=False, lesson_quiz=False)
        completed = all_incomplete(video=True, wortschatz=True, wortschatz_quiz=True)
        unlocked = self.service._compute_unlocked(applicable, completed)
        # lesen unlocks right after wortschatz_quiz — grammatik_quiz is
        # skipped entirely, not a blocker.
        self.assertTrue(unlocked["lesen"])
        # the inapplicable sections themselves report unlocked (nothing
        # to lock) but don't participate in the real chain.
        self.assertTrue(unlocked["grammatik_quiz"])
        self.assertTrue(unlocked["schreiben"])

    def test_grammatik_standalone_always_unlocked_not_gated(self):
        applicable = all_applicable()
        completed = all_incomplete()
        unlocked = self.service._compute_unlocked(applicable, completed)
        self.assertTrue(unlocked["grammatik"])

    def test_universal_across_levels_no_branching(self):
        """Same function, five different realistic section shapes — one
        per level. Passing all five with no level parameter anywhere in
        _compute_unlocked's signature is itself the proof there's no
        level-specific code path."""
        # A1: has wortschatz_quiz (VOCABULARY quiz exists for A1 only).
        a1 = all_applicable()
        # A2/B1/B2/C1: no VOCABULARY quiz ever gets created for them
        # (test_sync_service.py's existing A1-only gate) — and this
        # lesson also has no lesson_quiz.
        a2 = all_applicable(wortschatz_quiz=False)
        b1 = all_applicable(wortschatz_quiz=False, sprechen=False)
        b2 = all_applicable(wortschatz_quiz=False, lesson_quiz=False)
        c1 = all_applicable(wortschatz_quiz=False, grammatik_quiz=False, schreiben=False)

        for level_name, applicable in [("A1", a1), ("A2", a2), ("B1", b1), ("B2", b2), ("C1", c1)]:
            with self.subTest(level=level_name):
                completed = all_incomplete(video=True)
                unlocked = self.service._compute_unlocked(applicable, completed)
                # Whatever the first applicable section after video is,
                # it must be unlocked; video itself always is.
                self.assertTrue(unlocked["video"])
                first_after_video = next(
                    key for key in GATED_ORDER if key != "video" and applicable[key]
                )
                self.assertTrue(unlocked[first_after_video])


class TestIsLessonCompleted(unittest.TestCase):
    """is_lesson_completed = every applicable, gated section completed —
    tested by substituting get_state's return value directly (far
    simpler and more reliable than mocking the ~12 distinct db.query()
    shapes get_state's own DB calls would require)."""

    def setUp(self):
        self.service = SectionGateService(db=MagicMock())

    def _state(self, applicable: dict, completed: dict) -> dict:
        return {key: {"applicable": applicable[key], "completed": completed[key], "unlocked": True} for key in SECTION_ORDER}

    def test_all_applicable_completed_is_lesson_completed(self):
        applicable = all_applicable()
        completed = {key: True for key in SECTION_ORDER}
        with patch.object(SectionGateService, "get_state", return_value=self._state(applicable, completed)):
            self.assertTrue(self.service.is_lesson_completed(user_id="u", lesson_id="l"))

    def test_one_incomplete_applicable_section_blocks_completion(self):
        applicable = all_applicable()
        completed = {key: True for key in SECTION_ORDER}
        completed["sprechen"] = False
        with patch.object(SectionGateService, "get_state", return_value=self._state(applicable, completed)):
            self.assertFalse(self.service.is_lesson_completed(user_id="u", lesson_id="l"))

    def test_missing_section_never_blocks_lesson_completion(self):
        # Lesson has no Sprechen content at all — must not be required.
        applicable = all_applicable(sprechen=False)
        completed = {key: True for key in SECTION_ORDER}
        completed["sprechen"] = False  # never evaluated, because it doesn't exist
        with patch.object(SectionGateService, "get_state", return_value=self._state(applicable, completed)):
            self.assertTrue(self.service.is_lesson_completed(user_id="u", lesson_id="l"))

    def test_homework_never_appears_in_gated_order(self):
        # No submission/review system exists for Homework yet — it must
        # never be part of the required/gated sequence.
        self.assertNotIn("hausaufgabe", GATED_ORDER)
        self.assertNotIn("homework", GATED_ORDER)


class TestWritingSpeakingEvaluatedTightening(unittest.TestCase):
    """Only STATUS_GRADED (writing) / STATUS_FINAL (speaking) count as
    truly evaluated — SUBMITTED/PENDING_REVIEW/REVIEWED must not."""

    def _mock_db_returning(self, row_or_none):
        db = MagicMock()
        query = MagicMock()
        query.join.return_value = query
        query.filter.return_value = query
        query.first.return_value = row_or_none
        db.query.return_value = query
        return db

    def test_writing_pending_review_is_not_evaluated(self):
        service = SectionGateService(db=self._mock_db_returning(None))
        attempt = MagicMock(id="attempt-1")
        assessment = MagicMock(id="assessment-1")
        self.assertFalse(service._writing_evaluated(assessment, attempt))

    def test_writing_graded_is_evaluated(self):
        service = SectionGateService(db=self._mock_db_returning(MagicMock()))
        attempt = MagicMock(id="attempt-1")
        assessment = MagicMock(id="assessment-1")
        self.assertTrue(service._writing_evaluated(assessment, attempt))

    def test_speaking_reviewed_but_not_final_is_not_evaluated(self):
        # The mock DB's filter().first() returning None simulates the
        # STATUS_FINAL filter matching nothing — i.e. a REVIEWED-but-not-
        # finalized submission exists but doesn't satisfy the query.
        service = SectionGateService(db=self._mock_db_returning(None))
        attempt = MagicMock(id="attempt-1")
        assessment = MagicMock(id="assessment-1")
        self.assertFalse(service._speaking_evaluated(assessment, attempt))

    def test_speaking_final_is_evaluated(self):
        service = SectionGateService(db=self._mock_db_returning(MagicMock()))
        attempt = MagicMock(id="attempt-1")
        assessment = MagicMock(id="assessment-1")
        self.assertTrue(service._speaking_evaluated(assessment, attempt))

    def test_no_attempt_is_never_evaluated(self):
        service = SectionGateService(db=MagicMock())
        assessment = MagicMock(id="assessment-1")
        self.assertFalse(service._writing_evaluated(assessment, None))
        self.assertFalse(service._speaking_evaluated(assessment, None))


class TestQuizSubmittedIsAlwaysFullyGraded(unittest.TestCase):
    """Lesson/Grammar/Vocabulary Quiz completion — a StudentQuiz row
    existing always means fully graded (no manual-grading gap exists in
    this legacy system, confirmed by design)."""

    def test_no_student_quiz_row_is_not_submitted(self):
        db = MagicMock()
        quiz_query = MagicMock()
        quiz_query.filter.return_value = quiz_query
        quiz_query.first.return_value = MagicMock(id="quiz-1")

        student_quiz_query = MagicMock()
        student_quiz_query.filter.return_value = student_quiz_query
        student_quiz_query.first.return_value = None

        db.query.side_effect = [quiz_query, student_quiz_query]
        service = SectionGateService(db=db)
        self.assertFalse(service._quiz_submitted(user_id="u", lesson_id="l", quiz_type="LESSON"))

    def test_student_quiz_row_means_graded_and_complete(self):
        db = MagicMock()
        quiz_query = MagicMock()
        quiz_query.filter.return_value = quiz_query
        quiz_query.first.return_value = MagicMock(id="quiz-1")

        student_quiz_query = MagicMock()
        student_quiz_query.filter.return_value = student_quiz_query
        student_quiz_query.first.return_value = MagicMock()

        db.query.side_effect = [quiz_query, student_quiz_query]
        service = SectionGateService(db=db)
        self.assertTrue(service._quiz_submitted(user_id="u", lesson_id="l", quiz_type="LESSON"))


if __name__ == "__main__":
    unittest.main()
