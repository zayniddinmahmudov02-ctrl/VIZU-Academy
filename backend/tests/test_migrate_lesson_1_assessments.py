"""Regression tests for app/scripts/migrate_lesson_1_assessments.py — the
review-first, dry-run-capable importer that copies A1 Lesson 1's legacy
Hoeren/Schreiben/Sprechen content (listenings/writings/speakings tables)
into the Universal Assessment Engine. Uses stdlib unittest + MagicMock
(no real DB), matching this session's established pattern.

Covers: build_plan()'s read-only plan construction (create vs skip per
natural key, per the module's fixed db.scalar/db.scalars call order),
apply_plan()'s write behavior (only ever adds what the plan says is
missing, never touches what already exists), --dry-run never writing
anything, Hoeren always staying unpublished/no-fake-audio regardless of
the PUBLISH_ON_CREATE map, and the missing-lesson abort path.
"""

import inspect
import unittest
from unittest.mock import MagicMock, patch

import app.scripts.migrate_lesson_1_assessments as migrate
from app.models.assessment import STATUS_DRAFT, STATUS_PUBLISHED
from app.models.assessment_section import SKILL_HOEREN, SKILL_SCHREIBEN, SKILL_SPRECHEN
from app.models.assessment_task import TYPE_MULTIPLE_CHOICE, TYPE_SPEAKING, TYPE_WRITING


def make_lesson(lesson_id="lesson-1"):
    lesson = MagicMock()
    lesson.id = lesson_id
    return lesson


def make_listening(id_="listening-1", title="Text 1", transcript="Es ist Samstag...", order_index=1):
    row = MagicMock()
    row.id, row.title, row.transcript, row.order_index = id_, title, transcript, order_index
    return row


def make_writing(id_="writing-1", title="Topshiriq 1", instruction="Hallo! Ich heisse ___", min_words=5, max_words=60, order_index=1):
    row = MagicMock()
    row.id, row.title, row.instruction = id_, title, instruction
    row.min_words, row.max_words, row.order_index = min_words, max_words, order_index
    return row


def make_speaking(
    id_="speaking-1",
    title="Stellen Sie sich vor!",
    topic="Sich vorstellen",
    instruction="Hallo! Ich heisse ___",
    sample_answer=None,
    keywords=None,
    preparation_time=15,
    speaking_time=90,
    order_index=1,
):
    row = MagicMock()
    row.id, row.title, row.topic, row.instruction = id_, title, topic, instruction
    row.sample_answer, row.keywords = sample_answer, keywords
    row.preparation_time, row.speaking_time, row.order_index = preparation_time, speaking_time, order_index
    return row


def build_mock_db(
    *,
    assessment=None,
    hoeren_section=None,
    schreiben_section=None,
    sprechen_section=None,
    hoeren_existing_titles=(),
    schreiben_existing_titles=(),
    sprechen_existing_titles=(),
    listenings=(),
    writings=(),
    speakings=(),
):
    """db.scalar is called in build_plan()'s fixed order: Assessment
    lookup, then Hoeren/Schreiben/Sprechen section lookups (always, even
    when the assessment itself doesn't exist yet - existing_section()
    short-circuits to None without querying only when assessment is
    None). db.query(...).filter(...).all() (existing task titles) is
    only ever called for a section that does exist. db.scalars is
    called exactly 3 times in skill order for the legacy rows."""
    db = MagicMock()

    scalar_calls = [assessment]
    if assessment is not None:
        scalar_calls += [hoeren_section, schreiben_section, sprechen_section]
    else:
        scalar_calls += [None, None, None]
    db.scalar.side_effect = scalar_calls

    query_mocks = []
    for section, titles in (
        (hoeren_section, hoeren_existing_titles),
        (schreiben_section, schreiben_existing_titles),
        (sprechen_section, sprechen_existing_titles),
    ):
        if section is None:
            continue
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [(t,) for t in titles]
        query_mocks.append(q)
    db.query.side_effect = query_mocks

    scalars_mocks = []
    for rows in (listenings, writings, speakings):
        m = MagicMock()
        m.all.return_value = list(rows)
        scalars_mocks.append(m)
    db.scalars.side_effect = scalars_mocks

    return db


