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
import urllib.error
import urllib.request

from app.core.config import settings

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


def _call_tts(text: str) -> bytes:
    """Synchronous — always call via asyncio.to_thread. Returns a
    complete, playable .wav file's bytes."""
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


async def synthesize_word_audio(word: str) -> bytes:
    """de-DE pronunciation of exactly `word` (the bare Wort, no article —
    see the bulk-import spec's "Audio target: Wort"). Returns a complete
    .wav file's bytes."""
    return await asyncio.to_thread(_call_tts, word)
