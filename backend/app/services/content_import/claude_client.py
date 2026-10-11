"""Optional server-side generation of a content DRAFT with Claude.

Only active when ANTHROPIC_API_KEY is set. The result is never stored or
published here — it goes through the same validation and preview as an
uploaded JSON file, and an admin commits and publishes it."""

import json
import urllib.error
import urllib.request

from fastapi import HTTPException

from app.core.config import settings
from app.core.logging.logger import logger
from app.services.content_import import guide

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
TIMEOUT_SECONDS = 180


def is_configured() -> bool:
    return bool(settings.ANTHROPIC_API_KEY)


def status() -> dict:
    return {
        "claude_api_configured": is_configured(),
        "model": settings.ANTHROPIC_MODEL if is_configured() else None,
        "note": None if is_configured() else "ANTHROPIC_API_KEY ist nicht gesetzt — JSON-Import und manuelle Bearbeitung nutzen.",
    }


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in the answer")
    return json.loads(text[start : end + 1])


def _post(payload: dict) -> dict:
    request = urllib.request.Request(
        ANTHROPIC_URL,
        data=json.dumps(payload).encode(),
        headers={"x-api-key": settings.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310 — fixed https URL
        return json.loads(response.read())


def generate_document(level: str, module: int, lesson: int, topic: str, skills: list[str], notes: str | None) -> dict:
    if not is_configured():
        raise HTTPException(status_code=503, detail="CLAUDE_NOT_CONFIGURED")
    instructions = guide.prompt(level).replace("<MODUL>", str(module)).replace("<LEKTION>", str(lesson)).replace("<THEMA>", topic)
    request_text = (
        f"{instructions}\nErzeuge Aufgaben für diese Fertigkeiten: {', '.join(skills)}."
        + (f"\nZusätzliche Hinweise: {notes}" if notes else "")
        + f"\nBeispiel für das Format:\n{json.dumps(guide.example(level), ensure_ascii=False)}"
    )
    payload = {"model": settings.ANTHROPIC_MODEL, "max_tokens": 16000, "messages": [{"role": "user", "content": request_text}]}
    try:
        data = _post(payload)
    except urllib.error.HTTPError as exc:
        logger.warning("Claude generation failed: HTTP %s", exc.code)
        raise HTTPException(status_code=502, detail=f"CLAUDE_HTTP_{exc.code}") from None
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.warning("Claude generation failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="CLAUDE_UNAVAILABLE") from None
    text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
    try:
        return _extract_json(text)
    except (ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=502, detail="CLAUDE_INVALID_JSON") from None