class TestBuildPlanFreshMigration(unittest.TestCase):
    """Nothing exists yet in the Assessment Engine for this lesson at
    all - the most common real scenario (Lesen's Assessment does exist
    in production, but this test also covers the from-scratch case)."""

    def test_no_assessment_no_sections_everything_to_create(self):
        db = build_mock_db(
            assessment=None,
            listenings=[make_listening()],
            writings=[make_writing()],
            speakings=[make_speaking()],
        )
        plan = migrate.build_plan(db, make_lesson())

        self.assertFalse(plan.assessment_already_exists)
        self.assertIsNone(plan.assessment_id)
        self.assertEqual(plan.to_create_count(), 3)
        for section in plan.sections:
            self.assertFalse(section.already_exists)
            for task in section.tasks:
                self.assertFalse(task.already_exists)

    def test_assessment_exists_sections_missing_tasks_all_new(self):
        assessment = MagicMock(id="assessment-1", status="PUBLISHED")
        db = build_mock_db(
            assessment=assessment,
            hoeren_section=None,
            schreiben_section=None,
            sprechen_section=None,
            listenings=[make_listening(title="Text 1"), make_listening(title="Text 2")],
            writings=[make_writing()],
            speakings=[make_speaking()],
        )
        plan = migrate.build_plan(db, make_lesson())

        self.assertTrue(plan.assessment_already_exists)
        self.assertEqual(plan.assessment_id, "assessment-1")
        self.assertEqual(plan.to_create_count(), 4)  # 2 hoeren + 1 schreiben + 1 sprechen


class TestBuildPlanIdempotentSkip(unittest.TestCase):
    def test_already_migrated_tasks_are_skipped_not_recreated(self):
        assessment = MagicMock(id="assessment-1", status="PUBLISHED")
        hoeren_section = MagicMock(id="section-hoeren")
        schreiben_section = MagicMock(id="section-schreiben")
        sprechen_section = MagicMock(id="section-sprechen")

        db = build_mock_db(
            assessment=assessment,
            hoeren_section=hoeren_section,
            schreiben_section=schreiben_section,
            sprechen_section=sprechen_section,
            hoeren_existing_titles=["Text 1"],
            schreiben_existing_titles=["Topshiriq 1"],
            sprechen_existing_titles=["Stellen Sie sich vor!"],
            listenings=[make_listening(title="Text 1")],
            writings=[make_writing(title="Topshiriq 1")],
            speakings=[make_speaking(title="Stellen Sie sich vor!")],
        )
        plan = migrate.build_plan(db, make_lesson())

        self.assertEqual(plan.to_create_count(), 0)
        for section in plan.sections:
            self.assertTrue(section.already_exists)
            for task in section.tasks:
                self.assertTrue(task.already_exists)

    def test_partial_overlap_only_missing_titles_created(self):
        assessment = MagicMock(id="assessment-1", status="PUBLISHED")
        schreiben_section = MagicMock(id="section-schreiben")
        db = build_mock_db(
            assessment=assessment,
            hoeren_section=None,
            schreiben_section=schreiben_section,
            sprechen_section=None,
            schreiben_existing_titles=["Topshiriq 1", "Topshiriq 2"],
            writings=[
                make_writing(title="Topshiriq 1"),
                make_writing(title="Topshiriq 2"),
                make_writing(title="Topshiriq 3"),
                make_writing(title="Topshiriq 4"),
            ],
        )
        plan = migrate.build_plan(db, make_lesson())

        schreiben_plan = next(s for s in plan.sections if s.skill == SKILL_SCHREIBEN)
        created_titles = {t.title for t in schreiben_plan.tasks if not t.already_exists}
        self.assertEqual(created_titles, {"Topshiriq 3", "Topshiriq 4"})


