"""Verifies the deterministic (no-AI) Alphabet quiz generator: requested
count is honored exactly when enough unique candidates exist, never
padded/duplicated when it doesn't, every question has exactly 4 options
with exactly 1 correct, generation is A1-only, and it only ever appends
to the target quiz (existing questions untouched, no delete). Uses a
MagicMock Session — same stdlib unittest+mock approach as
test_vocabulary_test_sync.py (no pytest, no real DB)."""

import unittest
import uuid
from unittest.mock import MagicMock

from app.models.course import Course
from app.models.quiz import Quiz
from app.models.quiz_option import QuizOption
from app.models.quiz_question import QuizQuestion
from app.services.quiz_generation.quiz_generation_service import (
    QuizGenerationError,
    generate_quiz,
)


def build_mock_db(
    level: str,
    existing_question_texts: list[str] | None = None,
    existing_max_order: int = 0,
    quiz_type: str = "GRAMMAR",
    quiz_already_published: bool = False,
):
    quiz_id = uuid.uuid4()
    lesson_id = uuid.uuid4()
    quiz = Quiz(
        id=quiz_id,
        lesson_id=str(lesson_id),
        quiz_type=quiz_type,
        title="Grammatik Quiz",
        is_published=quiz_already_published,
    )

    db = MagicMock()
    db.get.return_value = quiz

    existing_question_texts = existing_question_texts or []

    def query_side_effect(*args):
        target = args[0]
        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q

        if target is Course.level:
            q.first.return_value = (level,)
        elif target is QuizQuestion.question:
            q.all.return_value = [(t,) for t in existing_question_texts]
        else:
            # func.max(QuizQuestion.order_index) — the only other query shape.
            q.scalar.return_value = existing_max_order or None
        return q

    db.query.side_effect = query_side_effect
    return db, quiz_id, lesson_id


def added_questions(db: MagicMock) -> list[QuizQuestion]:
    return [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], QuizQuestion)]


def questions_with_their_options(db: MagicMock) -> list[tuple[QuizQuestion, list[QuizOption]]]:
    groups: list[tuple[QuizQuestion, list[QuizOption]]] = []
    for c in db.add.call_args_list:
        obj = c.args[0]
        if isinstance(obj, QuizQuestion):
            groups.append((obj, []))
        elif isinstance(obj, QuizOption):
            groups[-1][1].append(obj)
    return groups


