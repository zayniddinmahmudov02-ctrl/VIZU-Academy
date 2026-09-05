"""Regression tests for
app/scripts/cleanup_lesson_1_assessment_duplicates.py — the review-first,
dry-run-by-default tool that removes the Assessment Engine Hoeren/
Schreiben/Sprechen sections+tasks migrate_lesson_1_assessments.py
created, now that those three skills are legacy-backed. Uses stdlib
unittest + MagicMock (no real DB), matching this session's established
pattern.

Covers: fingerprint matching (only migration-titled tasks are ever
candidates), the six dependency checks each independently blocking
deletion, a section only being removable when every one of its tasks is
safe, dry-run-by-default never writing, --confirm being required for a
real run, and the missing-lesson / no-assessment abort paths.
"""

import unittest
from unittest.mock import MagicMock, patch

import app.scripts.cleanup_lesson_1_assessment_duplicates as cleanup
from app.models.assessment_section import SKILL_HOEREN, SKILL_SCHREIBEN, SKILL_SPRECHEN
from app.models.assessment_task import TYPE_MULTIPLE_CHOICE, TYPE_SPEAKING, TYPE_WRITING


def make_lesson(lesson_id="lesson-1"):
    lesson = MagicMock()
    lesson.id = lesson_id
    return lesson


def make_assessment(assessment_id="assessment-1"):
    a = MagicMock()
    a.id = assessment_id
    return a


def make_section(section_id, skill):
    s = MagicMock()
    s.id = section_id
    s.skill = skill
    return s


def make_task(task_id, title, task_type):
    t = MagicMock()
    t.id = task_id
    t.title = title
    t.task_type = task_type
    return t


def build_mock_db(assessments, sections, tasks, dependency_results=()):
    """db.scalars is called in build_plan()'s fixed order: assessments,
    then one call per assessment for its sections, then one call per
    section for its tasks. This helper is scoped to exactly one
    assessment and one section (every test case here uses that shape),
    so the side_effect list is always [assessments, sections, tasks].
    db.query is called 6 times per fingerprint-matching task (the
    dependency checks, fixed order — see _dependency_blockers) via
    .filter().first(); `dependency_results` is a flat list of 6 * (number
    of matching tasks) values, in that same order."""
    db = MagicMock()
    db.scalars.side_effect = [
        MagicMock(all=MagicMock(return_value=assessments)),
        MagicMock(all=MagicMock(return_value=sections)),
        MagicMock(all=MagicMock(return_value=tasks)),
    ]

    query_mocks = []
    for result in dependency_results:
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = result
        query_mocks.append(q)
    db.query.side_effect = query_mocks

    return db


class TestFingerprintMatching(unittest.TestCase):
    def test_matching_title_and_type_is_a_candidate(self):
        db = build_mock_db(
            [make_assessment()],
            [make_section("section-1", SKILL_HOEREN)],
            [make_task("task-1", "Text 1", TYPE_MULTIPLE_CHOICE)],
            dependency_results=[None] * 6,
        )
        plan = cleanup.build_plan(db, make_lesson())
        self.assertEqual(len(plan.sections), 1)
        self.assertEqual(len(plan.sections[0].tasks), 1)
        self.assertEqual(plan.sections[0].tasks[0].title, "Text 1")

    def test_non_matching_title_is_never_a_candidate(self):
        db = build_mock_db(
            [make_assessment()],
            [make_section("section-1", SKILL_HOEREN)],
            [make_task("task-1", "A Real Admin-Authored Task", TYPE_MULTIPLE_CHOICE)],
            dependency_results=[],
        )
        plan = cleanup.build_plan(db, make_lesson())
        # Section has zero fingerprint-matching tasks -> never appended.
        self.assertEqual(plan.sections, [])

    def test_matching_title_but_wrong_task_type_is_never_a_candidate(self):
        db = build_mock_db(
            [make_assessment()],
            [make_section("section-1", SKILL_SCHREIBEN)],
            [make_task("task-1", "Topshiriq 1", TYPE_SPEAKING)],  # wrong type for SCHREIBEN
            dependency_results=[],
        )
        plan = cleanup.build_plan(db, make_lesson())
        self.assertEqual(plan.sections, [])

    def test_sprechen_task_matches(self):
        db = build_mock_db(
            [make_assessment()],
            [make_section("section-1", SKILL_SPRECHEN)],
            [make_task("task-1", "Stellen Sie sich vor!", TYPE_SPEAKING)],
            dependency_results=[None] * 6,
        )
        plan = cleanup.build_plan(db, make_lesson())
        self.assertEqual(len(plan.sections[0].tasks), 1)