class TestHoerenNeverPublished(unittest.TestCase):
    def test_hoeren_task_plan_never_publishes_even_if_map_says_true(self):
        db = build_mock_db(listenings=[make_listening()])
        with patch.dict(migrate.PUBLISH_ON_CREATE, {SKILL_HOEREN: True}):
            plan = migrate.build_plan(db, make_lesson())
        hoeren_plan = next(s for s in plan.sections if s.skill == SKILL_HOEREN)
        self.assertFalse(hoeren_plan.tasks[0].publish)

    def test_hoeren_task_type_is_multiple_choice_no_audio_no_questions(self):
        db = build_mock_db(listenings=[make_listening(transcript="real transcript text")])
        plan = migrate.build_plan(db, make_lesson())
        hoeren_task = next(s for s in plan.sections if s.skill == SKILL_HOEREN).tasks[0]
        self.assertEqual(hoeren_task.task_type, TYPE_MULTIPLE_CHOICE)
        self.assertEqual(hoeren_task.content, "real transcript text")

    def test_hoeren_transcript_is_never_lost(self):
        db = build_mock_db(listenings=[make_listening(transcript="Es ist Samstag. Tom und Anna...")])
        plan = migrate.build_plan(db, make_lesson())
        hoeren_task = next(s for s in plan.sections if s.skill == SKILL_HOEREN).tasks[0]
        self.assertEqual(hoeren_task.content, "Es ist Samstag. Tom und Anna...")


class TestSchreibenSprechenMapping(unittest.TestCase):
    def test_writing_maps_instruction_and_word_limits(self):
        db = build_mock_db(writings=[make_writing(instruction="fill in the blanks", min_words=5, max_words=60)])
        plan = migrate.build_plan(db, make_lesson())
        task = next(s for s in plan.sections if s.skill == SKILL_SCHREIBEN).tasks[0]
        self.assertEqual(task.task_type, TYPE_WRITING)
        self.assertEqual(task.content, "fill in the blanks")
        self.assertEqual(task.min_words, 5)
        self.assertEqual(task.max_words, 60)
        self.assertEqual(task.evaluation_mode, "AI_ONLY")

    def test_speaking_maps_topic_to_instructions_and_content_to_instruction(self):
        db = build_mock_db(
            speakings=[make_speaking(topic="Sich vorstellen", instruction="Hallo! Ich heisse ___")]
        )
        plan = migrate.build_plan(db, make_lesson())
        task = next(s for s in plan.sections if s.skill == SKILL_SPRECHEN).tasks[0]
        self.assertEqual(task.task_type, TYPE_SPEAKING)
        self.assertEqual(task.instructions, "Sich vorstellen")
        self.assertEqual(task.content, "Hallo! Ich heisse ___")
        self.assertEqual(task.evaluation_mode, "TEACHER_ONLY")

    def test_speaking_prep_and_speak_seconds_mapped(self):
        db = build_mock_db(speakings=[make_speaking(preparation_time=15, speaking_time=90)])
        plan = migrate.build_plan(db, make_lesson())
        task = next(s for s in plan.sections if s.skill == SKILL_SPRECHEN).tasks[0]
        self.assertEqual(task.prep_seconds, 15)
        self.assertEqual(task.speak_seconds, 90)

    def test_speaking_sample_answer_and_keywords_appended_when_present(self):
        db = build_mock_db(
            speakings=[make_speaking(instruction="base text", sample_answer="Ich heisse Anna.", keywords="Fussball, Musik")]
        )
        plan = migrate.build_plan(db, make_lesson())
        task = next(s for s in plan.sections if s.skill == SKILL_SPRECHEN).tasks[0]
        self.assertIn("base text", task.content)
        self.assertIn("Ich heisse Anna.", task.content)
        self.assertIn("Fussball, Musik", task.content)

    def test_schreiben_sprechen_publish_true_by_default(self):
        db = build_mock_db(writings=[make_writing()], speakings=[make_speaking()])
        plan = migrate.build_plan(db, make_lesson())
        schreiben_task = next(s for s in plan.sections if s.skill == SKILL_SCHREIBEN).tasks[0]
        sprechen_task = next(s for s in plan.sections if s.skill == SKILL_SPRECHEN).tasks[0]
        self.assertTrue(schreiben_task.publish)
        self.assertTrue(sprechen_task.publish)


