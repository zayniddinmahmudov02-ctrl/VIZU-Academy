"""AI subtitles of Medienwelt films: speech-to-text with time stamps, translation, and the pure helpers around them.

Providers (settings, keys stay on the server and travel in a request header, never in a URL or an error text):
  * speech-to-text `SUBTITLE_STT_PROVIDER`: "gemini" (GEMINI_API_KEY; the model returns timed segments as JSON, a new segment per speaker turn)
    or "openai" (Whisper `verbose_json` segments, OPENAI_API_KEY);
  * translation `SUBTITLE_TRANSLATE_PROVIDER`: "gemini" or "google" (Cloud Translation v2, GOOGLE_TRANSLATE_API_KEY);
  * "fake" exists for the local test stack only (APP_ENV=test) and is refused everywhere else.
A provider without its key raises `SubtitleAIError("AI_NOT_CONFIGURED")` — the admin sees that message; nothing is ever invented.

Timing: the audio is cut into pieces of about SUBTITLE_CHUNK_SECONDS at a pause (`choose_cuts` over ffmpeg `silencedetect`), every piece is
transcribed on its own (short pieces keep the model's time stamps close), the segments are shifted back onto the film's clock, cleaned
(`build_cues`: sorted, no overlaps, readable minimum length, long lines wrapped) and their edges moved onto the real start / end of the speech
where a detected pause shows it (`snap_to_speech`). Nothing here touches the database (unit-tested in `tests/test_medien_subtitle_ai.py`)."""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.request
import uuid
from collections import Counter
from dataclasses import dataclass

from app.core.config import settings
from app.services.medien import subtitles as subs

log = logging.getLogger("vizu.medien.subtitle_ai")

LANGUAGES = ("de", "en", "uz", "ru")
PROMPT_NAMES = {"de": "German", "en": "English", "uz": "Uzbek (Latin script)", "ru": "Russian (Cyrillic script)"}
WHISPER_NAMES = {"german": "de", "english": "en", "uzbek": "uz", "russian": "ru"}
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GOOGLE_TRANSLATE_ENDPOINT = "https://translation.googleapis.com/language/translate/v2"
OPENAI_TRANSCRIBE_ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"
MAX_INLINE_BYTES = 18 * 1024 * 1024

MIN_CUE_MS = 700  # a shorter subtitle cannot be read
MAX_CUE_MS = 8000  # longer than any two subtitle lines need
SPOKEN = re.compile(r"\w")  # a line must contain a letter or digit
GAP_MS = 40  # between two cues that would otherwise touch / overlap
LINE_WIDTH = 42
SNAP_MS = 600  # how far an edge may move onto a detected pause
TAIL_MS = 150  # a cue stays this long after the speech stopped


