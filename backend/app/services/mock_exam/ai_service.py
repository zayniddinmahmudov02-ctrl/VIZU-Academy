"""Gemini-backed evaluation for Schreiben (writing) and Sprechen (speaking)
mock-exam submissions.

Uses Python's stdlib `urllib` rather than an SDK/httpx — this sandbox
cannot `pip install` anything into the backend venv (write-protected
site-packages), so this is the only HTTP client available without adding a
dependency the project can't actually install here. `urllib` is
synchronous; calls are wrapped in `asyncio.to_thread` so they don't block
the event loop.

Requires `GEMINI_API_KEY` to be set in the environment — see
app/core/config.py. Every function raises `AIServiceError` (never a bare
exception) if the key is missing or the API call fails, so callers can
turn it into a clean 502 instead of a 500.
"""

import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from app.core.config import settings

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class AIServiceError(Exception):
    pass


def _require_api_key() -> str:
    if not settings.GEMINI_API_KEY:
        raise AIServiceError(
            "GEMINI_API_KEY is not configured. Set it in the backend "
            "environment to enable AI evaluation."
        )
    return settings.GEMINI_API_KEY


def _call_gemini(parts: list[dict]) -> str:
    """Synchronous — call from a thread (see `asyncio.to_thread` in the
    async wrappers below), never directly from an async endpoint."""
    api_key = _require_api_key()

    url = GEMINI_ENDPOINT.format(model=settings.GEMINI_MODEL) + f"?key={api_key}"
    payload = json.dumps({"contents": [{"parts": parts}]}).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise AIServiceError(f"Gemini API error ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise AIServiceError(f"Could not reach Gemini API: {exc.reason}") from exc

    try:
        return body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise AIServiceError(f"Unexpected Gemini response shape: {body}") from exc


def _extract_json(text: str) -> dict:
    """Gemini is asked to return only JSON, but models occasionally wrap it
    in prose or a ```json fence — pull out the first {...} block rather
    than trusting the whole response body is valid JSON on its own."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise AIServiceError(f"No JSON object found in Gemini response: {text[:500]}")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise AIServiceError(f"Gemini returned malformed JSON: {exc}") from exc


def _read_local_or_remote_bytes(url_or_path: str) -> bytes:
    if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
        with urllib.request.urlopen(url_or_path, timeout=30) as response:
            return response.read()

    # Local storage convention: LocalStorage.url() returns "/uploads/{path}"
    relative = url_or_path.lstrip("/")
    if relative.startswith("uploads/"):
        relative = relative[len("uploads/"):]
    file_path = Path("uploads") / relative

    if not file_path.exists():
        raise AIServiceError(f"Audio file not found on disk: {file_path}")

    return file_path.read_bytes()


WRITING_EVAL_PROMPT = """You are a certified German language examiner evaluating a Schreiben (writing) submission for a {level} certification exam.

TASK GIVEN TO THE STUDENT:
{task_text}

EVALUATION RUBRIC (if provided by the exam admin):
{rubric}

STUDENT'S ANSWER:
{answer_text}

Evaluate this answer and respond with ONLY a JSON object (no markdown, no prose) in exactly this shape:
{{
  "grammar_score": <0-100 integer>,
  "vocabulary_score": <0-100 integer>,
  "structure_score": <0-100 integer>,
  "task_achievement_score": <0-100 integer>,
  "coherence_score": <0-100 integer>,
  "overall_score": <0-{max_points} integer, scaled to the exam's max points>,
  "feedback": "<detailed feedback in German, 3-5 sentences, covering strengths and concrete improvements>"
}}"""

SPEAKING_EVAL_PROMPT = """You are a certified German language examiner evaluating a Sprechen (speaking) submission for a certification exam.

TASK GIVEN TO THE STUDENT:
{task_text}

Listen to the attached audio recording. First transcribe it, then evaluate the student's spoken German.

Respond with ONLY a JSON object (no markdown, no prose) in exactly this shape:
{{
  "transcript": "<full transcription of the audio in German>",
  "score": <0-100 integer>,
  "feedback": "<detailed feedback in German, 3-5 sentences, covering pronunciation, fluency, grammar, and task fulfillment>"
}}"""


async def evaluate_writing(
    task_text: str,
    answer_text: str,
    rubric: str | None,
    max_points: int,
    level: str = "B2",
) -> dict:
    import asyncio

    prompt = WRITING_EVAL_PROMPT.format(
        level=level,
        task_text=task_text,
        rubric=rubric or "(none provided — use standard exam-level expectations)",
        answer_text=answer_text,
        max_points=max_points,
    )

    text = await asyncio.to_thread(_call_gemini, [{"text": prompt}])
    result = _extract_json(text)

    required = {
        "grammar_score",
        "vocabulary_score",
        "structure_score",
        "task_achievement_score",
        "coherence_score",
        "overall_score",
        "feedback",
    }
    missing = required - result.keys()
    if missing:
        raise AIServiceError(f"Gemini response missing fields: {missing}")

    return result


async def evaluate_speaking(task_text: str, audio_url: str) -> dict:
    import asyncio

    audio_bytes = await asyncio.to_thread(_read_local_or_remote_bytes, audio_url)
    audio_b64 = base64.b64encode(audio_bytes).decode("ascii")

    mime_type = "audio/mpeg"
    lower = audio_url.lower()
    if lower.endswith(".wav"):
        mime_type = "audio/wav"
    elif lower.endswith(".m4a"):
        mime_type = "audio/mp4"

    prompt = SPEAKING_EVAL_PROMPT.format(task_text=task_text)

    parts = [
        {"text": prompt},
        {"inline_data": {"mime_type": mime_type, "data": audio_b64}},
    ]

    text = await asyncio.to_thread(_call_gemini, parts)
    result = _extract_json(text)

    required = {"transcript", "score", "feedback"}
    missing = required - result.keys()
    if missing:
        raise AIServiceError(f"Gemini response missing fields: {missing}")

    return result