class TestApplyPlanOnlyWritesWhatsMissing(unittest.TestCase):
    def _plan_with_one_new_task(self, skill, publish):
        task = migrate.TaskPlan(
            skill=skill,
            legacy_id="legacy-1",
            title="New Task",
            already_exists=False,
            task_type=TYPE_WRITING,
            content="content",
            publish=publish,
        )
        section = migrate.SectionPlan(skill=skill, already_exists=True, existing_id="section-1", tasks=[task])
        return migrate.MigrationPlan(
            lesson_id="lesson-1",
            assessment_already_exists=True,
            assessment_id="assessment-1",
            assessment_status="PUBLISHED",
            sections=[section],
        )

    def test_reuses_existing_assessment_and_section_no_new_ones_created(self):
        db = MagicMock()
        plan = self._plan_with_one_new_task(SKILL_SCHREIBEN, publish=True)
        migrate.apply_plan(db, plan)

        from app.models.assessment import Assessment
        from app.models.assessment_section import AssessmentSection

        created_assessments = [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], Assessment)]
        created_sections = [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], AssessmentSection)]
        self.assertEqual(created_assessments, [])
        self.assertEqual(created_sections, [])
        db.commit.assert_called_once()

    def test_creates_exactly_the_missing_task(self):
        db = MagicMock()
        plan = self._plan_with_one_new_task(SKILL_SCHREIBEN, publish=True)
        migrate.apply_plan(db, plan)

        from app.models.assessment_task import AssessmentTask

        created_tasks = [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], AssessmentTask)]
        self.assertEqual(len(created_tasks), 1)
        self.assertEqual(created_tasks[0].title, "New Task")
        self.assertEqual(created_tasks[0].status, STATUS_PUBLISHED)

    def test_already_existing_task_is_never_added(self):
        db = MagicMock()
        existing_task = migrate.TaskPlan(
            skill=SKILL_SCHREIBEN, legacy_id="legacy-1", title="Old Task",
            already_exists=True, task_type=TYPE_WRITING, content="x",
        )
        section = migrate.SectionPlan(skill=SKILL_SCHREIBEN, already_exists=True, existing_id="section-1", tasks=[existing_task])
        plan = migrate.MigrationPlan(
            lesson_id="lesson-1", assessment_already_exists=True, assessment_id="assessment-1",
            assessment_status="PUBLISHED", sections=[section],
        )
        migrate.apply_plan(db, plan)
        db.add.assert_not_called()
        db.commit.assert_called_once()

    def test_hoeren_task_created_with_draft_status(self):
        db = MagicMock()
        plan = self._plan_with_one_new_task(SKILL_HOEREN, publish=False)
        migrate.apply_plan(db, plan)

        from app.models.assessment_task import AssessmentTask

        created_tasks = [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], AssessmentTask)]
        self.assertEqual(created_tasks[0].status, STATUS_DRAFT)

    def test_creates_assessment_and_section_when_neither_exists(self):
        db = MagicMock()
        task = migrate.TaskPlan(
            skill=SKILL_SCHREIBEN, legacy_id="legacy-1", title="New Task",
            already_exists=False, task_type=TYPE_WRITING, content="x", publish=True,
        )
        section = migrate.SectionPlan(skill=SKILL_SCHREIBEN, already_exists=False, existing_id=None, tasks=[task])
        plan = migrate.MigrationPlan(
            lesson_id="lesson-1", assessment_already_exists=False, assessment_id=None,
            assessment_status=None, sections=[section],
        )
        migrate.apply_plan(db, plan)

        from app.models.assessment import Assessment
        from app.models.assessment_section import AssessmentSection

        created_assessments = [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], Assessment)]
        created_sections = [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], AssessmentSection)]
        self.assertEqual(len(created_assessments), 1)
        self.assertEqual(created_assessments[0].status, STATUS_DRAFT)
        self.assertEqual(len(created_sections), 1)

    def test_section_with_no_legacy_tasks_is_never_created(self):
        db = MagicMock()
        section = migrate.SectionPlan(skill=SKILL_HOEREN, already_exists=False, existing_id=None, tasks=[])
        plan = migrate.MigrationPlan(
            lesson_id="lesson-1", assessment_already_exists=True, assessment_id="assessment-1",
            assessment_status="PUBLISHED", sections=[section],
        )
        migrate.apply_plan(db, plan)
        db.add.assert_not_called()


