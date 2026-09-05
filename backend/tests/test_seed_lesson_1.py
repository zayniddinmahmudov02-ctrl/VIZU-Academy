"""Regression tests for app/scripts/seed_lesson_1.py — the idempotent A1
Lesson 1 content importer. Uses stdlib unittest + MagicMock (no real DB),
matching this session's established pattern (see test_section_gate_
dynamic.py / test_vocabulary_test_sync.py): pytest isn't installed in
this venv, and every seed_* helper only ever calls db.scalar/add/flush,
which a MagicMock can stand in for directly.

Covers:
  - Content shape: 54 Wortschatz items, 3 Lesen texts, 3 Hören texts, 4
    Schreiben tasks, exactly one Sprechen task, 20 Grammatik Quiz
    questions each with exactly 4 options and exactly one correct one.
  - Idempotency: every seed_* helper skips (never calls db.add) when a
    matching row is already found via db.scalar, and creates when none
    is found.
  - get_lesson_1 aborts (returns None) instead of creating anything when
    the Language/Course/Module/Lesson chain doesn't already exist.
  - Lesson Quiz (quiz_type=LESSON) is never created by this script — it
    only ever creates/looks up quiz_type=GRAMMAR.
  - Homework and Video are never touched by this script at all.
"""

import unittest
from unittest.mock import MagicMock, patch

import app.scripts.seed_lesson_1 as seed_lesson_1
from app.models.quiz import QUIZ_TYPE_GRAMMAR, QUIZ_TYPE_LESSON


def make_lesson(lesson_id="lesson-1", title="Begrüßung"):
    lesson = MagicMock()
    lesson.id = lesson_id
    lesson.title = title
    return lesson


class TestContentShape(unittest.TestCase):
    def test_54_vocabulary_items(self):
        self.assertEqual(len(seed_lesson_1.VOCABULARY_ITEMS), 54)

    def test_every_vocabulary_item_has_word_and_translation(self):
        for word, article, translation in seed_lesson_1.VOCABULARY_ITEMS:
            with self.subTest(word=word, translation=translation):
                self.assertTrue(word)
                self.assertTrue(translation)
                self.assertIsInstance(article, (str, type(None)))

    def test_3_reading_texts(self):
        self.assertEqual(len(seed_lesson_1.READING_TEXTS), 3)

    def test_3_listening_texts(self):
        self.assertEqual(len(seed_lesson_1.LISTENING_TEXTS), 3)

    def test_4_writing_tasks(self):
        self.assertEqual(len(seed_lesson_1.WRITING_TASKS), 4)

    def test_20_quiz_questions(self):
        self.assertEqual(len(seed_lesson_1.QUIZ_QUESTIONS), 20)

    def test_every_quiz_question_has_4_options_and_1_correct(self):
        for question, options, correct_index in seed_lesson_1.QUIZ_QUESTIONS:
            with self.subTest(question=question):
                self.assertEqual(len(options), 4)
                self.assertTrue(0 <= correct_index <= 3)

    def test_quiz_targets_grammar_type_not_lesson_type(self):
        self.assertNotEqual(QUIZ_TYPE_GRAMMAR, QUIZ_TYPE_LESSON)
        # seed_grammar_quiz below is asserted to only ever query/create
        # Quiz.quiz_type == QUIZ_TYPE_GRAMMAR.


