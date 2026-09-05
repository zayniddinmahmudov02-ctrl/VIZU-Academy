"""Regression tests for Lesen/Hören/Schreiben/Sprechen applicability.

History: this file originally covered `_skill_applicable`, which checked
Assessment Engine task existence for these four skills, joining
Assessment -> Section -> Task by lesson_id (fixed from an earlier bug
where a duplicate COURSE Assessment row per lesson could hide an entire
section from students — see git history for the original incident).

That whole code path — and the Assessment Engine as the student-facing
source for these four skills — no longer exists: Lesen/Hören/Schreiben/
Sprechen are now LEGACY-backed (readings/listenings/writings/speakings
tables are the source of truth; see section_gate.py's module docstring
and reading/listening/writing/speaking-section.tsx). `_skill_applicable`
itself was removed. This file now covers its replacements:
`_reading_applicable`, `_listening_applicable`, `_writing_applicable`,
`_speaking_applicable` — each a simple existence check against its
legacy table, with no is_published filter (matches the old method's
behavior: a row's own status never gated the nav tab, only the
content-fetch endpoint's published_only filter does)."""

import unittest
from unittest.mock import MagicMock

from app.services.lesson_progress.section_gate import SectionGateService


class TestLegacyApplicableExistenceOnly(unittest.TestCase):
    """Each of the four legacy-applicable checks is a plain existence
    query against its own table — no is_published filter, no Assessment
    Engine involvement at all."""

    def _mock_db_returning(self, row_or_none):
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = row_or_none
        db.query.return_value = query
        return db

    def test_reading_applicable_true_when_a_row_exists(self):
        service = SectionGateService(db=self._mock_db_returning(MagicMock()))
        self.assertTrue(service._reading_applicable(lesson_id="lesson-1"))

    def test_reading_applicable_false_when_no_row_exists(self):
        service = SectionGateService(db=self._mock_db_returning(None))
        self.assertFalse(service._reading_applicable(lesson_id="lesson-1"))

    def test_listening_applicable_true_regardless_of_publish_status(self):
        # A Listening row with is_published=False (no real audio yet,
        # see seed_lesson_1.py) still makes the section applicable —
        # this query never filters on is_published at all.
        service = SectionGateService(db=self._mock_db_returning(MagicMock()))
        self.assertTrue(service._listening_applicable(lesson_id="lesson-1"))

    def test_listening_applicable_false_when_no_row_exists(self):
        service = SectionGateService(db=self._mock_db_returning(None))
        self.assertFalse(service._listening_applicable(lesson_id="lesson-1"))

    def test_writing_applicable_true_when_a_row_exists(self):
        service = SectionGateService(db=self._mock_db_returning(MagicMock()))
        self.assertTrue(service._writing_applicable(lesson_id="lesson-1"))

    def test_writing_applicable_false_when_no_row_exists(self):
        service = SectionGateService(db=self._mock_db_returning(None))
        self.assertFalse(service._writing_applicable(lesson_id="lesson-1"))

    def test_speaking_applicable_true_when_a_row_exists(self):
        service = SectionGateService(db=self._mock_db_returning(MagicMock()))
        self.assertTrue(service._speaking_applicable(lesson_id="lesson-1"))

    def test_speaking_applicable_false_when_no_row_exists(self):
        service = SectionGateService(db=self._mock_db_returning(None))
        self.assertFalse(service._speaking_applicable(lesson_id="lesson-1"))

    def test_skill_applicable_no_longer_exists(self):
        # Proves the Assessment-Engine-based method was actually removed,
        # not just superseded/left dangling.
        self.assertFalse(hasattr(SectionGateService, "_skill_applicable"))


class TestLatestAttemptOrdersByNewestAssessment(unittest.TestCase):
    """_latest_attempt still exists (feeds the now-vestigial-but-present
    Assessment-Engine-based `completed` signal for lesen/hoeren/
    schreiben/sprechen — see section_gate.py's module docstring). When
    duplicate COURSE assessments exist for one lesson, it must
    deterministically pick the most recently created one — matching
    crud_service.list_assessments' own created_at-desc ordering."""

    def test_orders_assessment_query_by_created_at_desc(self):
        db = MagicMock()
        assessment_query = MagicMock()
        assessment_query.filter.return_value = assessment_query
        assessment_query.order_by.return_value = assessment_query
        assessment_query.first.return_value = None

        attempt_query = MagicMock()
        attempt_query.filter.return_value = attempt_query
        attempt_query.order_by.return_value = attempt_query
        attempt_query.first.return_value = None

        db.query.side_effect = [assessment_query]
        service = SectionGateService(db=db)
        service._latest_attempt(user_id="u", lesson_id="l")

        assessment_query.order_by.assert_called_once()


if __name__ == "__main__":
    unittest.main()
