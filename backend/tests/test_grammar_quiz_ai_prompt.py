"""Regression tests for the new prompt-driven Gemini Grammar Quiz
generator — the "Automatisch erstellen" dialog's optional "Anweisungen
/ Prompt" field. Covers two layers:

1. generate_grammar_quiz_mc_from_prompt (app/services/ai_content/
   generation_service.py) — the Gemini call + strict server-side
   enforcement that every returned question has exactly 4 options and
   exactly 1 marked correct, dropping (never repairing) anything that
   doesn't conform.
2. generate_quiz_from_prompt (app/services/quiz_generation/
   quiz_generation_service.py) — the DB-writing wrapper: GRAMMAR-only
   guard, quiz/lesson ownership check, draft-by-default (unlike the
   deterministic generator's GRAMMAR auto-publish), dedup against
   existing questions, and that the original deterministic generate_quiz
   is never called or touched by this path.

Uses stdlib unittest.IsolatedAsyncioTestCase + mock (no real network
call, no real DB) — call_gemini is patched at the exact import site
each module under test uses it from."""

import json
import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.course import Course
from app.models.quiz import Quiz
from app.models.quiz_option import QuizOption
from app.models.quiz_question import QuizQuestion
from app.services.ai_content.generation_service import generate_grammar_quiz_mc_from_prompt
from app.services.ai_content.gemini_client import AIContentError
from app.services.quiz_generation.quiz_generation_service import (
    QuizGenerationError,
    generate_quiz_from_prompt,
)


def gemini_json(questions: list[dict]) -> str:
    return json.dumps({"questions": questions})


def four_option_question(text: str = "Welcher Artikel passt?", correct_index: int = 0) -> dict:
    return {
        "question": text,
        "options": [
            {"option_text": f"Option {i}", "is_correct": i == correct_index}
            for i in range(4)
        ],
    }


class TestGenerateGrammarQuizMcFromPrompt(unittest.IsolatedAsyncioTestCase):
    async def test_valid_response_returns_all_questions(self):
        questions = [four_option_question(f"Frage {i}") for i in range(5)]
        with patch(
            "app.services.ai_content.generation_service.call_gemini",
            new=AsyncMock(return_value=gemini_json(questions)),
        ):
            result = await generate_grammar_quiz_mc_from_prompt("A1 Alphabet, 5 Fragen", "A1", 5)

        self.assertEqual(len(result), 5)
        for q in result:
            self.assertEqual(len(q.options), 4)
            self.assertEqual(sum(1 for o in q.options if o.is_correct), 1)

    async def test_question_with_wrong_option_count_is_dropped(self):
        questions = [
            four_option_question("Gute Frage"),
            {
                "question": "Schlechte Frage — nur 3 Optionen",
                "options": [{"option_text": f"O{i}", "is_correct": i == 0} for i in range(3)],
            },
        ]
        with patch(
            "app.services.ai_content.generation_service.call_gemini",
            new=AsyncMock(return_value=gemini_json(questions)),
        ):
            result = await generate_grammar_quiz_mc_from_prompt("prompt", "A1", 2)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].question, "Gute Frage")

    async def test_question_with_two_correct_answers_is_dropped(self):
        bad = {
            "question": "Zwei richtige Antworten",
            "options": [{"option_text": f"O{i}", "is_correct": i < 2} for i in range(4)],
        }
        with patch(
            "app.services.ai_content.generation_service.call_gemini",
            new=AsyncMock(return_value=gemini_json([bad])),
        ):
            result = await generate_grammar_quiz_mc_from_prompt("prompt", "A1", 1)

        self.assertEqual(len(result), 0)

    async def test_question_with_zero_correct_answers_is_dropped(self):
        bad = {
            "question": "Keine richtige Antwort",
            "options": [{"option_text": f"O{i}", "is_correct": False} for i in range(4)],
        }
        with patch(
            "app.services.ai_content.generation_service.call_gemini",
            new=AsyncMock(return_value=gemini_json([bad])),
        ):
            result = await generate_grammar_quiz_mc_from_prompt("prompt", "A1", 1)

        self.assertEqual(len(result), 0)

    async def test_malformed_json_raises_ai_content_error(self):
        with patch(
            "app.services.ai_content.generation_service.call_gemini",
            new=AsyncMock(return_value="not json at all"),
        ):
            with self.assertRaises(AIContentError):
                await generate_grammar_quiz_mc_from_prompt("prompt", "A1", 1)