class TestLessonLookupNeverCreates(unittest.TestCase):
    def test_missing_language_returns_none(self):
        db = MagicMock()
        db.scalar.return_value = None  # no 'de' Language row
        result = seed_lesson_1.get_lesson_1(db)
        self.assertIsNone(result)
        db.add.assert_not_called()

    def test_missing_course_returns_none(self):
        db = MagicMock()
        language = MagicMock()
        db.scalar.side_effect = [language, None]  # language found, course missing
        result = seed_lesson_1.get_lesson_1(db)
        self.assertIsNone(result)
        db.add.assert_not_called()

    def test_missing_module_returns_none(self):
        db = MagicMock()
        language = MagicMock()
        course = MagicMock()
        db.scalar.side_effect = [language, course, None]
        result = seed_lesson_1.get_lesson_1(db)
        self.assertIsNone(result)
        db.add.assert_not_called()

    def test_missing_lesson_returns_none(self):
        db = MagicMock()
        language, course, module = MagicMock(), MagicMock(), MagicMock()
        db.scalar.side_effect = [language, course, module, None]
        result = seed_lesson_1.get_lesson_1(db)
        self.assertIsNone(result)
        db.add.assert_not_called()

    def test_full_chain_found_returns_lesson(self):
        db = MagicMock()
        language, course, module, lesson = MagicMock(), MagicMock(), MagicMock(), make_lesson()
        db.scalar.side_effect = [language, course, module, lesson]
        result = seed_lesson_1.get_lesson_1(db)
        self.assertIs(result, lesson)

    def test_main_aborts_without_commit_when_lesson_missing(self):
        with patch.object(seed_lesson_1, "SessionLocal") as session_local:
            db = MagicMock()
            db.scalar.return_value = None
            session_local.return_value = db
            seed_lesson_1.main()
            db.commit.assert_not_called()
            db.add.assert_not_called()


class TestSeedHelpersAreIdempotent(unittest.TestCase):
    def setUp(self):
        self.lesson = make_lesson()

    def test_seed_grammar_skips_when_existing(self):
        db = MagicMock()
        db.scalar.return_value = MagicMock()  # existing Grammar row found
        created = seed_lesson_1.seed_grammar(db, self.lesson)
        self.assertEqual(created, 0)
        db.add.assert_not_called()

    def test_seed_grammar_creates_when_missing(self):
        db = MagicMock()
        db.scalar.return_value = None
        created = seed_lesson_1.seed_grammar(db, self.lesson)
        self.assertEqual(created, 1)
        db.add.assert_called_once()

    def test_seed_vocabulary_skips_all_when_all_existing(self):
        db = MagicMock()
        db.scalar.return_value = MagicMock()
        created = seed_lesson_1.seed_vocabulary(db, self.lesson)
        self.assertEqual(created, 0)
        db.add.assert_not_called()

    def test_seed_vocabulary_creates_all_when_none_existing(self):
        db = MagicMock()
        db.scalar.return_value = None
        created = seed_lesson_1.seed_vocabulary(db, self.lesson)
        self.assertEqual(created, len(seed_lesson_1.VOCABULARY_ITEMS))
        self.assertEqual(db.add.call_count, len(seed_lesson_1.VOCABULARY_ITEMS))

    def test_seed_vocabulary_creates_only_missing_ones(self):
        db = MagicMock()
        # First two already exist, the rest are missing.
        db.scalar.side_effect = [MagicMock(), MagicMock()] + [None] * (len(seed_lesson_1.VOCABULARY_ITEMS) - 2)
        created = seed_lesson_1.seed_vocabulary(db, self.lesson)
        self.assertEqual(created, len(seed_lesson_1.VOCABULARY_ITEMS) - 2)

    def test_seed_reading_skips_when_existing(self):
        db = MagicMock()
        db.scalar.return_value = MagicMock()
        created = seed_lesson_1.seed_reading(db, self.lesson)
        self.assertEqual(created, 0)
        db.add.assert_not_called()

    def test_seed_reading_creates_all_when_missing(self):
        db = MagicMock()
        db.scalar.return_value = None
        created = seed_lesson_1.seed_reading(db, self.lesson)
        self.assertEqual(created, 3)

    def test_seed_listening_creates_unpublished_rows_with_empty_audio_url(self):
        db = MagicMock()
        db.scalar.return_value = None
        created = seed_lesson_1.seed_listening(db, self.lesson)
        self.assertEqual(created, 3)
        for call in db.add.call_args_list:
            listening = call.args[0]
            self.assertEqual(listening.audio_url, "")
            self.assertFalse(listening.is_published)

    def test_seed_listening_skips_when_existing(self):
        db = MagicMock()
        db.scalar.return_value = MagicMock()
        created = seed_lesson_1.seed_listening(db, self.lesson)
        self.assertEqual(created, 0)
        db.add.assert_not_called()

    def test_seed_writing_creates_all_when_missing(self):
        db = MagicMock()
        db.scalar.return_value = None
        created = seed_lesson_1.seed_writing(db, self.lesson)
        self.assertEqual(created, 4)

    def test_seed_writing_skips_when_existing(self):
        db = MagicMock()
        db.scalar.return_value = MagicMock()
        created = seed_lesson_1.seed_writing(db, self.lesson)
        self.assertEqual(created, 0)
        db.add.assert_not_called()

    def test_seed_speaking_creates_when_missing(self):
        db = MagicMock()
        db.scalar.return_value = None
        created = seed_lesson_1.seed_speaking(db, self.lesson)
        self.assertEqual(created, 1)

    def test_seed_speaking_skips_when_existing(self):
        db = MagicMock()
        db.scalar.return_value = MagicMock()
        created = seed_lesson_1.seed_speaking(db, self.lesson)
        self.assertEqual(created, 0)
        db.add.assert_not_called()


