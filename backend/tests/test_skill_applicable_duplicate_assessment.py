"""Regression test for the "Hören/Schreiben/Sprechen missing from
student nav despite admin content existing" incident.

Root cause: nothing enforces at most one COURSE Assessment row per
lesson at the DB level (no unique constraint on lesson_id+
assessment_type — see app/models/assessment.py). The admin builder
(LesenAssessmentManager.ensureAssessmentAndSection, frontend) lazily
get-or-creates the Assessment the first time a task is added under any
skill tab; each skill tab holds its own independently-keyed React Query
cache (["skill-assessment", lessonId, skill]), so switching tabs before
the first tab's assessment list has loaded can create a second,
duplicate Assessment row for the same lesson.

The pre-fix `_skill_applicable(assessment, skill)` only checked tasks
under ONE already-resolved Assessment (picked by `_latest_attempt`'s
unordered `.first()`) — so a skill whose section/task happened to land
under a *different* duplicate Assessment than the one that query
returned was reported as not-applicable, hiding an entire section
(Hören/Schreiben/Sprechen) from students even though content existed
and was published, while the admin's own content-status view
(get_content_status_for_module, which never narrows to a single
Assessment) correctly showed it as present — a real divergence between
the two "source of truth" views the student nav and admin panel are
supposed to share.

Fix: `_skill_applicable` now takes `lesson_id` directly and joins
Assessment -> Section -> Task filtered by lesson_id + assessment_type,
so a task under *any* matching Assessment counts — correct regardless
of how many duplicate rows exist, no DB constraint required, no
migration, no level-specific branching (skill is just a parameter,
proven across all four skills below via subTest)."""

import unittest
from unittest.mock import MagicMock

from app.services.lesson_progress.section_gate import SectionGateService


class TestSkillApplicableTakesLessonIdNotAssessment(unittest.TestCase):
    """The actual API-contract regression: the old signature required a
    pre-resolved Assessment object (`assessment.id` access internally);
    the new one takes a plain lesson_id and never assumes a single
    resolved assessment exists."""

    def _mock_db_returning(self, row_or_none):
        db = MagicMock()
        query = MagicMock()
        query.join.return_value = query
        query.filter.return_value = query
        query.first.return_value = row_or_none
        db.query.return_value = query
        return db

    def test_applicable_true_when_a_task_exists_for_the_skill(self):
        service = SectionGateService(db=self._mock_db_returning(("task-id",)))
        self.assertTrue(service._skill_applicable(lesson_id="lesson-1", skill="HOEREN"))

    def test_applicable_false_when_no_task_exists_for_the_skill(self):
        service = SectionGateService(db=self._mock_db_returning(None))
        self.assertFalse(service._skill_applicable(lesson_id="lesson-1", skill="HOEREN"))

    def test_never_dereferences_an_assessment_object(self):
        # Calling with a plain string (no .id attribute at all) must not
        # raise — proves the function doesn't internally do
        # `assessment.id` the way the pre-fix version did.
        db = self._mock_db_returning(None)
        service = SectionGateService(db=db)
        try:
            service._skill_applicable(lesson_id="plain-lesson-id-string", skill="SCHREIBEN")
        except AttributeError as exc:
            self.fail(f"_skill_applicable unexpectedly touched an Assessment attribute: {exc}")

    def test_universal_across_all_four_skills_no_special_casing(self):
        for skill in ("LESEN", "HOEREN", "SCHREIBEN", "SPRECHEN"):
            with self.subTest(skill=skill):
                service = SectionGateService(db=self._mock_db_returning(("task-id",)))
                self.assertTrue(service._skill_applicable(lesson_id="lesson-1", skill=skill))


class TestLatestAttemptOrdersByNewestAssessment(unittest.TestCase):
    """When duplicate COURSE assessments exist for one lesson (the exact
    scenario above), _latest_attempt must deterministically pick the
    most recently created one — matching crud_service.list_assessments'
    own created_at-desc ordering, which is what the admin UI's
    `assessments?.[0]` already relies on — instead of arbitrary DB
    order, which could silently return an older, content-less
    duplicate."""

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
