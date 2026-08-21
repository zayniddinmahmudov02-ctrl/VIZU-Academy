"""Gemini-backed TEXT enrichment for the bulk vocabulary generator:
word-type/article/plural detection, German -> Uzbek translation, a
level-appropriate example sentence, and its translation — for a whole
batch of words in one call.

No vocabulary pronunciation-audio feature exists in this project — this
module is text-only by design, and audio_url (when set at all) is a
plain manually-provided URL.

Same urllib + asyncio.to_thread approach as this project's other real,
Gemini-backed AI feature (app/services/mock_exam/ai_service.py, used for
writing/speaking evaluation) — the helpers here are deliberately
duplicated rather than imported from there, so the bulk vocabulary
generator has zero coupling to mock-exam internals and touches nothing
in that already-working system.

Requires GEMINI_API_KEY (see app/core/config.py). Every function raises
AIServiceError (never a bare exception) with the real cause, so callers
can surface it instead of a bare 500.
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

# Bounded exponential backoff for transient upstream failures only -- 4
# total attempts per model (1 initial + 3 retries), plus a small random
# jitter added to each wait so many concurrent admin requests don't all
# retry in lockstep. If Gemini sends a Retry-After header, that's used
# instead of the fixed delay (clamped to RETRY_AFTER_MAX_SECONDS so one
# upstream hint can't stall the whole request indefinitely). Permanent
# errors (auth, bad request, config) are never retried; they raise on
# the first attempt, against either model.
RETRY_DELAYS_SECONDS = [2, 5, 10]
RETRY_AFTER_MAX_SECONDS = 30
JITTER_MAX_SECONDS = 1.0
TRANSIENT_HTTP_STATUS_CODES = {429, 500, 502, 503, 504}

VALID_WORD_TYPES = {
    "NOMEN",
    "VERB",
    "ADJEKTIV",
    "ADVERB",
    "PRONOMEN",
    "PRAEPOSITION",
    "KONJUNKTION",
    "REDEWENDUNG",
    "OTHER",
}


class AIServiceError(Exception):
    def __init__(self, message: str, transient: bool = False):
        super().__init__(message)
        self.transient = transient


def _require_api_key() -> str:
    if not settings.GEMINI_API_KEY:
        raise AIServiceError(
            "GEMINI_API_KEY is not configured. Set it in the backend "
            "environment to enable the bulk vocabulary generator."
        )
    return settings.GEMINI_API_KEY


def _build_request(parts: list[dict], model: str, api_key: str) -> urllib.request.Request:
    url = GEMINI_ENDPOINT.format(model=model) + f"?key={api_key}"
    payload = json.dumps({"contents": [{"parts": parts}]}).encode("utf-8")
    return urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )


def _call_gemini(parts: list[dict], context: str = "vocabulary") -> str:
    """Synchronous — always call via asyncio.to_thread, never directly
    from an async endpoint. Tries GEMINI_MODEL first; only if that
    model's own retries are exhausted on a transient failure, and
    GEMINI_FALLBACK_MODEL is explicitly configured, does it try the
    fallback model (with its own retry sequence) before giving up."""
    api_key = _require_api_key()

    primary_request = _build_request(parts, settings.GEMINI_MODEL, api_key)
    try:
        body = _post_with_retry(primary_request, model_label="primary", context=context)
    except AIServiceError as primary_exc:
        if not primary_exc.transient or not settings.GEMINI_FALLBACK_MODEL:
            raise

        print(f"[VOCAB] context={context} primary model exhausted, trying fallback model")
        fallback_request = _build_request(parts, settings.GEMINI_FALLBACK_MODEL, api_key)
        try:
            body = _post_with_retry(fallback_request, model_label="fallback", context=context)
        except AIServiceError:
            # Surface the primary model's failure -- it's the one actually
            # configured for production use; the fallback attempt was a
            # bonus, and its own failure doesn't need a second raise.
            raise primary_exc

    try:
        return body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise AIServiceError(f"Unexpected Gemini response shape: {body}") from exc


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
    timeout into URLError, so the URLError branch already covers it).
    Everything else (401/403 auth, 400 validation, missing config)
    raises immediately on the first attempt — retrying a request that
    will fail the same way every time just wastes up to 17 seconds
    before failing anyway."""
    total_attempts = len(RETRY_DELAYS_SECONDS) + 1  # 1 initial + 3 retries
    for attempt in range(1, total_attempts + 1):
        start = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))
            duration = time.monotonic() - start
            print(
                f"[VOCAB] context={context} model={model_label} attempt={attempt} "
                f"status=success duration={duration:.2f}s"
            )
            return result
        except urllib.error.HTTPError as exc:
            duration = time.monotonic() - start
            detail = exc.read().decode("utf-8", errors="ignore")
            is_transient = exc.code in TRANSIENT_HTTP_STATUS_CODES
            is_last_attempt = attempt == total_attempts
            print(
                f"[VOCAB] context={context} model={model_label} attempt={attempt} "
                f"status={exc.code} transient={is_transient} duration={duration:.2f}s"
            )
            if not is_transient or is_last_attempt:
                raise AIServiceError(f"Gemini API error ({exc.code}): {detail}", transient=is_transient) from exc

            # RETRY_DELAYS_SECONDS[attempt - 1] is the wait BEFORE the
            # next attempt (attempt 1 failing waits [0]=2s before
            # attempt 2, attempt 2 failing waits [1]=5s before attempt
            # 3, etc.) -- not this attempt's own (already-elapsed) delay.
            base_delay = RETRY_DELAYS_SECONDS[attempt - 1]
            retry_after = _retry_after_seconds(exc)
            wait = retry_after if retry_after is not None else base_delay + random.uniform(0, JITTER_MAX_SECONDS)
            time.sleep(wait)
        except urllib.error.URLError as exc:
            duration = time.monotonic() - start
            is_last_attempt = attempt == total_attempts
            print(
                f"[VOCAB] context={context} model={model_label} attempt={attempt} "
                f"status=network_error({exc.reason}) transient=True duration={duration:.2f}s"
            )
            if is_last_attempt:
                raise AIServiceError(f"Could not reach Gemini API: {exc.reason}", transient=True) from exc
            base_delay = RETRY_DELAYS_SECONDS[attempt - 1]
            time.sleep(base_delay + random.uniform(0, JITTER_MAX_SECONDS))

    raise AIServiceError("Gemini request failed after retries.", transient=True)


