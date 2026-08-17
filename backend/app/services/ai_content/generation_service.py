"""Prompt templates + response validation for each of the five AI
content-generation endpoints (Feature 3). Every function here only ever
returns a preview object — nothing in this module touches the database.
Turning a preview into real content is entirely the caller's job, via
the same create endpoints a human admin would use by hand (see
ai_content_router.py's docstring)."""

from pydantic import ValidationError

from app.schemas.ai_content import (
    AIGrammarQuizPreview,
    AIHoerenPreview,
    AILesenPreview,
    AISchreibenPreview,
    AISprechenPreview,
)

from .gemini_client import AIContentError, call_gemini, extract_json_object

VALID_QUESTION_TYPES = {
    "MULTIPLE_CHOICE",
    "TRUE_FALSE",
    "CLOZE_TEXT",
    "SENTENCE_COMPLETION",
    "SENTENCE_ORDERING",
    "ERROR_FINDING",
    "MATCHING",
}


async def generate_grammar_quiz(source_text: str, level: str, count: int) -> AIGrammarQuizPreview:
    prompt = f"""You are a German-language curriculum assistant creating a Grammatik Quiz for level {level} students, based on this source text/instructions:

{source_text}

Generate exactly {count} quiz questions, using a healthy mix of these question_type values: MULTIPLE_CHOICE, TRUE_FALSE, CLOZE_TEXT, SENTENCE_COMPLETION, ERROR_FINDING, MATCHING. Every question MUST have an explicit, unambiguous correct answer.

For MULTIPLE_CHOICE / TRUE_FALSE / ERROR_FINDING: provide 2-4 "options", each with option_text and is_correct (exactly one true for MULTIPLE_CHOICE/TRUE_FALSE).
For CLOZE_TEXT / SENTENCE_COMPLETION: provide "correct_text_answer" (a short free-text answer), options can be empty.
For MATCHING: provide 3-5 "options", each with option_text (the German term) and match_value (its correct pairing/translation) — is_correct is not used for MATCHING.

Respond with ONLY a JSON object (no markdown, no prose), exactly this shape:
{{"questions": [{{"question": "...", "question_type": "...", "points": 1, "options": [{{"option_text": "...", "is_correct": true, "match_value": null}}], "correct_text_answer": null}}]}}"""

    text = await call_gemini(prompt)
    data = extract_json_object(text)

    for q in data.get("questions", []):
        qtype = str(q.get("question_type") or "MULTIPLE_CHOICE").upper()
        q["question_type"] = qtype if qtype in VALID_QUESTION_TYPES else "MULTIPLE_CHOICE"
        q["options"] = q.get("options") or []

    try:
        return AIGrammarQuizPreview.model_validate(data)
    except ValidationError as exc:
        raise AIContentError(f"Gemini returned an unexpected shape: {exc}") from exc


async def generate_lesen(source_text: str, level: str, count: int) -> AILesenPreview:
    prompt = f"""You are a German-language curriculum assistant creating a Lesen (reading comprehension) exercise for level {level} students, based on this topic/instructions:

{source_text}

Write one German reading text appropriate for level {level} (a few short paragraphs), then generate exactly {count} multiple-choice comprehension questions about it in German. Each question needs 3-4 options with exactly ONE marked is_correct: true — never an open/free-text answer.

Respond with ONLY a JSON object (no markdown, no prose), exactly this shape:
{{"reading_text": "...", "questions": [{{"prompt": "...", "options": [{{"option_text": "...", "is_correct": true}}]}}]}}"""

    text = await call_gemini(prompt)
    data = extract_json_object(text)

    try:
        return AILesenPreview.model_validate(data)
    except ValidationError as exc:
        raise AIContentError(f"Gemini returned an unexpected shape: {exc}") from exc


async def generate_hoeren(source_text: str, level: str, count: int) -> AIHoerenPreview:
    prompt = f"""You are a German-language curriculum assistant creating Hören (listening comprehension) questions for level {level} students. The audio track itself already exists and is described/transcribed below — you are NOT generating audio, only comprehension questions about it:

{source_text}

Generate exactly {count} multiple-choice comprehension questions in German. Each question needs 3-4 options with exactly ONE marked is_correct: true — never an open/free-text answer.

Respond with ONLY a JSON object (no markdown, no prose), exactly this shape:
{{"questions": [{{"prompt": "...", "options": [{{"option_text": "...", "is_correct": true}}]}}]}}"""

    text = await call_gemini(prompt)
    data = extract_json_object(text)

    try:
        return AIHoerenPreview.model_validate(data)
    except ValidationError as exc:
        raise AIContentError(f"Gemini returned an unexpected shape: {exc}") from exc


async def generate_schreiben(source_text: str, level: str) -> AISchreibenPreview:
    prompt = f"""You are a German-language curriculum assistant creating a Schreiben (writing) task for level {level} students, based on this topic/instructions:

{source_text}

Write: a task_content (the writing prompt/scenario the student must respond to, in German), requirements (word count / format expectations, in German), and 3-5 rubric_criteria for evaluating the response (each with a short name like "Wortschatz", "Grammatik", "Aufgabenbewältigung", "Aufbau" and a max_score out of 5).

Respond with ONLY a JSON object (no markdown, no prose), exactly this shape:
{{"task_content": "...", "requirements": "...", "rubric_criteria": [{{"name": "...", "max_score": 5}}]}}"""

    text = await call_gemini(prompt)
    data = extract_json_object(text)

    try:
        return AISchreibenPreview.model_validate(data)
    except ValidationError as exc:
        raise AIContentError(f"Gemini returned an unexpected shape: {exc}") from exc


async def generate_sprechen(source_text: str, level: str) -> AISprechenPreview:
    prompt = f"""You are a German-language curriculum assistant creating a Sprechen (speaking) task for level {level} students, based on this topic/instructions:

{source_text}

Write: a task_content (the speaking prompt/scenario, in German), preparation_instructions (how the student should prepare/what to cover, in German), and 3-5 rubric_criteria for evaluating the recording (each with a short name like "Aussprache", "Flüssigkeit", "Wortschatz", "Aufgabenbewältigung" and a max_score out of 5).

Respond with ONLY a JSON object (no markdown, no prose), exactly this shape:
{{"task_content": "...", "preparation_instructions": "...", "rubric_criteria": [{{"name": "...", "max_score": 5}}]}}"""

    text = await call_gemini(prompt)
    data = extract_json_object(text)

    try:
        return AISprechenPreview.model_validate(data)
    except ValidationError as exc:
        raise AIContentError(f"Gemini returned an unexpected shape: {exc}") from exc
