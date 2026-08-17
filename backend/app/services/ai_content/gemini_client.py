"""Shared low-level Gemini call for the admin content-generation
endpoints (Grammatik Quiz / Lesen / Hören / Schreiben / Sprechen).

Same urllib + asyncio.to_thread approach, same GEMINI_API_KEY/
GEMINI_MODEL settings, as this project's other two real Gemini
integrations (app/services/mock_exam/ai_service.py,
app/services/vocabulary/ai_enrichment.py) — deliberately not imported
from either, so this module has zero coupling to mock-exam or
vocabulary internals. Only the "call Gemini, get raw text back" step is
shared here; each feature's own prompt template and response
validation stays in its own endpoint, per this codebase's convention of
not coupling feature business logic across features.
"""

import asyncio
import json
import re
import urllib.error
import urllib.request

from app.core.config import settings

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class AIContentError(Exception):
    pass


def _require_api_key() -> str:
    if not settings.GEMINI_API_KEY:
        raise AIContentError(
            "GEMINI_API_KEY is not configured. Set it in the backend environment to enable AI content generation."
        )
    return settings.GEMINI_API_KEY


def _call_gemini_sync(prompt: str) -> str:
    """Synchronous — always call via asyncio.to_thread, never directly
    from an async endpoint."""
    api_key = _require_api_key()

    url = GEMINI_ENDPOINT.format(model=settings.GEMINI_MODEL) + f"?key={api_key}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise AIContentError(f"Gemini API error ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise AIContentError(f"Could not reach Gemini API: {exc.reason}") from exc

    try:
        return body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise AIContentError(f"Unexpected Gemini response shape: {body}") from exc


async def call_gemini(prompt: str) -> str:
    return await asyncio.to_thread(_call_gemini_sync, prompt)


def extract_json_object(text: str) -> dict:
    """Gemini is asked to return only JSON, but models occasionally wrap
    it in prose or a ```json fence — pull out the first {...} block
    rather than trusting the whole response body is valid JSON alone."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise AIContentError(f"No JSON object found in Gemini response: {text[:500]}")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise AIContentError(f"Gemini returned malformed JSON: {exc}") from exc