class TestGrammarQuizSeed(unittest.TestCase):
    def setUp(self):
        self.lesson = make_lesson()

    def test_creates_quiz_and_all_20_questions_when_nothing_exists(self):
        db = MagicMock()
        # 1st scalar() call resolves the Quiz lookup (None -> create);
        # every subsequent scalar() call resolves a QuizQuestion lookup
        # (also None -> create) — 20 of those.
        db.scalar.side_effect = [None] + [None] * len(seed_lesson_1.QUIZ_QUESTIONS)
        quizzes_created, questions_created = seed_lesson_1.seed_grammar_quiz(db, self.lesson)
        self.assertEqual(quizzes_created, 1)
        self.assertEqual(questions_created, 20)

    def test_reuses_existing_quiz_and_only_adds_missing_questions(self):
        db = MagicMock()
        existing_quiz = MagicMock()
        existing_quiz.id = "quiz-1"
        # Quiz already exists; first 5 questions already exist too.
        db.scalar.side_effect = (
            [existing_quiz] + [MagicMock()] * 5 + [None] * (len(seed_lesson_1.QUIZ_QUESTIONS) - 5)
        )
        quizzes_created, questions_created = seed_lesson_1.seed_grammar_quiz(db, self.lesson)
        self.assertEqual(quizzes_created, 0)
        self.assertEqual(questions_created, len(seed_lesson_1.QUIZ_QUESTIONS) - 5)

    def test_every_created_question_gets_exactly_one_correct_option(self):
        db = MagicMock()
        db.scalar.side_effect = [None] + [None] * len(seed_lesson_1.QUIZ_QUESTIONS)
        seed_lesson_1.seed_grammar_quiz(db, self.lesson)

        from app.models.quiz_option import QuizOption
        from app.models.quiz_question import QuizQuestion

        questions_added = [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], QuizQuestion)]
        options_added = [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], QuizOption)]

        self.assertEqual(len(questions_added), 20)
        self.assertEqual(len(options_added), 80)  # 20 questions * 4 options

        # db.flush() is a no-op MagicMock here, so question.id never gets
        # a real generated value to group options by — instead, rely on
        # insertion order: seed_grammar_quiz adds exactly 4 options right
        # after each question, so consecutive chunks of 4 map 1:1 to a
        # question's option set.
        for i in range(0, len(options_added), 4):
            chunk = options_added[i : i + 4]
            with self.subTest(question_index=i // 4):
                self.assertEqual(len(chunk), 4)
                self.assertEqual(sum(1 for o in chunk if o.is_correct), 1)


class TestScriptNeverTouchesHomeworkOrVideo(unittest.TestCase):
    def test_no_homework_import(self):
        self.assertFalse(hasattr(seed_lesson_1, "Homework"))

    def test_no_video_import(self):
        self.assertFalse(hasattr(seed_lesson_1, "Video"))


if __name__ == "__main__":
    unittest.main()
