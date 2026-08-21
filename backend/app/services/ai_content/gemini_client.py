"""Shared low-level Gemini call for the admin content-generation
endpoints (Grammatik Quiz / Lesen / Hören / Schreiben / Sprechen) AND
the multi-lesson vocabulary generation script
(app/scripts/vocabulary_cleanup_and_generate.py) — both call
`call_gemini(prompt)` and get the same retry/fallback policy for free.

Same urllib + asyncio.to_thread approach, same GEMINI_API_KEY/
GEMINI_MODEL settings, as this project's other real Gemini integration
(app/services/mock_exam/ai_service.py) and the near-identical
app/services/vocabulary/ai_enrichment.py (used by the admin "Wörter
importieren" dialog, which has its own copy of this same retry policy
since its call shape — a list of "parts" — differs slightly). The
public call_gemini(prompt: str) -> str signature and behavior are
unchanged from before this file's retry hardening — every existing
caller (the 5 AI content-generation endpoints) is unaffected by this
upgrade; they only get more resilient to transient upstream failures.
"""

import asyncio
import json
import random
import re
import time
import urllib.error
import urllib.request

from app.core.config import settings

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Bounded exponential backoff for transient upstream failures only --
# 4 total attempts per model (1 initial + 3 retries), plus a small
# random jitter added to each wait so many concurrent requests don't
# retry in lockstep. A Gemini-supplied Retry-After header is honored
# instead of the fixed delay when present (clamped to
# RETRY_AFTER_MAX_SECONDS). Permanent errors (auth, bad request,
# config) are never retried; they raise on the first attempt, against
# either model.
RETRY_DELAYS_SECONDS = [2, 5, 10]
RETRY_AFTER_MAX_SECONDS = 30
JITTER_MAX_SECONDS = 1.0
TRANSIENT_HTTP_STATUS_CODES = {429, 500, 502, 503, 504}


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


def _build_request(prompt: str, model: str, api_key: str) -> urllib.request.Request:
    url = GEMINI_ENDPOINT.format(model=model) + f"?key={api_key}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    return urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )


def _call_gemini_sync(prompt: str, context: str = "ai-content") -> str:
    """Synchronous — always call via asyncio.to_thread, never directly
    from an async endpoint. Tries GEMINI_MODEL first; only if that
    model's own retries are exhausted on a transient failure, and
    GEMINI_FALLBACK_MODEL is explicitly configured (verified separately
    — see app/scripts/check_gemini_models.py — never guessed), does it
    try the fallback model (with its own retry sequence) before giving
    up."""
    api_key = _require_api_key()

    primary_request = _build_request(prompt, settings.GEMINI_MODEL, api_key)
    try:
        body = _post_with_retry(primary_request, model_label="primary", context=context)
    except AIContentError as primary_exc:
        if not primary_exc.transient or not settings.GEMINI_FALLBACK_MODEL:
            raise

        print(f"[AI-CONTENT] context={context} primary model exhausted, trying fallback model")
        fallback_request = _build_request(prompt, settings.GEMINI_FALLBACK_MODEL, api_key)
        try:
            body = _post_with_retry(fallback_request, model_label="fallback", context=context)
        except AIContentError:
            # The primary model is the one actually configured for
            # production use; surface its failure, not the fallback's.
            raise primary_exc

    try:
        return body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise AIContentError(f"Unexpected Gemini response shape: {body}") from exc


def _retry_after_seconds(exc: urllib.error.HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers else None
    if not raw:
        return None
    try:
        seconds = float(raw)
    except ValueError:
        return None
    return max(0.0, min(seconds, RETRY_AFTER_MAX_SECONDS))


def _post_with_retry(request: urllib.request.Request, model_label: str, context: str) -> dict:
    """Retries only genuinely transient upstream conditions (429, 500,
    502, 503, 504, and network/timeout errors — urllib wraps a socket
    timeout into URLError). Everything else (401/403 auth, 400
    validation, missing config) raises immediately on the first
    attempt, since retrying a request that will fail the same way every
    time just wastes up to 17 seconds before failing anyway."""
    total_attempts = len(RETRY_DELAYS_SECONDS) + 1
    for attempt in range(1, total_attempts + 1):
        start = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))
            duration = time.monotonic() - start
            print(
                f"[AI-CONTENT] context={context} model={model_label} attempt={attempt} "
                f"status=success duration={duration:.2f}s"
            )
            return result
        except urllib.error.HTTPError as exc:
            duration = time.monotonic() - start
            detail = exc.read().decode("utf-8", errors="ignore")
            is_transient = exc.code in TRANSIENT_HTTP_STATUS_CODES
            is_last_attempt = attempt == total_attempts
            print(
                f"[AI-CONTENT] context={context} model={model_label} attempt={attempt} "
                f"status={exc.code} transient={is_transient} duration={duration:.2f}s"
            )
            if not is_transient or is_last_attempt:
                raise AIContentError(f"Gemini API error ({exc.code}): {detail}", transient=is_transient) from exc

            base_delay = RETRY_DELAYS_SECONDS[attempt - 1]
            retry_after = _retry_after_seconds(exc)
            wait = retry_after if retry_after is not None else base_delay + random.uniform(0, JITTER_MAX_SECONDS)
            time.sleep(wait)
        except urllib.error.URLError as exc:
            duration = time.monotonic() - start
            is_last_attempt = attempt == total_attempts
            print(
                f"[AI-CONTENT] context={context} model={model_label} attempt={attempt} "
                f"status=network_error({exc.reason}) transient=True duration={duration:.2f}s"
            )
            if is_last_attempt:
                raise AIContentError(f"Could not reach Gemini API: {exc.reason}", transient=True) from exc
            base_delay = RETRY_DELAYS_SECONDS[attempt - 1]
            time.sleep(base_delay + random.uniform(0, JITTER_MAX_SECONDS))

    raise AIContentError("Gemini request failed after retries.", transient=True)


async def call_gemini(prompt: str, context: str = "ai-content") -> str:
    return await asyncio.to_thread(_call_gemini_sync, prompt, context)


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
