"""SpeechToTextService — provider-agnostic speech-to-text.

    SpeechToTextService().transcribe(audio_path, content_type, language="de")
    -> TranscriptionResult(text, language, duration_seconds, confidence, provider, observations)

Provider = settings.SPEECH_TO_TEXT_PROVIDER ("gemini" | "openai"), model =
settings.SPEECH_TO_TEXT_MODEL (empty = provider default). API keys are read
server-side only.

The transcript is VERBATIM: learner errors are kept (never corrected) —
the evaluation must judge what the student actually said. The Gemini
provider also returns `observations` about what it HEARD (intelligibility,
pronunciation, fluency, pauses), so pronunciation/fluency are not judged
from text alone. Whisper has no such channel; its confidence is derived
from the segment log-probabilities.
"""

import base64
import json
import math
import mimetypes
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import settings
from app.services.mock_exam.ai_service import GEMINI_ENDPOINT, _extract_json

# Inline Gemini requests are limited to ~20 MB; a 3-minute opus answer is ~1.5 MB.
MAX_INLINE_BYTES = 18 * 1024 * 1024

GEMINI_PROMPT = """Du bist ein präzises Transkriptionssystem für Prüfungsaufnahmen von Deutschlernenden.

Transkribiere die Aufnahme WÖRTLICH auf {language_name}:
- Schreibe GENAU, was gesagt wird. Korrigiere KEINE Grammatik-, Wort-, Endungs- oder Satzbaufehler — sie müssen im Transkript stehen bleiben.
- Füge nichts hinzu, fasse nichts zusammen, übersetze nichts. Zahlen dürfen als Ziffern stehen.
- Unverständliche Stellen: [unverständlich]. Längere Pausen/Zögern: „…“.
- Wenn nichts oder keine Sprache zu hören ist: "text" ist "".

Beschreibe außerdem knapp und sachlich, was du HÖRST (nicht den Inhalt):
- "intelligibility": "hoch" | "mittel" | "niedrig" — wie gut ist die Person zu verstehen?
- "pronunciation": 1 Satz zu Aussprache/Intonation (konkrete Laute, falls auffällig).
- "fluency": 1 Satz zu Sprechfluss, Tempo, Pausen, Selbstkorrekturen.

Antworte NUR mit JSON:
{{"text": "...", "language": "{language}", "confidence": <0.0-1.0, wie sicher die Transkription ist>, "intelligibility": "...", "pronunciation": "...", "fluency": "..."}}"""

LANGUAGE_NAMES = {"de": "Deutsch", "en": "Englisch"}


class SpeechToTextError(Exception):
    """Transcription failed (provider/network/format). The caller keeps the
    audio and can retry."""


@dataclass
class TranscriptionResult:
    text: str
    language: str
    duration_seconds: float | None
    confidence: float | None
    provider: str
    observations: dict | None = field(default=None)

    def as_dict(self) -> dict:
        return {
            "text": self.text,
            "language": self.language,
            "duration_seconds": self.duration_seconds,
            "confidence": self.confidence,
        }


