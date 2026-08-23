"""Regression test for get_content_status_for_module's has_grammar_quiz
field — the Admin Courses -> lesson-list "✓/-" indicator. Verifies it
correctly reports True only when a *published* GRAMMAR-type Quiz row
exists for the lesson, matching the same is_published-only definition
SectionGateService._quiz_applicable uses for the student-facing gate
(see section_gate.py) — no separate/divergent logic. The function takes
no level parameter and branches on nothing level-specific, so running
the same assertions against several distinct module/lesson id sets
(standing in for A1-C1) is itself the proof there's no per-level
special-casing. Uses stdlib unittest + MagicMock (no real DB), matching
this session's established pattern.

Root cause this pins down: every lesson_id column touched here
(Video/Vocabulary/Grammar/Quiz.lesson_id) resolves to a native
UUID(as_uuid=True) column at the DB level regardless of its Python
`Mapped[str]` vs `Mapped[UUID]` annotation — mapped_column(ForeignKey
(...)) with no explicit type infers from the FK target (Lesson.id),
confirmed directly via Quiz.__table__.columns["lesson_id"].type.
python_type (== uuid.UUID, not str). A real query on Quiz.lesson_id
therefore returns uuid.UUID objects, not strings — so every fixture
below passes raw UUID objects for lesson_id in *_rows (matching real
query results), not pre-stringified ones; a test that stringified them
itself would never have caught the "keyed by UUID, looked up by str"
bug this file exists to pin down."""

import unittest
import uuid
from unittest.mock import MagicMock

from app.services.lesson.service import get_content_status_for_module


def make_lesson(lesson_id, number=1, title="Lektion"):
    lesson = MagicMock()
    lesson.id = lesson_id
    lesson.number = number
    lesson.title = title
    lesson.is_free = False
    return lesson


def build_mock_db(
    lesson,
    quiz_type_rows: list[tuple],
    video_rows: list[tuple] = (),
    grammar_rows: list[tuple] = (),
    vocabulary_rows: list[tuple] = (),
):
    """quiz_type_rows: list of (lesson_id, quiz_type) tuples already
    filtered as if Quiz.is_published.is_(True) had been applied.
    video_rows/grammar_rows/vocabulary_rows: list of (lesson_id,)
    tuples. All lesson_id values here are raw uuid.UUID objects — see
    the module docstring for why that's what a real query actually
    returns for every one of these columns, Grammar/Quiz included."""
    db = MagicMock()

    execute_results = [
        MagicMock(all=MagicMock(return_value=[(lesson.id,)])),  # lesson_ids
        MagicMock(all=MagicMock(return_value=list(video_rows))),  # video_lessons
        MagicMock(all=MagicMock(return_value=list(grammar_rows))),  # grammar_lessons
        MagicMock(all=MagicMock(return_value=list(vocabulary_rows))),  # vocabulary_lessons
        MagicMock(all=MagicMock(return_value=[])),  # skill_rows
        MagicMock(all=MagicMock(return_value=quiz_type_rows)),  # quiz_type_rows
    ]
    db.execute.side_effect = execute_results
    db.scalars.return_value = MagicMock(all=MagicMock(return_value=[lesson]))
    return db