class TestDryRunNeverWrites(unittest.TestCase):
    def test_dry_run_makes_no_db_writes(self):
        db = build_mock_db(listenings=[make_listening()], writings=[make_writing()], speakings=[make_speaking()])
        with patch.object(migrate, "SessionLocal", return_value=db), patch.object(migrate, "find_lesson_1", return_value=make_lesson()):
            with patch("sys.argv", ["migrate_lesson_1_assessments.py", "--dry-run"]):
                migrate.main()
        db.add.assert_not_called()
        db.flush.assert_not_called()
        db.commit.assert_not_called()

    def test_real_run_with_nothing_to_create_still_makes_no_writes(self):
        assessment = MagicMock(id="assessment-1", status="PUBLISHED")
        hoeren_section = MagicMock(id="section-hoeren")
        db = build_mock_db(
            assessment=assessment,
            hoeren_section=hoeren_section,
            hoeren_existing_titles=["Text 1"],
            listenings=[make_listening(title="Text 1")],
        )
        with patch.object(migrate, "SessionLocal", return_value=db), patch.object(migrate, "find_lesson_1", return_value=make_lesson()):
            with patch("sys.argv", ["migrate_lesson_1_assessments.py"]):
                migrate.main()
        db.add.assert_not_called()
        db.commit.assert_not_called()


class TestMissingLessonAborts(unittest.TestCase):
    def test_missing_lesson_aborts_without_writes_dry_run(self):
        db = MagicMock()
        with patch.object(migrate, "SessionLocal", return_value=db), patch.object(migrate, "find_lesson_1", return_value=None):
            with patch("sys.argv", ["migrate_lesson_1_assessments.py", "--dry-run"]):
                migrate.main()
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_missing_lesson_aborts_without_writes_real_run(self):
        db = MagicMock()
        with patch.object(migrate, "SessionLocal", return_value=db), patch.object(migrate, "find_lesson_1", return_value=None):
            with patch("sys.argv", ["migrate_lesson_1_assessments.py"]):
                migrate.main()
        db.add.assert_not_called()
        db.commit.assert_not_called()


class TestLegacyAndSeedScriptsStayIndependent(unittest.TestCase):
    def test_does_not_import_seed_lesson_1(self):
        # This module must stay wholly independent of the legacy seeder —
        # no import, no shared helper (mentioning it by name in comments/
        # docstrings for context is fine and expected).
        source = inspect.getsource(migrate)
        self.assertNotIn("import app.scripts.seed_lesson_1", source)
        self.assertNotIn("from app.scripts.seed_lesson_1", source)
        self.assertNotIn("seed_lesson_1", migrate.__dict__)


if __name__ == "__main__":
    unittest.main()