class SubtitleAIError(Exception):
    """`code` (UPPER_SNAKE) is stored on the job and shown to the admin with the message; `retryable` = a later try may work."""

    def __init__(self, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


# ---------------- pure helpers ----------------

_SILENCE_START = re.compile(r"silence_start:\s*(-?\d+(?:\.\d+)?)")
_SILENCE_END = re.compile(r"silence_end:\s*(-?\d+(?:\.\d+)?)")


def parse_silences(stderr: str) -> list[tuple[float, float]]:
    """Pauses found by ffmpeg `silencedetect` ([(start_s, end_s)], sorted). A pause still open at the end of the file is dropped."""
    out: list[tuple[float, float]] = []
    start: float | None = None
    for line in stderr.splitlines():
        m = _SILENCE_START.search(line)
        if m:
            start = max(0.0, float(m.group(1)))
            continue
        m = _SILENCE_END.search(line)
        if m and start is not None:
            end = float(m.group(1))
            if end > start:
                out.append((start, end))
            start = None
    return sorted(out)


def choose_cuts(duration: float, silences: list[tuple[float, float]], target: float = 180, window: float = 25) -> list[float]:
    """Piece borders [0, …, duration]: about every `target` seconds, moved into the middle of the nearest pause within ±`window`
    (the longest one wins a tie), so a sentence is rarely cut in two. The last piece is never shorter than a third of `target`."""
    if duration <= 0:
        return [0.0]
    cuts = [0.0]
    while duration - cuts[-1] > target * 1.33:
        aim = cuts[-1] + target
        near = [(abs((s + e) / 2 - aim), -(e - s), (s + e) / 2) for s, e in silences if aim - window <= (s + e) / 2 <= aim + window]
        cut = min(near)[2] if near else aim
        if cut <= cuts[-1] + 1:
            cut = aim
        cuts.append(round(cut, 3))
    cuts.append(round(duration, 3))
    return cuts


def pieces(cuts: list[float]) -> list[tuple[float, float]]:
    return [(a, b) for a, b in zip(cuts, cuts[1:]) if b - a > 0.05]


_CLOCK = re.compile(r"^(?:(\d+):)?(\d+):(\d+(?:[.,]\d+)?)$")


def to_seconds(value) -> float | None:
    """12.5 / "12.5" / "0:12.5" / "00:00:12,500" → seconds; anything else → None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip()
    try:
        return float(text.replace(",", "."))
    except ValueError:
        pass
    m = _CLOCK.match(text)
    if not m:
        return None
    return int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + float(m.group(3).replace(",", "."))


def normalize_language(value) -> str | None:
    code = str(value or "").strip().lower()
    code = WHISPER_NAMES.get(code, code)
    code = {"deu": "de", "ger": "de", "eng": "en", "uzb": "uz", "rus": "ru"}.get(code, code)
    return code[:2] if len(code) >= 2 and code[:2].isalpha() else None


def parse_segments(raw: dict, piece_seconds: float) -> list[dict]:
    """The segments a provider answered for one piece, with times in seconds from the piece's start, clamped into the piece."""
    out = []
    for item in raw.get("segments") or []:
        if not isinstance(item, dict):
            continue
        start, end = to_seconds(item.get("start")), to_seconds(item.get("end"))
        text = subs.clean_text(str(item.get("text") or ""))
        if start is None or end is None or not text:
            continue
        start = min(max(0.0, start), piece_seconds)
        end = min(max(0.0, end), piece_seconds + 0.5)
        if end <= start:
            end = min(start + max(1.0, len(text) / 15), piece_seconds + 0.5)  # a reading time when the model gave no end
        speaker = str(item.get("speaker") or "").strip()[:12] or None
        out.append({"start": round(start, 3), "end": round(end, 3), "text": text, "speaker": speaker})
    return out


def wrap_text(text: str, width: int = LINE_WIDTH) -> str:
    """A single long line becomes two lines, broken at the space nearest the middle (existing line breaks are kept)."""
    if "\n" in text or len(text) <= width:
        return text
    middle = len(text) // 2
    spaces = [i for i, ch in enumerate(text) if ch == " "]
    if not spaces:
        return text
    at = min(spaces, key=lambda i: abs(i - middle))
    return text[:at].rstrip() + "\n" + text[at + 1:].lstrip()


def build_cues(segments: list[dict], video_ms: int | None = None) -> list[subs.Cue]:
    """Segments on the film clock (seconds) → clean, sorted cues: no empty text, no overlap, at least MIN_CUE_MS where the next cue allows it,
    nothing after the end of the video, long lines wrapped."""
    items = sorted((s for s in segments if s.get("text")), key=lambda s: (s["start"], s["end"]))
    cues: list[subs.Cue] = []
    for s in items:
        start, end = int(round(s["start"] * 1000)), int(round(s["end"] * 1000))
        if video_ms and start >= video_ms:
            continue
        if video_ms:
            end = min(end, video_ms)
        text = wrap_text(subs.clean_text(s["text"]))[:subs.MAX_CUE_TEXT]
        if not text or end <= start or not SPOKEN.search(text):  # "...", "[…]", "-": a placeholder for unclear sound, not a line (seen live: 176 s of "...")
            continue
        end = min(end, start + MAX_CUE_MS)  # a wrong end from the model never leaves a line on the screen for minutes
        if cues and cues[-1].text == text and start - cues[-1].end < 1500:  # the same words twice at a piece border
            cues[-1].end = max(cues[-1].end, end)
            continue
        cues.append(subs.Cue(start, end, text))
    for i, cue in enumerate(cues):
        nxt = cues[i + 1] if i + 1 < len(cues) else None
        if nxt and cue.end > nxt.start - GAP_MS:
            cue.end = max(cue.start + 1, nxt.start - GAP_MS)
        if cue.end - cue.start < MIN_CUE_MS:
            limit = (nxt.start - GAP_MS) if nxt else (video_ms or cue.start + MIN_CUE_MS)
            cue.end = max(cue.end, min(cue.start + MIN_CUE_MS, limit))
    return [c for c in cues if c.end > c.start]


def snap_to_speech(cues: list[subs.Cue], silences: list[tuple[float, float]], max_shift_ms: int = SNAP_MS) -> list[subs.Cue]:
    """Moves a cue start that lies inside a detected pause to the end of that pause (= where the voice starts), and a cue end inside a pause to
    just after its beginning (= where the voice stopped). Moves are small (≤ max_shift_ms) and never make a cue shorter than MIN_CUE_MS or let it
    overlap its neighbours. Without pauses (music under the speech) nothing moves."""
    ranges = [(int(s * 1000), int(e * 1000)) for s, e in silences]
    if not ranges:
        return cues

    def inside(ms: int):
        lo, hi = 0, len(ranges) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            s, e = ranges[mid]
            if ms < s:
                hi = mid - 1
            elif ms > e:
                lo = mid + 1
            else:
                return s, e
        return None

    out = [subs.Cue(c.start, c.end, c.text) for c in cues]
    for i, cue in enumerate(out):
        prev_end = out[i - 1].end if i else 0
        next_start = out[i + 1].start if i + 1 < len(out) else None
        hit = inside(cue.start)
        if hit and hit[1] - cue.start <= max_shift_ms and cue.end - hit[1] >= MIN_CUE_MS:
            cue.start = max(hit[1], prev_end + GAP_MS)
        hit = inside(cue.end)
        if hit and cue.end - (hit[0] + TAIL_MS) <= max_shift_ms and hit[0] + TAIL_MS - cue.start >= MIN_CUE_MS:
            cue.end = hit[0] + TAIL_MS
        if next_start is not None and cue.end > next_start - GAP_MS:
            cue.end = max(cue.start + 1, next_start - GAP_MS)
    return out


def majority_language(codes: list[str | None]) -> str | None:
    counted = Counter(c for c in codes if c)
    return counted.most_common(1)[0][0] if counted else None


def to_srt(cues: list[subs.Cue]) -> bytes:
    """SubRip export of a track (numbered blocks, comma milliseconds, plain text)."""
    def ts(ms: int) -> str:
        return f"{ms // 3_600_000:02d}:{ms // 60_000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    out = []
    for n, c in enumerate(cues, start=1):
        out += [str(n), f"{ts(c.start)} --> {ts(c.end)}", c.text, ""]
    return "\n".join(out).encode("utf-8")


def extract_json(text: str) -> dict | list:
    """The JSON of a model answer: the whole text, else the outermost {...} or [...] block (models sometimes wrap JSON in a ``` fence or prose).
    A top-level ARRAY is a valid answer too (seen live: the fast model answered the segment list without the object around it). Control
    characters inside strings (a real line break in a two-line subtitle) are accepted."""
    raw = (text or "").strip()
    candidates = [raw]
    for pattern in (r"\{.*\}", r"\[.*\]"):
        m = re.search(pattern, raw, re.DOTALL)
        if m:
            candidates.append(m.group(0))
    if not any(candidates):
        raise SubtitleAIError("AI_BAD_ANSWER", "The AI answer contained no JSON.", retryable=True)
    for candidate in sorted(set(c for c in candidates if c), key=lambda c: -len(c)):
        try:
            return json.loads(candidate, strict=False)
        except json.JSONDecodeError:
            continue
    raise SubtitleAIError("AI_BAD_ANSWER", "The AI answer was not valid JSON (cut off?).", retryable=True)


def as_object(answer: dict | list, key: str) -> dict:
    """{key: [...]} from an answer that may be the bare list."""
    if isinstance(answer, list):
        return {key: answer}
    return answer if isinstance(answer, dict) else {}


# ---------------- HTTP ----------------


def quota_kind(detail: dict) -> str:
    """For a Gemini 429: "day" = a daily quota is used up (asking again today does not help), "minute" = a per-minute rate limit (passes by
    itself; Google's text also says "exceeded your current quota"), "" = not said. Read from the QuotaFailure ids / RetryInfo / the message."""
    details = [d for d in detail.get("details") or [] if isinstance(d, dict)]
    ids = " ".join(str(v.get("quotaId", "")) for d in details for v in d.get("violations") or [] if isinstance(v, dict))
    text = f"{ids} {detail.get('message', '')}".lower()
    if "perday" in text or "per day" in text or "daily" in text:
        return "day"
    if "perminute" in text or "per minute" in text or "retry in" in text or any("RetryInfo" in str(d.get("@type", "")) for d in details):
        return "minute"
    return ""


def _post(url: str, body: bytes, headers: dict, timeout: int = 300) -> dict:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8", "replace")).get("error", {})
            detail = detail if isinstance(detail, dict) else {"message": str(detail)}
        except Exception:
            detail = {}
        message = str(detail.get("message") or "")[:200]
        code = exc.code
        if code in (401, 403):
            raise SubtitleAIError("AI_KEY_REJECTED", f"The AI service refused the key (HTTP {code}). {message}".strip()) from None
        kind = quota_kind(detail) if code == 429 else ""
        if code == 429 and (kind == "day" or (not kind and "quota" in message.lower())):
            # the key's daily quota for this model is used up: asking again in a few seconds does not help (the next model may still work).
            # A per-minute limit (seen live 2026-11-19 on a burst of proofreading) is an ordinary, retried 429 instead.
            raise SubtitleAIError("AI_QUOTA", f"The quota of the AI key is used up for this model. {message[:120]}".strip()) from None
        raise SubtitleAIError(f"AI_HTTP_{code}", f"The AI service answered HTTP {code}. {message}".strip(), retryable=code == 429 or code >= 500) from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SubtitleAIError("AI_NETWORK", f"The AI service could not be reached ({type(exc).__name__}).", retryable=True) from None
    except json.JSONDecodeError:
        raise SubtitleAIError("AI_BAD_ANSWER", "The AI service sent an unreadable answer.", retryable=True) from None


# tests replace these (no network, no waiting in the test suite)
transport = _post
RETRY_PAUSE = 4.0


def _with_retries(call, tries: int = 3):
    """A busy service (5xx, network) is asked again after 4 / 8 s; a rate limit (429) waits 4× longer (16 / 32 s) — seen live on the first run."""
    for attempt in range(tries):
        try:
            return call()
        except SubtitleAIError as exc:
            if not exc.retryable or attempt == tries - 1:
                raise
            time.sleep(RETRY_PAUSE * (attempt + 1) * (4 if exc.code == "AI_HTTP_429" else 1))
    raise AssertionError("unreachable")


def is_transient(exc: SubtitleAIError) -> bool:
    """A busy / unreachable service (HTTP 5xx, a rate limit that is not the used-up quota, network): asking again a bit later helps."""
    return exc.code in ("AI_NETWORK", "AI_HTTP_429") or exc.code.startswith("AI_HTTP_5")


def _gemini_models() -> list[str]:
    """The "strong" order: the configured subtitle model, then the general one, then the fast and the fallback model."""
    return [m for m in dict.fromkeys([settings.SUBTITLE_AI_MODEL, settings.GEMINI_MODEL, settings.SUBTITLE_FAST_MODEL, settings.GEMINI_FALLBACK_MODEL]) if m]


def fast_models() -> list[str]:
    """The fast model first, then the strong order (the translator: text only, a slower model is acceptable)."""
    return [m for m in dict.fromkeys([settings.SUBTITLE_FAST_MODEL, *_gemini_models()]) if m]


def fast_only() -> list[str]:
    """The listener's and the proofreader's normal path: ONLY the fast model. A busy fast model must not fall through to the slow strong model
    (minutes per piece, seen live 2026-11-19); the job waits and asks the fast model again instead. Empty SUBTITLE_FAST_MODEL = the strong order."""
    return [settings.SUBTITLE_FAST_MODEL] if settings.SUBTITLE_FAST_MODEL else _gemini_models()


# structured output: Gemini has to answer exactly this shape (no prose, no bare list, strings escaped)
SEGMENT_SCHEMA = {"type": "OBJECT", "properties": {
    "language": {"type": "STRING"},
    "segments": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
        "start": {"type": "NUMBER"}, "end": {"type": "NUMBER"}, "speaker": {"type": "STRING"}, "text": {"type": "STRING"}},
        "required": ["start", "end", "text"]}}},
    "required": ["segments"]}