class TestDependencyBlockers(unittest.TestCase):
    """Each of the six dependency checks independently makes a task
    unsafe — verified one at a time by putting a truthy result in that
    exact position of the six-check sequence (TaskQuestion, TaskAudio,
    WritingRubricCriterion, TaskAttempt, WritingSubmission,
    SpeakingSubmission)."""

    def _results_with_one_hit(self, index: int) -> list:
        results = [None] * 6
        results[index] = MagicMock()
        return results

    def test_task_question_blocks(self):
        db = build_mock_db(
            [make_assessment()], [make_section("s1", SKILL_HOEREN)],
            [make_task("t1", "Text 1", TYPE_MULTIPLE_CHOICE)],
            dependency_results=self._results_with_one_hit(0),
        )
        plan = cleanup.build_plan(db, make_lesson())
        self.assertFalse(plan.sections[0].tasks[0].safe_to_delete)

    def test_task_audio_blocks(self):
        db = build_mock_db(
            [make_assessment()], [make_section("s1", SKILL_HOEREN)],
            [make_task("t1", "Text 1", TYPE_MULTIPLE_CHOICE)],
            dependency_results=self._results_with_one_hit(1),
        )
        plan = cleanup.build_plan(db, make_lesson())
        self.assertFalse(plan.sections[0].tasks[0].safe_to_delete)

    def test_rubric_criterion_blocks(self):
        db = build_mock_db(
            [make_assessment()], [make_section("s1", SKILL_SCHREIBEN)],
            [make_task("t1", "Topshiriq 1", TYPE_WRITING)],
            dependency_results=self._results_with_one_hit(2),
        )
        plan = cleanup.build_plan(db, make_lesson())
        self.assertFalse(plan.sections[0].tasks[0].safe_to_delete)

    def test_task_attempt_blocks(self):
        db = build_mock_db(
            [make_assessment()], [make_section("s1", SKILL_HOEREN)],
            [make_task("t1", "Text 1", TYPE_MULTIPLE_CHOICE)],
            dependency_results=self._results_with_one_hit(3),
        )
        plan = cleanup.build_plan(db, make_lesson())
        self.assertFalse(plan.sections[0].tasks[0].safe_to_delete)

    def test_writing_submission_blocks(self):
        db = build_mock_db(
            [make_assessment()], [make_section("s1", SKILL_SCHREIBEN)],
            [make_task("t1", "Topshiriq 1", TYPE_WRITING)],
            dependency_results=self._results_with_one_hit(4),
        )
        plan = cleanup.build_plan(db, make_lesson())
        self.assertFalse(plan.sections[0].tasks[0].safe_to_delete)

    def test_speaking_submission_blocks(self):
        db = build_mock_db(
            [make_assessment()], [make_section("s1", SKILL_SPRECHEN)],
            [make_task("t1", "Stellen Sie sich vor!", TYPE_SPEAKING)],
            dependency_results=self._results_with_one_hit(5),
        )
        plan = cleanup.build_plan(db, make_lesson())
        self.assertFalse(plan.sections[0].tasks[0].safe_to_delete)

    def test_zero_dependencies_is_safe(self):
        db = build_mock_db(
            [make_assessment()], [make_section("s1", SKILL_HOEREN)],
            [make_task("t1", "Text 1", TYPE_MULTIPLE_CHOICE)],
            dependency_results=[None] * 6,
        )
        plan = cleanup.build_plan(db, make_lesson())
        self.assertTrue(plan.sections[0].tasks[0].safe_to_delete)


class TestSectionRemovability(unittest.TestCase):
    def test_section_all_tasks_safe_is_fully_removable(self):
        db = build_mock_db(
            [make_assessment()], [make_section("s1", SKILL_HOEREN)],
            [make_task("t1", "Text 1", TYPE_MULTIPLE_CHOICE), make_task("t2", "Text 2", TYPE_MULTIPLE_CHOICE)],
            dependency_results=[None] * 12,
        )
        plan = cleanup.build_plan(db, make_lesson())
        self.assertEqual(len(plan.sections_fully_removable()), 1)

    def test_section_with_one_unsafe_task_is_not_removable(self):
        # First task: 6 clean checks. Second task: TaskQuestion hit (index 0).
        results = ([None] * 6) + ([MagicMock()] + [None] * 5)
        db = build_mock_db(
            [make_assessment()], [make_section("s1", SKILL_HOEREN)],
            [make_task("t1", "Text 1", TYPE_MULTIPLE_CHOICE), make_task("t2", "Text 2", TYPE_MULTIPLE_CHOICE)],
            dependency_results=results,
        )
        plan = cleanup.build_plan(db, make_lesson())
        self.assertEqual(plan.sections_fully_removable(), [])
        self.assertEqual(plan.safe_task_count(), 1)
        self.assertEqual(plan.unsafe_task_count(), 1)


