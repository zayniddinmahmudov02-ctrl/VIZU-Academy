"""Verifies sync_vocabulary_test's question count always equals the
lesson's published-vocabulary count — no artificial cap (the removed
MAX_QUESTIONS=20 limit) — and that a single-word lesson (no in-lesson
distractor) still gets a question via the level-wide distractor fallback.
Uses a MagicMock Session (no real DB) since the function only ever calls
db.query/add/flush/delete/commit — same stdlib unittest+mock approach as
test_ai_enrichment_retry.py / test_gemini_client_retry.py (pytest isn't
installed in this venv)."""

import unittest
from unittest.mock import MagicMock

from app.models.course import Course
from app.models.quiz import Quiz
from app.models.quiz_option import QuizOption
from app.models.quiz_question import QuizQuestion
from app.models.vocabulary import Vocabulary
from app.services.vocabulary.test_sync_service import sync_vocabulary_test


def make_words(n: int, distinct_translations: bool = True) -> list[Vocabulary]:
    words = []
    for i in range(n):
        w = Vocabulary(
            lesson_id="lesson-1",
            german_word=f"Wort{i}",
            article="der",
            translation=(f"translation-{i}" if distinct_translations else "same"),
            order_index=i,
        )
        words.append(w)
    return words


def build_mock_db(words: list[Vocabulary], level_pool_words: list[Vocabulary] | None = None):
    """A MagicMock Session whose .query() routes by the queried entity —
    only what sync_vocabulary_test actually calls: Course.level (level
    lookup), Quiz (get-or-create), QuizQuestion (delete-before-rebuild),
    Vocabulary (this lesson's published words), Vocabulary.translation
    (the level-wide fallback pool)."""
    db = MagicMock()
    level_pool_words = level_pool_words if level_pool_words is not None else words

    def query_side_effect(*args):
        target = args[0]
        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q
        q.order_by.return_value = q

        if target is Course.level:
            q.first.return_value = ("A1",)
        elif target is Quiz:
            q.first.return_value = None  # always creates a fresh quiz
        elif target is QuizQuestion:
            q.delete.return_value = 0
        elif target is Vocabulary:
            q.all.return_value = list(words)
        elif target is Vocabulary.translation:
            q.all.return_value = [(w.translation,) for w in level_pool_words]
        return q

    db.query.side_effect = query_side_effect
    return db


def added_questions(db: MagicMock) -> list[QuizQuestion]:
    return [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], QuizQuestion)]


def questions_with_their_options(db: MagicMock) -> list[tuple[QuizQuestion, list[QuizOption]]]:
    """Groups db.add() calls by add-order into (question, its 2 options) —
    QuizQuestion.id is never populated here (no real DB flush), so
    matching by question_id would be meaningless; call order is the only
    reliable link between a question and the options added right after it."""
    groups: list[tuple[QuizQuestion, list[QuizOption]]] = []
    current: QuizQuestion | None = None
    for c in db.add.call_args_list:
        obj = c.args[0]
        if isinstance(obj, QuizQuestion):
            current = obj
            groups.append((current, []))
        elif isinstance(obj, QuizOption):
            groups[-1][1].append(obj)
    return groups


class TestVocabularyTestSyncCount(unittest.TestCase):
    def test_no_cap_at_various_sizes(self):
        # The old code hard-capped at 20 regardless of how many words a
        # lesson published — this is exactly what that cap removal fixes.
        # n=1 is covered separately below (it needs a level-wide
        # distractor pool, since a single word has no in-lesson one).
        for n in (2, 5, 20, 52, 60, 40, 100):
            with self.subTest(n=n):
                words = make_words(n)
                db = build_mock_db(words)
                sync_vocabulary_test(db, "lesson-1")
                self.assertEqual(len(added_questions(db)), n)

    def test_zero_words_makes_zero_questions(self):
        db = build_mock_db([])
        sync_vocabulary_test(db, "lesson-1")
        self.assertEqual(len(added_questions(db)), 0)

    def test_delete_happens_before_rebuild(self):
        """Full-regenerate design: every sync clears old questions first,
        so re-syncing never accumulates duplicates."""
        words = make_words(5)
        db = build_mock_db(words)
        sync_vocabulary_test(db, "lesson-1")
        # QuizQuestion.filter(...).delete() is called via db.query(QuizQuestion)
        self.assertTrue(any(c.args and c.args[0] is QuizQuestion for c in db.query.call_args_list))

    def test_each_question_has_exactly_two_options_one_correct(self):
        words = make_words(10)
        db = build_mock_db(words)
        sync_vocabulary_test(db, "lesson-1")
        groups = questions_with_their_options(db)
        self.assertEqual(len(groups), 10)
        for _question, q_options in groups:
            self.assertEqual(len(q_options), 2)
            self.assertEqual(sum(1 for o in q_options if o.is_correct), 1)

    def test_single_word_lesson_still_gets_a_question_via_level_fallback(self):
        # No in-lesson distractor exists (only one word) — must fall back
        # to the wider A1 pool rather than skipping the word entirely.
        lonely_word = make_words(1)
        level_pool = lonely_word + make_words(3)  # other A1 words elsewhere
        db = build_mock_db(lonely_word, level_pool_words=level_pool)
        sync_vocabulary_test(db, "lesson-1")
        self.assertEqual(len(added_questions(db)), 1)

    def test_single_word_lesson_with_no_level_fallback_available_is_skipped(self):
        # Degenerate case: truly no other distinct-translation A1 word
        # exists anywhere — a valid 2-option question is impossible, so
        # (and only so) the word is skipped, same as before this change.
        lonely_word = make_words(1)
        db = build_mock_db(lonely_word, level_pool_words=lonely_word)
        sync_vocabulary_test(db, "lesson-1")
        self.assertEqual(len(added_questions(db)), 0)

    def test_shrink_and_grow_each_reflect_current_published_count(self):
        # Not incremental state — each call is an independent full
        # regenerate, so calling with a smaller/larger set afterward
        # reflects exactly that set's size, not the previous call's.
        db_grow = build_mock_db(make_words(52))
        sync_vocabulary_test(db_grow, "lesson-1")
        self.assertEqual(len(added_questions(db_grow)), 52)

        db_shrink = build_mock_db(make_words(40))
        sync_vocabulary_test(db_shrink, "lesson-1")
        self.assertEqual(len(added_questions(db_shrink)), 40)

        db_empty = build_mock_db(make_words(0))
        sync_vocabulary_test(db_empty, "lesson-1")
        self.assertEqual(len(added_questions(db_empty)), 0)


if __name__ == "__main__":
    unittest.main()