LINES_SCHEMA = {"type": "OBJECT", "properties": {"t": {"type": "ARRAY", "items": {"type": "STRING"}}}, "required": ["t"]}


def _gemini(parts: list[dict], max_tokens: int = 16384, schema: dict | None = None, models: list[str] | None = None,
            tries: int = 3) -> tuple[dict | list, str]:
    """One Gemini call (JSON answer, shape forced by `schema`) with retries, falling back to the next model on a lasting error. → (answer, model)."""
    if not settings.GEMINI_API_KEY:
        raise SubtitleAIError("AI_NOT_CONFIGURED", "GEMINI_API_KEY is not set on the server.")
    config = {"temperature": 0, "responseMimeType": "application/json", "maxOutputTokens": max_tokens}
    if schema:
        config["responseSchema"] = schema
    body = json.dumps({"contents": [{"parts": parts}], "generationConfig": config}).encode("utf-8")
    headers = {"Content-Type": "application/json", "x-goog-api-key": settings.GEMINI_API_KEY}
    last: SubtitleAIError | None = None
    for model in models or _gemini_models():
        try:
            answer = _with_retries(lambda: transport(GEMINI_ENDPOINT.format(model=model), body, headers), tries)
            candidate = (answer.get("candidates") or [{}])[0]
            if candidate.get("finishReason") == "MAX_TOKENS":
                raise SubtitleAIError("AI_ANSWER_TOO_LONG", "The AI answer was cut off (too long).", retryable=False)
            text = "".join(p.get("text", "") for p in (candidate.get("content") or {}).get("parts") or [])
            if not text:
                reason = candidate.get("finishReason") or (answer.get("promptFeedback") or {}).get("blockReason") or "empty"
                raise SubtitleAIError("AI_EMPTY_ANSWER", f"The AI gave no text ({reason}).", retryable=True)
            return extract_json(text), model
        except SubtitleAIError as exc:
            if exc.code in ("AI_KEY_REJECTED", "AI_NOT_CONFIGURED", "AI_ANSWER_TOO_LONG"):
                raise
            last = exc
            log.warning("gemini %s failed: %s", model, exc.code)
    raise last or SubtitleAIError("AI_NOT_CONFIGURED", "No Gemini model is configured.")