def _extract_json_array(text: str) -> list:
    """Gemini is asked to return only JSON, but models occasionally wrap
    it in prose or a ```json fence — pull out the first [...] block
    rather than trusting the whole response body is valid JSON alone."""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise AIServiceError(f"No JSON array found in Gemini response: {text[:500]}")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise AIServiceError(f"Gemini returned malformed JSON: {exc}") from exc


ENRICHMENT_PROMPT = """You are a German-language curriculum assistant preparing Wortschatz (vocabulary) entries for Uzbek-speaking students at level {level}.

For EACH input word/phrase below, determine:
- word_type: exactly one of NOMEN, VERB, ADJEKTIV, ADVERB, PRONOMEN, PRAEPOSITION, KONJUNKTION, REDEWENDUNG, OTHER
- article: "der", "die", or "das" if word_type is NOMEN — the correct German grammatical gender, even if the input already includes a (possibly wrong) article; correct it if it's wrong. null for every other word_type.
- base_word: the word itself without any article prefix, correctly capitalized per German orthography (nouns capitalized, verbs/adjectives lowercase)
- plural: for word_type NOMEN — the real German plural form (e.g. "Häuser", "Wohnungen", "Studenten"). Use "—" if the noun has no natural plural (an uncountable/mass noun) — never invent an implausible plural. null for every other word_type.
- translation: a natural, contextually appropriate Uzbek translation — not a stiff literal one
- example_sentence: one natural German sentence at level {level} that actually uses base_word
- example_translation: a natural Uzbek translation of example_sentence

Input words (one per line):
{word_list}

Respond with ONLY a JSON array (no markdown, no prose), one object per input word IN THE SAME ORDER, exactly this shape:
[{{"input": "<the original input line, verbatim>", "word_type": "...", "article": "..."|null, "base_word": "...", "plural": "..."|null, "translation": "...", "example_sentence": "...", "example_translation": "..."}}]"""


async def enrich_words(words: list[str], level: str, context: str = "vocabulary") -> list[dict]:
    """One batched call for the whole list — cheaper and far faster than
    one request per word, and the model naturally keeps translations
    consistent when it sees related words together. `context` is only
    used for server-side log lines (e.g. a lesson id) — never sent to
    the client or to Gemini."""

    word_list = "\n".join(f"- {w}" for w in words)
    prompt = ENRICHMENT_PROMPT.format(level=level, word_list=word_list)

    text = await asyncio.to_thread(_call_gemini, [{"text": prompt}], context)
    results = _extract_json_array(text)

    if len(results) != len(words):
        raise AIServiceError(
            f"Gemini returned {len(results)} results for {len(words)} input words — "
            "refusing to guess which is which."
        )

    normalized = []
    for item in results:
        word_type = str(item.get("word_type") or "OTHER").upper()
        if word_type not in VALID_WORD_TYPES:
            word_type = "OTHER"

        normalized.append(
            {
                "input": item.get("input"),
                "word_type": word_type,
                # Only NOMEN ever gets an article/plural — never fill these
                # in for a verb/adjective/etc. even if the model tried to.
                "article": (item.get("article") or None) if word_type == "NOMEN" else None,
                "base_word": item.get("base_word") or item.get("input") or "",
                "plural": (item.get("plural") or None) if word_type == "NOMEN" else None,
                "translation": item.get("translation") or "",
                "example_sentence": item.get("example_sentence") or "",
                "example_translation": item.get("example_translation") or "",
            }
        )

    return normalized