def _clamp_confidence(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(min(1.0, max(0.0, number)), 3)


def _clean_mime(content_type: str | None, path: Path) -> str:
    mime = (content_type or "").split(";")[0].strip().lower()
    if not mime:
        mime = mimetypes.guess_type(path.name)[0] or "audio/webm"
    if mime == "audio/x-wav":
        mime = "audio/wav"
    return mime


class _GeminiProvider:
    name = "gemini"

    def __init__(self, model: str):
        if not settings.GEMINI_API_KEY:
            raise SpeechToTextError("GEMINI_API_KEY is not configured.")
        self.models = [m for m in dict.fromkeys([model, settings.GEMINI_MODEL, settings.GEMINI_FALLBACK_MODEL]) if m]

    def transcribe(self, data: bytes, mime: str, language: str, duration: float | None) -> TranscriptionResult:
        if len(data) > MAX_INLINE_BYTES:
            raise SpeechToTextError("Audio too large for transcription.")
        payload = json.dumps(
            {
                "contents": [
                    {
                        "parts": [
                            {"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode("ascii")}},
                            {"text": GEMINI_PROMPT.format(language=language, language_name=LANGUAGE_NAMES.get(language, language))},
                        ]
                    }
                ],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
            }
        ).encode("utf-8")
        last_error: Exception | None = None
        for model in self.models:
            for _try in range(2):
                url = GEMINI_ENDPOINT.format(model=model) + f"?key={settings.GEMINI_API_KEY}"
                request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
                try:
                    with urllib.request.urlopen(request, timeout=120) as response:
                        body = json.loads(response.read().decode("utf-8"))
                    raw = _extract_json(body["candidates"][0]["content"]["parts"][0]["text"])
                    text = " ".join(str(raw.get("text", "")).split())
                    return TranscriptionResult(
                        text=text,
                        language=str(raw.get("language") or language)[:10],
                        duration_seconds=duration,
                        confidence=_clamp_confidence(raw.get("confidence")),
                        provider=f"gemini:{model}",
                        observations={
                            key: str(raw.get(key, "")).strip()[:300]
                            for key in ("intelligibility", "pronunciation", "fluency")
                            if str(raw.get(key, "")).strip()
                        }
                        or None,
                    )
                except urllib.error.HTTPError as exc:
                    last_error = exc
                    if exc.code in (400, 401, 403):  # bad request / key — another try will not help
                        break
                except Exception as exc:  # network, malformed JSON, missing candidates
                    last_error = exc
        raise SpeechToTextError(f"Gemini transcription failed: {last_error}")


class _OpenAIProvider:
    name = "openai"
    ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"

    def __init__(self, model: str):
        if not settings.OPENAI_API_KEY:
            raise SpeechToTextError("OPENAI_API_KEY is not configured.")
        self.model = model or "whisper-1"

    def transcribe(self, data: bytes, mime: str, language: str, duration: float | None) -> TranscriptionResult:
        boundary = "----vizu" + uuid.uuid4().hex
        extension = (mimetypes.guess_extension(mime) or ".webm").lstrip(".")
        fields = {"model": self.model, "language": language, "response_format": "verbose_json", "temperature": "0"}
        body = b"".join(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items()
        )
        body += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="answer.{extension}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
        request = urllib.request.Request(
            self.ENDPOINT,
            data=body,
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise SpeechToTextError(f"OpenAI transcription failed: {exc}") from exc
        segments = raw.get("segments") or []
        logprobs = [s.get("avg_logprob") for s in segments if isinstance(s.get("avg_logprob"), (int, float))]
        confidence = round(math.exp(sum(logprobs) / len(logprobs)), 3) if logprobs else None
        return TranscriptionResult(
            text=" ".join(str(raw.get("text", "")).split()),
            language=str(raw.get("language") or language)[:10],
            duration_seconds=raw.get("duration") or duration,
            confidence=_clamp_confidence(confidence),
            provider=f"openai:{self.model}",
            observations=None,
        )


_PROVIDERS = {"gemini": _GeminiProvider, "openai": _OpenAIProvider}


class SpeechToTextService:
    def __init__(self, provider: str | None = None, model: str | None = None):
        name = (provider or settings.SPEECH_TO_TEXT_PROVIDER or "gemini").strip().lower()
        if name not in _PROVIDERS:
            raise SpeechToTextError(f"Unknown SPEECH_TO_TEXT_PROVIDER '{name}'.")
        self.provider = _PROVIDERS[name](model if model is not None else settings.SPEECH_TO_TEXT_MODEL)

    def transcribe(
        self,
        audio_file: Path | str,
        content_type: str | None = None,
        language: str = "de",
        duration_seconds: float | None = None,
    ) -> TranscriptionResult:
        path = Path(audio_file)
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise SpeechToTextError(f"Audio file not readable: {exc}") from exc
        if not data:
            raise SpeechToTextError("Audio file is empty.")
        return self.provider.transcribe(data, _clean_mime(content_type, path), language, duration_seconds)