def build_mock_db(
    quiz_type: str = "GRAMMAR",
    existing_question_texts: list[str] | None = None,
    existing_max_order: int = 0,
    lesson_id: uuid.UUID | None = None,
):
    quiz_id = uuid.uuid4()
    lesson_id = lesson_id or uuid.uuid4()
    quiz = Quiz(
        id=quiz_id,
        lesson_id=str(lesson_id),
        quiz_type=quiz_type,
        title="Grammatik Quiz",
        is_published=False,
    )

    db = MagicMock()
    db.get.return_value = quiz

    existing_question_texts = existing_question_texts or []

    def query_side_effect(*args):
        target = args[0]
        q = MagicMock()
        q.filter.return_value = q
        if target is Course.level:
            q.first.return_value = ("A1",)
        elif target is QuizQuestion.question:
            q.all.return_value = [(t,) for t in existing_question_texts]
        else:
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


class TestGenerateQuizFromPrompt(unittest.IsolatedAsyncioTestCase):
    def _patch_ai(self, questions_data: list[dict]):
        from app.schemas.ai_content import AIGrammarQuizPreview

        preview = AIGrammarQuizPreview.model_validate({"questions": questions_data})
        return patch(
            "app.services.quiz_generation.quiz_generation_service.generate_grammar_quiz_mc_from_prompt",
            new=AsyncMock(return_value=preview.questions),
        )

    async def test_creates_mc_questions_as_drafts_not_published(self):
        db, quiz_id, lesson_id = build_mock_db()
        questions = [four_option_question(f"Frage {i}") for i in range(3)]
        with self._patch_ai(questions):
            result = await generate_quiz_from_prompt(db, quiz_id, lesson_id, prompt="A1 Alphabet", count=3)

        self.assertEqual(result.created_count, 3)
        self.assertFalse(result.shortfall)
        created = added_questions(db)
        self.assertEqual(len(created), 3)
        # Unlike the deterministic GRAMMAR path, AI-generated questions
        # are never auto-published — they need admin review first.
        self.assertTrue(all(not q.is_published for q in created))
        self.assertTrue(all(q.question_type == "MULTIPLE_CHOICE" for q in created))
        # The quiz container itself must not be silently flipped to
        # published either.
        self.assertFalse(db.get.return_value.is_published)

    async def test_each_created_question_has_four_options_one_correct(self):
        db, quiz_id, lesson_id = build_mock_db()
        questions = [four_option_question(f"Frage {i}", correct_index=i % 4) for i in range(6)]
        with self._patch_ai(questions):
            await generate_quiz_from_prompt(db, quiz_id, lesson_id, prompt="prompt", count=6)

        groups = questions_with_their_options(db)
        self.assertEqual(len(groups), 6)
        for _question, options in groups:
            self.assertEqual(len(options), 4)
            self.assertEqual(sum(1 for o in options if o.is_correct), 1)

    async def test_non_grammar_quiz_type_is_rejected(self):
        db, quiz_id, lesson_id = build_mock_db(quiz_type="LESSON")
        with self._patch_ai([four_option_question()]):
            with self.assertRaises(QuizGenerationError):
                await generate_quiz_from_prompt(db, quiz_id, lesson_id, prompt="prompt", count=1)

    async def test_missing_quiz_raises(self):
        db, quiz_id, lesson_id = build_mock_db()
        db.get.return_value = None
        with self.assertRaises(QuizGenerationError):
            await generate_quiz_from_prompt(db, quiz_id, lesson_id, prompt="prompt", count=1)

    async def test_quiz_belonging_to_different_lesson_raises(self):
        db, quiz_id, lesson_id = build_mock_db()
        other_lesson_id = uuid.uuid4()
        with self.assertRaises(QuizGenerationError):
            await generate_quiz_from_prompt(db, quiz_id, other_lesson_id, prompt="prompt", count=1)

    async def test_dedup_against_existing_questions(self):
        db, quiz_id, lesson_id = build_mock_db(existing_question_texts=["Frage 0"])
        questions = [four_option_question("Frage 0"), four_option_question("Frage 1")]
        with self._patch_ai(questions):
            result = await generate_quiz_from_prompt(db, quiz_id, lesson_id, prompt="prompt", count=2)

        self.assertEqual(result.created_count, 1)
        created = added_questions(db)
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].question, "Frage 1")

    async def test_shortfall_reported_when_ai_returns_fewer_valid_questions_than_requested(self):
        db, quiz_id, lesson_id = build_mock_db()
        with self._patch_ai([four_option_question("Nur eine")]):
            result = await generate_quiz_from_prompt(db, quiz_id, lesson_id, prompt="prompt", count=5)

        self.assertEqual(result.created_count, 1)
        self.assertEqual(result.requested_count, 5)
        self.assertTrue(result.shortfall)
        self.assertIsNotNone(result.message)


if __name__ == "__main__":
    unittest.main()
