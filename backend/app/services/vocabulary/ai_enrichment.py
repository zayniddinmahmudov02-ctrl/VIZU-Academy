"""Gemini-backed content generation for the bulk vocabulary generator:
word-type/article/plural detection, German -> Uzbek translation, a
level-appropriate example sentence, and its translation — for a whole
batch of words in one call — plus German pronunciation audio.

Audio uses Gemini's own native audio-output models (generateContent with
responseModalities=["AUDIO"]), not the separate Google Cloud
Text-to-Speech product — that product requires OAuth2/service-account
credentials and rejects plain API keys outright ("API keys are not
supported by this API", confirmed live), which GEMINI_API_KEY can never
satisfy. Gemini's native TTS uses the exact same API key and endpoint as
the text side above, just a TTS-capable model — genuinely reachable with
what this project already has.

Same urllib + asyncio.to_thread approach as this project's other real,
Gemini-backed AI feature (app/services/mock_exam/ai_service.py, used for
writing/speaking evaluation) — the helpers here are deliberately
duplicated rather than imported from there, so the bulk vocabulary
generator has zero coupling to mock-exam internals and touches nothing
in that already-working system.

Requires GEMINI_API_KEY (see app/core/config.py) for both text and
audio. Every function raises AIServiceError (never a bare exception)
with the real cause, so callers can surface it instead of a bare 500.
"""

import asyncio
import base64
import json
import re
import struct
import time
import urllib.error
import urllib.request
from collections import deque

from app.core.config import settings
from app.core.logging.logger import logger

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

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
    pass


def _require_api_key() -> str:
    if not settings.GEMINI_API_KEY:
        raise AIServiceError(
            "GEMINI_API_KEY is not configured. Set it in the backend "
            "environment to enable the bulk vocabulary generator."
        )
    return settings.GEMINI_API_KEY


def _call_gemini(parts: list[dict]) -> str:
    """Synchronous — always call via asyncio.to_thread, never directly
    from an async endpoint."""
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
        with urllib.request.urlopen(request, timeout=90) as response:
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


async def enrich_words(words: list[str], level: str) -> list[dict]:
    """One batched call for the whole list — cheaper and far faster than
    one request per word, and the model naturally keeps translations
    consistent when it sees related words together."""

    word_list = "\n".join(f"- {w}" for w in words)
    prompt = ENRICHMENT_PROMPT.format(level=level, word_list=word_list)

    text = await asyncio.to_thread(_call_gemini, [{"text": prompt}])
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


_PCM_RATE_RE = re.compile(r"rate=(\d+)")


def _pcm_to_wav(pcm_data: bytes, sample_rate: int, channels: int = 1, bits_per_sample: int = 16) -> bytes:
    """Gemini's native TTS returns headerless raw PCM (mimeType
    "audio/L16;codec=pcm;rate=<n>") — not a playable file on its own.
    Wraps it in a standard 44-byte WAV header so it's a normal .wav file
    any <audio> element (or storage-backed URL) can just play."""

    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    data_size = len(pcm_data)

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_size, b"WAVE",
        b"fmt ", 16, 1, channels, sample_rate, byte_rate, block_align, bits_per_sample,
        b"data", data_size,
    )
    return header + pcm_data


_TTS_MAX_ATTEMPTS = 3
_TTS_BACKOFF_SECONDS = [1, 2, 4]
_TTS_MAX_RETRY_WAIT_SECONDS = 45  # cap so one rate-limited word can't stall a whole batch too long

