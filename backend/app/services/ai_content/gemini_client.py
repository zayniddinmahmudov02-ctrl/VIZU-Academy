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
import time
import urllib.error
import urllib.request

from app.core.config import settings

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Bounded exponential backoff for transient upstream failures (503/
# UNAVAILABLE, 429/rate-limited) only -- 4 total attempts (1 initial +
# 3 retries). Permanent errors (auth, bad request, config) are never
# retried; they raise on the first attempt.
RETRY_DELAYS_SECONDS = [2, 5, 10]


class AIContentError(Exception):
    def __init__(self, message: str, transient: bool = False):
        super().__init__(message)
        self.transient = transient


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

    body = _post_with_retry(request)

    try:
        return body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise AIContentError(f"Unexpected Gemini response shape: {body}") from exc


def _post_with_retry(request: urllib.request.Request) -> dict:
    """Retries only 503 (UNAVAILABLE) and 429 (rate-limited) — genuinely
    transient upstream conditions. Everything else (401/403 auth, 400
    validation, missing config) raises immediately on the first
    attempt, since retrying a request that will fail the same way every
    time just wastes 17 seconds before failing anyway."""
    delays = [0] + RETRY_DELAYS_SECONDS
    for attempt, delay in enumerate(delays):
        if delay:
            time.sleep(delay)

        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            is_transient = exc.code in (503, 429)
            is_last_attempt = attempt == len(delays) - 1
            if not is_transient or is_last_attempt:
                raise AIContentError(f"Gemini API error ({exc.code}): {detail}", transient=is_transient) from exc
        except urllib.error.URLError as exc:
            if attempt == len(delays) - 1:
                raise AIContentError(f"Could not reach Gemini API: {exc.reason}", transient=True) from exc

    raise AIContentError("Gemini request failed after retries.", transient=True)


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