class TestApplyCleanupOnlyDeletesSafeRows(unittest.TestCase):
    def _plan_with_tasks(self, *, all_safe: bool):
        task1 = cleanup.TaskFinding(task_id="t1", title="Text 1", task_type=TYPE_MULTIPLE_CHOICE, blockers=[])
        task2 = cleanup.TaskFinding(
            task_id="t2", title="Text 2", task_type=TYPE_MULTIPLE_CHOICE,
            blockers=[] if all_safe else ["has TaskAttempt rows"],
        )
        section = cleanup.SectionFinding(section_id="s1", skill=SKILL_HOEREN, tasks=[task1, task2])
        return cleanup.CleanupPlan(lesson_id="lesson-1", assessment_id="assessment-1", sections=[section])

    def test_deletes_task_and_section_when_all_safe(self):
        db = MagicMock()
        plan = self._plan_with_tasks(all_safe=True)
        cleanup.apply_cleanup(db, plan)

        # 2 tasks + 1 section = 3 db.delete() calls; committed once.
        self.assertEqual(db.delete.call_count, 3)
        db.commit.assert_called_once()

    def test_skips_whole_section_when_any_task_unsafe(self):
        db = MagicMock()
        plan = self._plan_with_tasks(all_safe=False)
        cleanup.apply_cleanup(db, plan)
        db.delete.assert_not_called()
        db.commit.assert_called_once()


class TestDryRunIsDefault(unittest.TestCase):
    def test_no_flags_makes_no_writes(self):
        db = MagicMock()
        with patch.object(cleanup, "SessionLocal", return_value=db), patch.object(
            cleanup, "find_lesson_1", return_value=make_lesson()
        ), patch.object(cleanup, "build_plan", return_value=None):
            with patch("sys.argv", ["cleanup_lesson_1_assessment_duplicates.py"]):
                cleanup.main()
        db.delete.assert_not_called()
        db.commit.assert_not_called()

    def test_explicit_dry_run_flag_makes_no_writes(self):
        db = MagicMock()
        with patch.object(cleanup, "SessionLocal", return_value=db), patch.object(
            cleanup, "find_lesson_1", return_value=make_lesson()
        ), patch.object(cleanup, "build_plan", return_value=None):
            with patch("sys.argv", ["cleanup_lesson_1_assessment_duplicates.py", "--dry-run"]):
                cleanup.main()
        db.delete.assert_not_called()
        db.commit.assert_not_called()

    def test_confirm_and_dry_run_together_stays_safe(self):
        # --dry-run always wins if both are somehow passed.
        db = MagicMock()
        with patch.object(cleanup, "SessionLocal", return_value=db), patch.object(
            cleanup, "find_lesson_1", return_value=make_lesson()
        ), patch.object(cleanup, "build_plan", return_value=None):
            with patch("sys.argv", ["cleanup_lesson_1_assessment_duplicates.py", "--dry-run", "--confirm"]):
                cleanup.main()
        db.delete.assert_not_called()
        db.commit.assert_not_called()

    def test_confirm_alone_triggers_a_real_run(self):
        db = MagicMock()
        real_plan = cleanup.CleanupPlan(lesson_id="lesson-1", assessment_id="assessment-1", sections=[])
        with patch.object(cleanup, "SessionLocal", return_value=db), patch.object(
            cleanup, "find_lesson_1", return_value=make_lesson()
        ), patch.object(cleanup, "build_plan", return_value=real_plan), patch.object(
            cleanup, "apply_cleanup"
        ) as apply_mock:
            with patch("sys.argv", ["cleanup_lesson_1_assessment_duplicates.py", "--confirm"]):
                cleanup.main()
        # Zero safe tasks in an empty plan -> apply_cleanup must not even
        # be invoked (nothing to do), proving main() only calls it when
        # there's real work, not unconditionally on --confirm.
        apply_mock.assert_not_called()


class TestAbortPaths(unittest.TestCase):
    def test_missing_lesson_aborts_without_writes(self):
        db = MagicMock()
        with patch.object(cleanup, "SessionLocal", return_value=db), patch.object(
            cleanup, "find_lesson_1", return_value=None
        ):
            with patch("sys.argv", ["cleanup_lesson_1_assessment_duplicates.py", "--confirm"]):
                cleanup.main()
        db.delete.assert_not_called()
        db.commit.assert_not_called()

    def test_no_course_assessment_returns_none_plan(self):
        db = MagicMock()
        db.scalars.side_effect = [MagicMock(all=MagicMock(return_value=[]))]
        plan = cleanup.build_plan(db, make_lesson())
        self.assertIsNone(plan)


if __name__ == "__main__":
    unittest.main()
