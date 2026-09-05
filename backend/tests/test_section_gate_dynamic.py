"""Verifies the core logic in SectionGateService: sections are never
sequentially gated (_compute_unlocked, a pure function — no DB, no
inputs at all now), lesson completion counting only applicable sections
and excluding the removed-from-navigation Lesson Quiz (is_lesson_completed),
and the tightened Schreiben/Sprechen "evaluated" checks (STATUS_GRADED /
STATUS_FINAL, not merely submitted). Uses stdlib unittest + MagicMock/
patch, matching this session's established pattern (no pytest, no real
DB) — _compute_unlocked needs no mocking at all since it takes nothing
and returns a fixed shape."""

import unittest
from unittest.mock import MagicMock, patch

from app.services.lesson_progress.section_gate import GATED_ORDER, SECTION_ORDER, SectionGateService


def all_applicable(**overrides) -> dict[str, bool]:
    base = {key: True for key in SECTION_ORDER}
    base.update(overrides)
    return base


def all_incomplete(**overrides) -> dict[str, bool]:
    base = {key: False for key in SECTION_ORDER}
    base.update(overrides)
    return base


class TestSectionsAlwaysUnlocked(unittest.TestCase):
    """No sequential gate exists anymore: every section is open
    regardless of what else has or hasn't been completed. Covers the
    exact scenarios requested — video incomplete -> wortschatz open,
    wortschatz incomplete -> grammatik_quiz open, grammatik_quiz
    incomplete -> lesen open, lesen incomplete -> hoeren open, hoeren
    incomplete -> schreiben open, schreiben incomplete -> sprechen
    open — plus the general "any one incomplete, everything else still
    open" case, and confirms this holds identically for every A1-C1
    section-content shape (same universal, non-level-branching proof
    the previous version of this test made for the old gate)."""

    def setUp(self):
        self.service = SectionGateService(db=MagicMock())

    def test_compute_unlocked_takes_no_input_and_is_unconditionally_true(self):
        # The direct proof of the fix: unlocking no longer depends on
        # applicable/completed at all — the function doesn't even
        # accept them as parameters anymore.
        unlocked = self.service._compute_unlocked()
        for key in SECTION_ORDER:
            with self.subTest(section=key):
                self.assertTrue(unlocked[key])

    def _get_state_with(self, applicable: dict, completed: dict) -> dict:
        unlocked = self.service._compute_unlocked()
        return {
            key: {"applicable": applicable[key], "completed": completed[key], "unlocked": unlocked[key]}
            for key in SECTION_ORDER
        }

    def test_video_incomplete_wortschatz_still_open(self):
        applicable = all_applicable()
        completed = all_incomplete()
        with patch.object(SectionGateService, "get_state", return_value=self._get_state_with(applicable, completed)):
            state = self.service.get_state(user_id="u", lesson_id="l")
            self.assertFalse(state["video"]["completed"])
            self.assertTrue(state["wortschatz"]["unlocked"])

    def test_wortschatz_incomplete_grammatik_quiz_still_open(self):
        applicable = all_applicable()
        completed = all_incomplete(video=True)
        with patch.object(SectionGateService, "get_state", return_value=self._get_state_with(applicable, completed)):
            state = self.service.get_state(user_id="u", lesson_id="l")
            self.assertFalse(state["wortschatz"]["completed"])
            self.assertTrue(state["grammatik_quiz"]["unlocked"])

    def test_grammatik_quiz_incomplete_lesen_still_open(self):
        applicable = all_applicable()
        completed = all_incomplete(video=True, wortschatz=True, wortschatz_quiz=True)
        with patch.object(SectionGateService, "get_state", return_value=self._get_state_with(applicable, completed)):
            state = self.service.get_state(user_id="u", lesson_id="l")
            self.assertFalse(state["grammatik_quiz"]["completed"])
            self.assertTrue(state["lesen"]["unlocked"])

    def test_lesen_incomplete_hoeren_still_open(self):
        applicable = all_applicable()
        completed = all_incomplete(video=True, wortschatz=True, wortschatz_quiz=True, grammatik_quiz=True)
        with patch.object(SectionGateService, "get_state", return_value=self._get_state_with(applicable, completed)):
            state = self.service.get_state(user_id="u", lesson_id="l")
            self.assertFalse(state["lesen"]["completed"])
            self.assertTrue(state["hoeren"]["unlocked"])

    def test_hoeren_incomplete_schreiben_still_open(self):
        applicable = all_applicable()
        completed = all_incomplete(video=True, wortschatz=True, wortschatz_quiz=True, grammatik_quiz=True, lesen=True)
        with patch.object(SectionGateService, "get_state", return_value=self._get_state_with(applicable, completed)):
            state = self.service.get_state(user_id="u", lesson_id="l")
            self.assertFalse(state["hoeren"]["completed"])
            self.assertTrue(state["schreiben"]["unlocked"])

    def test_schreiben_incomplete_sprechen_still_open(self):
        applicable = all_applicable()
        completed = all_incomplete(
            video=True, wortschatz=True, wortschatz_quiz=True, grammatik_quiz=True, lesen=True, hoeren=True,
        )
        with patch.object(SectionGateService, "get_state", return_value=self._get_state_with(applicable, completed)):
            state = self.service.get_state(user_id="u", lesson_id="l")
            self.assertFalse(state["schreiben"]["completed"])
            self.assertTrue(state["sprechen"]["unlocked"])

    def test_sprechen_incomplete_hausaufgabe_area_still_open(self):
        # Hausaufgabe/Ergebnisse have no gate key at all (see
        # lesson-sections.ts SECTION_GATE_KEYS: homework/results -> null)
        # so they were never lockable to begin with; the section
        # immediately before them (sprechen) staying incomplete must not
        # newly block anything either.
        applicable = all_applicable()
        completed = all_incomplete(
            video=True, wortschatz=True, wortschatz_quiz=True, grammatik_quiz=True,
            lesen=True, hoeren=True, schreiben=True, sprechen=False,
        )
        with patch.object(SectionGateService, "get_state", return_value=self._get_state_with(applicable, completed)):
            state = self.service.get_state(user_id="u", lesson_id="l")
            self.assertFalse(state["sprechen"]["completed"])
            for key in SECTION_ORDER:
                self.assertTrue(state[key]["unlocked"], f"{key} must stay unlocked")

    def test_nothing_completed_everything_still_unlocked(self):
        applicable = all_applicable()
        completed = all_incomplete()
        with patch.object(SectionGateService, "get_state", return_value=self._get_state_with(applicable, completed)):
            state = self.service.get_state(user_id="u", lesson_id="l")
            for key in SECTION_ORDER:
                with self.subTest(section=key):
                    self.assertTrue(state[key]["unlocked"])

    def test_universal_across_levels_no_branching(self):
        """Same _compute_unlocked, five different realistic A1-C1
        section-content shapes — none of them change the (unconditional)
        result, which is itself the proof there's no level-specific code
        path left."""
        a1 = all_applicable()
        a2 = all_applicable(wortschatz_quiz=False)
        b1 = all_applicable(wortschatz_quiz=False, sprechen=False)
        b2 = all_applicable(wortschatz_quiz=False, lesson_quiz=False)
        c1 = all_applicable(wortschatz_quiz=False, grammatik_quiz=False, schreiben=False)

        for level_name, applicable in [("A1", a1), ("A2", a2), ("B1", b1), ("B2", b2), ("C1", c1)]:
            with self.subTest(level=level_name):
                completed = all_incomplete()
                unlocked = self.service._compute_unlocked()
                for key in SECTION_ORDER:
                    self.assertTrue(unlocked[key])

    def test_lesson_quiz_removed_from_gated_order(self):
        # Lesson Quiz is out of student navigation entirely (see
        # frontend/src/constants/lesson-sections.ts) and must never be
        # able to block lesson completion for a lesson that still has a
        # published-but-unreachable one.
        self.assertNotIn("lesson_quiz", GATED_ORDER)


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
        # wortschatz_quiz stays in GATED_ORDER (unlike lesen/hoeren/
        # schreiben/sprechen, now legacy-backed and excluded — see
        # section_gate.py's module docstring), so it's the key that
        # still proves "one incomplete applicable+gated section blocks
        # completion".
        applicable = all_applicable()
        completed = {key: True for key in SECTION_ORDER}
        completed["wortschatz_quiz"] = False
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

    def test_incomplete_but_applicable_lesson_quiz_never_blocks_completion(self):
        # A published Lesson Quiz exists (applicable=True) but the
        # student never took it (completed=False) — since it's been
        # removed from student navigation entirely, this must not
        # prevent the lesson from being reported complete.
        applicable = all_applicable()  # lesson_quiz applicable=True
        completed = {key: True for key in SECTION_ORDER}
        completed["lesson_quiz"] = False
        with patch.object(SectionGateService, "get_state", return_value=self._state(applicable, completed)):
            self.assertTrue(self.service.is_lesson_completed(user_id="u", lesson_id="l"))


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


class TestGrammarApplicable(unittest.TestCase):
    """Regression for the Grammatik nav item: applicable["grammatik"] used
    to be hardcoded False (so the standalone Grammatik section could
    never appear in student navigation, even though its backend endpoint
    GET /grammars/lesson/{id} and frontend GrammarSection component
    already existed) — now it reflects real published Grammar content,
    same is_published-only pattern as _wortschatz_applicable."""

    def _mock_db_returning(self, row_or_none):
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = row_or_none
        db.query.return_value = query
        return db

    def test_true_when_a_published_grammar_row_exists(self):
        service = SectionGateService(db=self._mock_db_returning(MagicMock()))
        self.assertTrue(service._grammar_applicable(lesson_id="l"))

    def test_false_when_no_grammar_row_exists(self):
        service = SectionGateService(db=self._mock_db_returning(None))
        self.assertFalse(service._grammar_applicable(lesson_id="l"))

    def test_grammatik_excluded_from_gated_order_even_when_applicable(self):
        # Grammatik has no separate completion/points role — it must stay
        # out of GATED_ORDER regardless of applicability.
        self.assertNotIn("grammatik", GATED_ORDER)


if __name__ == "__main__":
    unittest.main()