class TestQuizGenerationService(unittest.TestCase):
    def test_alphabet_20_questions(self):
        db, quiz_id, lesson_id = build_mock_db("A1")
        result = generate_quiz(db, quiz_id, lesson_id, topic="alphabet", count=20, seed=1)
        self.assertEqual(result.created_count, 20)
        self.assertEqual(result.requested_count, 20)
        self.assertFalse(result.shortfall)
        self.assertEqual(len(added_questions(db)), 20)

    def test_alphabet_50_questions(self):
        db, quiz_id, lesson_id = build_mock_db("A1")
        result = generate_quiz(db, quiz_id, lesson_id, topic="alphabet", count=50, seed=2)
        self.assertEqual(result.created_count, 50)
        self.assertFalse(result.shortfall)
        self.assertEqual(len(added_questions(db)), 50)

    def test_zero_duplicates_among_generated_questions(self):
        db, quiz_id, lesson_id = build_mock_db("A1")
        generate_quiz(db, quiz_id, lesson_id, topic="alphabet", count=100, seed=3)
        texts = [q.question.strip().lower() for q in added_questions(db)]
        self.assertEqual(len(texts), len(set(texts)))

    def test_each_question_has_four_options_and_exactly_one_correct(self):
        db, quiz_id, lesson_id = build_mock_db("A1")
        generate_quiz(db, quiz_id, lesson_id, topic="alphabet", count=30, seed=4)
        groups = questions_with_their_options(db)
        self.assertEqual(len(groups), 30)
        for _question, options in groups:
            self.assertEqual(len(options), 4)
            self.assertEqual(sum(1 for o in options if o.is_correct), 1)

    def test_a1_only_other_levels_raise(self):
        for level in ("A2", "B1", "B2", "C1"):
            with self.subTest(level=level):
                db, quiz_id, lesson_id = build_mock_db(level)
                with self.assertRaises(QuizGenerationError):
                    generate_quiz(db, quiz_id, lesson_id, topic="alphabet", count=10)

    def test_insufficient_unique_candidates_reports_shortfall_honestly(self):
        # The Alphabet topic has ~400 possible candidates — asking for far
        # more than that must return exactly what's achievable, with a
        # clear shortfall message, never padded/duplicated filler.
        db, quiz_id, lesson_id = build_mock_db("A1")
        result = generate_quiz(db, quiz_id, lesson_id, topic="alphabet", count=10_000, seed=5)
        self.assertLess(result.created_count, 10_000)
        self.assertTrue(result.shortfall)
        self.assertIsNotNone(result.message)
        texts = [q.question.strip().lower() for q in added_questions(db)]
        self.assertEqual(len(texts), len(set(texts)))

    def test_existing_quiz_questions_are_never_touched_or_deleted(self):
        # Append-only, unlike the Wortschatz sync's full-regenerate design.
        db, quiz_id, lesson_id = build_mock_db(
            "A1", existing_question_texts=["Welcher Buchstabe kommt nach a?"], existing_max_order=5
        )
        generate_quiz(db, quiz_id, lesson_id, topic="alphabet", count=10, seed=6)
        # No delete() is ever called on this MagicMock db.
        self.assertFalse(db.query.return_value.delete.called)
        new_questions = added_questions(db)
        self.assertEqual(len(new_questions), 10)
        # Order indexes continue after the existing max, not restarting at 1.
        self.assertTrue(all(q.order_index > 5 for q in new_questions))
        # The already-seeded duplicate ("nach a") is never regenerated.
        self.assertNotIn("welcher buchstabe kommt nach a?", [q.question.strip().lower() for q in new_questions])

    def test_regenerating_same_quiz_seeds_dedup_from_existing_questions(self):
        existing = ["Welcher Buchstabe kommt nach A?", "Welcher Buchstabe kommt nach B?"]
        db, quiz_id, lesson_id = build_mock_db("A1", existing_question_texts=existing)
        generate_quiz(db, quiz_id, lesson_id, topic="alphabet", count=25, seed=7)
        new_texts = {q.question.strip().lower() for q in added_questions(db)}
        self.assertNotIn("welcher buchstabe kommt nach a?", new_texts)
        self.assertNotIn("welcher buchstabe kommt nach b?", new_texts)

    def test_unknown_topic_raises_clear_error(self):
        db, quiz_id, lesson_id = build_mock_db("A1")
        with self.assertRaises(QuizGenerationError):
            generate_quiz(db, quiz_id, lesson_id, topic="not-a-real-topic", count=5)


class TestGrammarQuizAutoPublish(unittest.TestCase):
    """A generated GRAMMAR quiz's questions (and the quiz container
    itself) are published immediately — the two-gate "draft by default"
    design was the actual root cause of "questions exist but the quiz
    doesn't fully show". Scoped to GRAMMAR only; other quiz types keep
    the original draft-first behavior."""

    def test_5_20_50_questions_all_published_immediately(self):
        for count in (5, 20, 50):
            with self.subTest(count=count):
                db, quiz_id, lesson_id = build_mock_db("A1")
                result = generate_quiz(db, quiz_id, lesson_id, topic="alphabet", count=count, seed=count)
                self.assertEqual(result.created_count, count)
                questions = added_questions(db)
                self.assertEqual(len(questions), count)
                self.assertTrue(all(q.is_published for q in questions))

    def test_quiz_container_becomes_published_after_generation(self):
        db, quiz_id, lesson_id = build_mock_db("A1", quiz_already_published=False)
        quiz = db.get.return_value
        self.assertFalse(quiz.is_published)
        generate_quiz(db, quiz_id, lesson_id, topic="alphabet", count=10, seed=1)
        self.assertTrue(quiz.is_published)

    def test_already_published_quiz_stays_published_idempotent(self):
        db, quiz_id, lesson_id = build_mock_db("A1", quiz_already_published=True)
        generate_quiz(db, quiz_id, lesson_id, topic="alphabet", count=10, seed=1)
        self.assertTrue(db.get.return_value.is_published)

    def test_lesson_type_quiz_keeps_draft_default_out_of_scope(self):
        # Only GRAMMAR gets the auto-publish behavior — LESSON-type
        # generation (should it ever be used) is untouched, per the
        # explicit "only change Grammar Quiz" scope of this fix.
        db, quiz_id, lesson_id = build_mock_db("A1", quiz_type="LESSON")
        generate_quiz(db, quiz_id, lesson_id, topic="alphabet", count=10, seed=1)
        questions = added_questions(db)
        self.assertEqual(len(questions), 10)
        self.assertTrue(all(not q.is_published for q in questions))
        self.assertFalse(db.get.return_value.is_published)


if __name__ == "__main__":
    unittest.main()