# ---------------- speech-to-text ----------------

TRANSCRIBE_PROMPT = """You are a professional film subtitler. Transcribe the speech in this audio clip ({seconds:.1f} seconds long) into subtitles.
Language: {language_rule}
Rules:
- Write exactly what is spoken, in the spoken language with its correct spelling and script (German: ä, ö, ü, ß, correct capital letters and punctuation; Uzbek: Latin script; Russian: Cyrillic). Do not translate, summarise or correct the speakers.
- One segment = one subtitle: at most about 7 seconds and at most two lines of about 42 characters. Split long sentences at natural pauses.
- Start a new segment whenever the speaker changes. Label the speakers "A", "B", "C" … consistently within this clip.
- "start" / "end": seconds from the beginning of THIS clip with milliseconds (e.g. 12.345) — the moment the words begin and end.
- Ignore music, noise and sound effects (no descriptions such as [music]). Unclear words: "[…]". If nobody speaks, return no segments.
Answer ONLY with JSON: {{"language": "<ISO 639-1 code of the spoken language>", "segments": [{{"start": 0.0, "end": 0.0, "speaker": "A", "text": "..."}}]}}"""


@dataclass
class Transcript:
    language: str | None
    segments: list[dict]
    model: str


class GeminiSTT:
    name = "gemini"

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise SubtitleAIError("AI_NOT_CONFIGURED", "Speech-to-text needs GEMINI_API_KEY on the server.")

    @property
    def model(self) -> str:
        return fast_models()[0]

    def transcribe(self, data: bytes, mime: str, language: str | None, seconds: float, strong: bool = False) -> Transcript:
        """`strong`: the checker agent asks again with the strong model first (the normal path starts with the fast one)."""
        if len(data) > MAX_INLINE_BYTES:
            raise SubtitleAIError("AUDIO_PIECE_TOO_LARGE", "An audio piece is larger than the AI service accepts.")
        import base64

        rule = (f"The audio is in {PROMPT_NAMES[language]}; transcribe it in {PROMPT_NAMES[language]}." if language in PROMPT_NAMES
                else "Detect the spoken language (expected: German, English, Uzbek or Russian) and transcribe in it.")
        parts = [{"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode("ascii")}},
                 {"text": TRANSCRIBE_PROMPT.format(seconds=seconds, language_rule=rule)}]
        # fast: only the fast model, asked patiently (a busy moment is common); strong: the strong order, one try per model (minutes per answer)
        raw, model = _gemini(parts, schema=SEGMENT_SCHEMA, models=_gemini_models() if strong else fast_only(), tries=1 if strong else 5)
        raw = as_object(raw, "segments")
        return Transcript(normalize_language(raw.get("language")) or language, parse_segments(raw, seconds), model)


class OpenAISTT:
    name = "openai"

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise SubtitleAIError("AI_NOT_CONFIGURED", "Speech-to-text with Whisper needs OPENAI_API_KEY on the server.")

    model = "whisper-1"

    def transcribe(self, data: bytes, mime: str, language: str | None, seconds: float, strong: bool = False) -> Transcript:
        boundary = "----vizu" + uuid.uuid4().hex
        fields = {"model": self.model, "response_format": "verbose_json", "temperature": "0", "timestamp_granularities[]": "segment"}
        if language in LANGUAGES:
            fields["language"] = language
        body = b"".join(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items())
        body += (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="piece.mp3"\r\nContent-Type: {mime}\r\n\r\n').encode() + data
        body += f"\r\n--{boundary}--\r\n".encode()
        headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": f"multipart/form-data; boundary={boundary}"}
        raw = _with_retries(lambda: transport(OPENAI_TRANSCRIBE_ENDPOINT, body, headers))
        return Transcript(normalize_language(raw.get("language")) or language, parse_segments(raw, seconds), self.model)


class FakeSTT:
    """Local test stack only (APP_ENV=test): a fixed, clearly marked text every 3 s — lets the E2E tests run the whole flow without a key."""

    name = "fake"
    model = "test-fake"

    def __init__(self):
        if settings.APP_ENV != "test":
            raise SubtitleAIError("AI_NOT_CONFIGURED", "The test provider is only available in the local test environment.")

    def transcribe(self, data: bytes, mime: str, language: str | None, seconds: float, strong: bool = False) -> Transcript:
        lang = language if language in LANGUAGES else "de"
        words = {"de": "testsatz", "en": "Test sentence", "uz": "Sinov gapi", "ru": "Тестовая фраза"}[lang]  # "testsatz": the test proofreader capitalises it
        segments = [{"start": t + 0.2, "end": min(t + 2.6, seconds), "text": f"{words} {int(t // 3) + 1}", "speaker": "A" if int(t // 3) % 2 == 0 else "B"}
                    for t in range(0, max(0, int(seconds) - 1), 3)]
        return Transcript(lang, [s for s in segments if s["end"] > s["start"]], self.model)


STT_PROVIDERS = {"gemini": GeminiSTT, "openai": OpenAISTT, "fake": FakeSTT}


def stt_provider():
    name = (settings.SUBTITLE_STT_PROVIDER or "gemini").strip().lower()
    if name not in STT_PROVIDERS:
        raise SubtitleAIError("AI_NOT_CONFIGURED", f"Unknown SUBTITLE_STT_PROVIDER '{name}'.")
    return STT_PROVIDERS[name]()


# ---------------- translation ----------------

TRANSLATE_PROMPT = """Translate these film subtitles from {source} to {target}.
- Keep the meaning, tone and register; write natural, short {target} subtitles that are easy to read.
- Exactly one translation per input entry, in the same order: {count} entries in, {count} entries out. Never merge or split entries.
- Keep a line break ("\\n") inside an entry where it helps reading. Names stay as they are. No notes, no explanations.
Input (JSON array): {lines}
Answer ONLY with JSON: {{"t": ["...", "..."]}}"""


class GeminiTranslator:
    name = "gemini"

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise SubtitleAIError("AI_NOT_CONFIGURED", "Translation needs GEMINI_API_KEY on the server.")

    @property
    def model(self) -> str:
        return fast_models()[0]

    def translate(self, lines: list[str], source: str, target: str) -> list[str]:
        prompt = TRANSLATE_PROMPT.format(source=PROMPT_NAMES.get(source, source), target=PROMPT_NAMES.get(target, target), count=len(lines),
                                         lines=json.dumps(lines, ensure_ascii=False))
        raw, _ = _gemini([{"text": prompt}], schema=LINES_SCHEMA, models=fast_models())
        out = as_object(raw, "t").get("t")
        if not isinstance(out, list) or len(out) != len(lines):
            raise SubtitleAIError("AI_TRANSLATION_COUNT", f"The translation had {len(out) if isinstance(out, list) else 0} entries for {len(lines)}.", retryable=True)
        return [subs.clean_text(str(x)) for x in out]


class GoogleTranslator:
    name = "google"
    model = "cloud-translation-v2"

    def __init__(self):
        if not settings.GOOGLE_TRANSLATE_API_KEY:
            raise SubtitleAIError("AI_NOT_CONFIGURED", "Google Translate needs GOOGLE_TRANSLATE_API_KEY on the server.")

    def translate(self, lines: list[str], source: str, target: str) -> list[str]:
        body = json.dumps({"q": lines, "source": source, "target": target, "format": "text"}).encode("utf-8")
        headers = {"Content-Type": "application/json", "x-goog-api-key": settings.GOOGLE_TRANSLATE_API_KEY}
        raw = _with_retries(lambda: transport(GOOGLE_TRANSLATE_ENDPOINT, body, headers, 120))
        out = [t.get("translatedText", "") for t in (raw.get("data") or {}).get("translations") or []]
        if len(out) != len(lines):
            raise SubtitleAIError("AI_TRANSLATION_COUNT", f"Google Translate answered {len(out)} entries for {len(lines)}.", retryable=True)
        import html

        return [subs.clean_text(html.unescape(x)) for x in out]


class FakeTranslator:
    name = "fake"
    model = "test-fake"

    def __init__(self):
        if settings.APP_ENV != "test":
            raise SubtitleAIError("AI_NOT_CONFIGURED", "The test provider is only available in the local test environment.")

    def translate(self, lines: list[str], source: str, target: str) -> list[str]:
        return [f"[{target}] {line}" for line in lines]


TRANSLATORS = {"gemini": GeminiTranslator, "google": GoogleTranslator, "fake": FakeTranslator}


def translator():
    name = (settings.SUBTITLE_TRANSLATE_PROVIDER or "gemini").strip().lower()
    if name not in TRANSLATORS:
        raise SubtitleAIError("AI_NOT_CONFIGURED", f"Unknown SUBTITLE_TRANSLATE_PROVIDER '{name}'.")
    return TRANSLATORS[name]()


# ---------------- proofreading (the "Korrektor" agent) ----------------

PROOFREAD_PROMPT = """You proofread German film subtitles that a speech recogniser wrote. Correct ONLY clear mistakes:
spelling, capital letters (German nouns!), umlauts and ß (e.g. "fur" -> "für", "dass"/"das"), punctuation, and a word that is obviously misheard
in its context. Do not rewrite style, do not shorten, do not translate, keep colloquial speech as it is.
Exactly one output entry per input entry, same order: {count} entries in, {count} entries out. Keep "\\n" line breaks.
Input (JSON array): {lines}
Answer ONLY with JSON: {{"t": ["...", "..."]}}"""


class GeminiProofreader:
    name = "gemini"

    @property
    def model(self) -> str:
        return fast_only()[0]

    def proofread(self, lines: list[str]) -> list[str]:
        prompt = PROOFREAD_PROMPT.format(count=len(lines), lines=json.dumps(lines, ensure_ascii=False))
        raw, _ = _gemini([{"text": prompt}], schema=LINES_SCHEMA, models=fast_only(), tries=4)
        out = as_object(raw, "t").get("t")
        if not isinstance(out, list) or len(out) != len(lines):
            raise SubtitleAIError("AI_TRANSLATION_COUNT", "The proofreading did not keep the number of lines.", retryable=True)
        return [subs.clean_text(str(x)) or original for x, original in zip(out, lines)]


class FakeProofreader:
    """Local test stack only: puts the German noun of the test text in its proper form ("testsatz" → "Testsatz") — a visible, harmless change."""

    name = "fake"
    model = "test-fake"

    def proofread(self, lines: list[str]) -> list[str]:
        return [line.replace("testsatz", "Testsatz") for line in lines]


def proofreader():
    """The proofreader agent, or None when it is switched off or no AI is set up (the subtitles are then used as heard)."""
    if not settings.SUBTITLE_PROOFREAD:
        return None
    name = (settings.SUBTITLE_STT_PROVIDER or "gemini").strip().lower()
    if name == "fake":
        return FakeProofreader() if settings.APP_ENV == "test" else None
    return GeminiProofreader() if settings.GEMINI_API_KEY else None


def status() -> dict:
    """What the admin panel shows before a job is started: which services are set up (never a key), and whether ffmpeg exists."""
    from app.services.audio_files.service import find_tool

    def probe(factory, setting: str) -> dict:
        name = (getattr(settings, setting) or "gemini").strip().lower()
        try:
            provider = factory()
            return {"provider": name, "configured": True, "model": getattr(provider, "model", None), "message": None}
        except SubtitleAIError as exc:
            return {"provider": name, "configured": False, "model": None, "message": str(exc)}

    proof = proofreader()
    return {"speech_to_text": probe(stt_provider, "SUBTITLE_STT_PROVIDER"), "translation": probe(translator, "SUBTITLE_TRANSLATE_PROVIDER"),
            "ffmpeg": bool(find_tool("ffmpeg")), "languages": list(LANGUAGES), "chunk_seconds": settings.SUBTITLE_CHUNK_SECONDS,
            "agents": {"fast_model": settings.SUBTITLE_FAST_MODEL, "strong_model": _gemini_models()[0] if _gemini_models() else None,
                       "proofread": proof is not None, "proofread_model": getattr(proof, "model", None)}}