_RETRY_DELAY_RE = re.compile(r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"')


_QUOTA_ID_RE = re.compile(r'"quotaId"\s*:\s*"([^"]+)"')


class RateLimitError(AIServiceError):
    """HTTP 429 specifically — Google's free tier for the TTS model is
    genuinely this tight (confirmed live: 3 requests/minute AND 10
    requests/day, RESOURCE_EXHAUSTED). retry_delay, when Google supplies
    one, is what it explicitly asked callers to wait — ignoring it and
    retrying immediately just gets rejected again.

    is_daily distinguishes the two quota violations Google actually
    returns (parsed from the response's own quotaId): a per-MINUTE hit
    is worth retrying within this call (see synthesize_word_audio), a
    per-DAY hit is a hard wall for the rest of today — no amount of
    waiting within one request resolves it, so callers should stop
    attempting further words entirely rather than retry each one."""

    def __init__(self, message: str, retry_delay: float | None, is_daily: bool):
        super().__init__(message)
        self.retry_delay = retry_delay
        self.is_daily = is_daily


def _parse_retry_delay(detail: str) -> float | None:
    match = _RETRY_DELAY_RE.search(detail)
    return float(match.group(1)) if match else None


def _parse_is_daily_quota(detail: str) -> bool:
    match = _QUOTA_ID_RE.search(detail)
    return bool(match and "PerDay" in match.group(1))


def _call_tts_once(text: str) -> bytes:
    api_key = _require_api_key()

    url = GEMINI_ENDPOINT.format(model=settings.GEMINI_TTS_MODEL) + f"?key={api_key}"
    payload = json.dumps(
        {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "languageCode": "de-DE",
                    "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": settings.GEMINI_TTS_VOICE}},
                },
            },
        }
    ).encode("utf-8")

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
        if exc.code == 429:
            raise RateLimitError(
                f"Gemini TTS error (429): {detail}",
                _parse_retry_delay(detail),
                _parse_is_daily_quota(detail),
            ) from exc
        raise AIServiceError(f"Gemini TTS error ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise AIServiceError(f"Could not reach Gemini API: {exc.reason}") from exc

    try:
        inline = body["candidates"][0]["content"]["parts"][0]["inlineData"]
        mime_type = inline["mimeType"]
        pcm_data = base64.b64decode(inline["data"])
    except (KeyError, IndexError) as exc:
        raise AIServiceError(f"Unexpected Gemini TTS response shape: {body}") from exc

    rate_match = _PCM_RATE_RE.search(mime_type)
    if not rate_match:
        raise AIServiceError(f"Unrecognized TTS audio format: {mime_type}")

    return _pcm_to_wav(pcm_data, sample_rate=int(rate_match.group(1)))


# Process-wide sliding-window limiter for TTS call *starts* — a
# concurrency semaphore alone doesn't stop this, since fast calls can
# still start more than the quota allows within one 60s window even at
# concurrency 1-2. Confirmed live: gemini-2.5-flash-tts free tier allows
# only 3 requests/minute; VOCAB_BULK_TTS_MAX_PER_MINUTE defaults to that
# exact number and should be raised once the project is on a paid plan.
_tts_call_times: deque[float] = deque()
_tts_rate_lock = asyncio.Lock()


async def _wait_for_tts_rate_slot() -> None:
    limit = settings.VOCAB_BULK_TTS_MAX_PER_MINUTE
    async with _tts_rate_lock:
        while True:
            now = time.monotonic()
            while _tts_call_times and now - _tts_call_times[0] >= 60:
                _tts_call_times.popleft()
            if len(_tts_call_times) < limit:
                _tts_call_times.append(now)
                return
            await asyncio.sleep(60 - (now - _tts_call_times[0]) + 0.25)


async def synthesize_word_audio(word: str) -> bytes:
    """de-DE pronunciation of exactly `word` (the bare Wort, no article —
    see the bulk-import spec's "Audio target: Wort"). Returns a complete
    .wav file's bytes.

    Retries up to _TTS_MAX_ATTEMPTS times for transient failures only:
    - HTTP 429, per-minute quota — waits Google's own stated retryDelay
      when given, since retrying sooner is guaranteed to fail again.
    - An empty-content response with no error (finishReason="OTHER",
      confirmed live as a genuine intermittent quirk of this preview
      model, not tied to rate limiting) — fixed exponential backoff.
    Never retried:
    - HTTP 429, per-DAY quota — a hard wall for the rest of today; no
      wait within a single request resolves it, so this fails on the
      first attempt rather than burning the remaining attempt budget.
    - Every other AIServiceError (bad/missing key, malformed request,
      non-429 4xx) — retrying those cannot succeed either."""

    last_error: AIServiceError | None = None

    for attempt in range(1, _TTS_MAX_ATTEMPTS + 1):
        await _wait_for_tts_rate_slot()

        try:
            audio = await asyncio.to_thread(_call_tts_once, word)
        except RateLimitError as exc:
            last_error = exc
            if exc.is_daily:
                logger.warning("Vocabulary TTS: '%s' hit the DAILY quota, not retrying", word)
                raise
            if attempt == _TTS_MAX_ATTEMPTS:
                logger.warning("Vocabulary TTS: '%s' rate-limited, out of retries", word)
                raise
            delay = min(exc.retry_delay or _TTS_BACKOFF_SECONDS[attempt - 1], _TTS_MAX_RETRY_WAIT_SECONDS)
            logger.warning(
                "Vocabulary TTS: '%s' rate-limited (attempt %d/%d), retrying in %.1fs",
                word, attempt, _TTS_MAX_ATTEMPTS, delay,
            )
            await asyncio.sleep(delay)
        except AIServiceError as exc:
            last_error = exc
            transient = "Unexpected Gemini TTS response shape" in str(exc)
            if not transient or attempt == _TTS_MAX_ATTEMPTS:
                logger.warning("Vocabulary TTS: '%s' failed permanently: %s", word, exc)
                raise
            logger.warning(
                "Vocabulary TTS: '%s' empty response (attempt %d/%d), retrying in %ds",
                word, attempt, _TTS_MAX_ATTEMPTS, _TTS_BACKOFF_SECONDS[attempt - 1],
            )
            await asyncio.sleep(_TTS_BACKOFF_SECONDS[attempt - 1])
        else:
            logger.info("Vocabulary TTS: '%s' PASS (%d bytes, attempt %d)", word, len(audio), attempt)
            return audio

    raise last_error  # unreachable, keeps type-checkers happy