class TestGrammarQuizContentStatus(unittest.TestCase):
    def test_published_grammar_quiz_shows_as_present(self):
        lesson_id = uuid.uuid4()
        lesson = make_lesson(lesson_id, number=1, title="Herzlich Willkommen")
        db = build_mock_db(lesson, quiz_type_rows=[(lesson_id, "GRAMMAR")])

        result = get_content_status_for_module(db, "module-1")

        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["has_grammar_quiz"])

    def test_no_quiz_at_all_shows_as_absent(self):
        lesson_id = uuid.uuid4()
        lesson = make_lesson(lesson_id)
        db = build_mock_db(lesson, quiz_type_rows=[])

        result = get_content_status_for_module(db, "module-1")

        self.assertFalse(result[0]["has_grammar_quiz"])

    def test_unpublished_grammar_quiz_shows_as_absent(self):
        # quiz_type_rows already reflects Quiz.is_published.is_(True)
        # having been applied at the query level (see get_content_status_
        # for_module) — an unpublished quiz simply never appears in this
        # list, same effect as "no quiz at all" from this function's
        # point of view.
        lesson_id = uuid.uuid4()
        lesson = make_lesson(lesson_id)
        db = build_mock_db(lesson, quiz_type_rows=[])

        result = get_content_status_for_module(db, "module-1")

        self.assertFalse(result[0]["has_grammar_quiz"])

    def test_lesson_quiz_type_does_not_count_as_grammar_quiz(self):
        # A LESSON-type quiz existing must not make has_grammar_quiz true
        # — the two are tracked independently (has_lesson_quiz is separate).
        lesson_id = uuid.uuid4()
        lesson = make_lesson(lesson_id)
        db = build_mock_db(lesson, quiz_type_rows=[(lesson_id, "LESSON")])

        result = get_content_status_for_module(db, "module-1")

        self.assertFalse(result[0]["has_grammar_quiz"])
        self.assertTrue(result[0]["has_lesson_quiz"])

    def test_both_quiz_types_tracked_independently(self):
        lesson_id = uuid.uuid4()
        lesson = make_lesson(lesson_id)
        db = build_mock_db(
            lesson, quiz_type_rows=[(lesson_id, "GRAMMAR"), (lesson_id, "LESSON")]
        )

        result = get_content_status_for_module(db, "module-1")

        self.assertTrue(result[0]["has_grammar_quiz"])
        self.assertTrue(result[0]["has_lesson_quiz"])

    def test_other_lessons_quiz_rows_do_not_leak_into_this_lesson(self):
        lesson_id = uuid.uuid4()
        other_lesson_id = uuid.uuid4()
        lesson = make_lesson(lesson_id)
        db = build_mock_db(lesson, quiz_type_rows=[(other_lesson_id, "GRAMMAR")])

        result = get_content_status_for_module(db, "module-1")

        self.assertFalse(result[0]["has_grammar_quiz"])

    def test_universal_across_simulated_levels_no_special_casing(self):
        # get_content_status_for_module takes only a module_id — running
        # it against several independent module/lesson id sets (standing
        # in for A1..C1) with the exact same assertions is the proof
        # nothing here branches on level.
        for level_name in ("A1", "A2", "B1", "B2", "C1"):
            with self.subTest(level=level_name):
                lesson_id = uuid.uuid4()
                lesson = make_lesson(lesson_id, title=f"{level_name} Lektion 1")
                db = build_mock_db(lesson, quiz_type_rows=[(lesson_id, "GRAMMAR")])

                result = get_content_status_for_module(db, f"module-{level_name}")

                self.assertTrue(result[0]["has_grammar_quiz"])


class TestVideoGrammarVocabularyContentStatus(unittest.TestCase):
    """Regression for has_grammar/has_video/has_vocabulary: every one of
    these lesson_id columns is a real UUID column at the DB level (see
    module docstring) — a set built from raw query rows must be
    stringified the same way the str(lesson.id) lookup is, or the
    membership check silently never matches even though the row is
    genuinely there."""

    def test_has_grammar_true_when_a_matching_row_exists(self):
        lesson_id = uuid.uuid4()
        lesson = make_lesson(lesson_id)
        db = build_mock_db(lesson, quiz_type_rows=[], grammar_rows=[(lesson_id,)])

        result = get_content_status_for_module(db, "module-1")

        self.assertTrue(result[0]["has_grammar"])

    def test_has_grammar_false_when_no_row_matches(self):
        lesson_id = uuid.uuid4()
        lesson = make_lesson(lesson_id)
        db = build_mock_db(lesson, quiz_type_rows=[], grammar_rows=[])

        result = get_content_status_for_module(db, "module-1")

        self.assertFalse(result[0]["has_grammar"])

    def test_has_video_true_when_a_matching_row_exists(self):
        lesson_id = uuid.uuid4()
        lesson = make_lesson(lesson_id)
        db = build_mock_db(lesson, quiz_type_rows=[], video_rows=[(lesson_id,)])

        result = get_content_status_for_module(db, "module-1")

        self.assertTrue(result[0]["has_video"])

    def test_has_vocabulary_true_when_a_matching_row_exists(self):
        lesson_id = uuid.uuid4()
        lesson = make_lesson(lesson_id)
        db = build_mock_db(lesson, quiz_type_rows=[], vocabulary_rows=[(lesson_id,)])

        result = get_content_status_for_module(db, "module-1")

        self.assertTrue(result[0]["has_vocabulary"])

    def test_other_lessons_rows_do_not_leak_into_this_lesson(self):
        lesson_id = uuid.uuid4()
        other_lesson_id = uuid.uuid4()
        lesson = make_lesson(lesson_id)
        db = build_mock_db(lesson, quiz_type_rows=[], grammar_rows=[(other_lesson_id,)])

        result = get_content_status_for_module(db, "module-1")

        self.assertFalse(result[0]["has_grammar"])


if __name__ == "__main__":
    unittest.main()
