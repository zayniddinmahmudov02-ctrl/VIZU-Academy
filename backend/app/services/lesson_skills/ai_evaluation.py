"""AI evaluation of lesson Schreiben / Sprechen submissions.

Pipeline (tasks with ai_evaluation_enabled only — every other task keeps the
existing teacher grading untouched):

  Schreiben: submit (SUBMITTED = pending_evaluation) -> claim (EVALUATING)
             -> Gemini (JSON, temperature 0) -> server-side validation
             -> GRADED with score, or EVALUATION_FAILED (text kept, retry).
  Sprechen:  upload (audio stored) -> claim -> speech-to-text (verbatim
             transcript + what the model HEARD) -> Gemini -> validation
             -> GRADED / EVALUATION_FAILED (audio kept, retry).

Guarantees:
* The score is computed HERE from the validated per-criterion points — never
  taken from the AI's own total and never from the client.
* Every criterion must come back as an integer within its maximum; anything
  malformed fails the run (status EVALUATION_FAILED), it is never guessed.
* Quoted errors must literally occur in the student's text / transcript.
* Pronunciation is only scored when the speech-to-text model actually
  listened to the audio (Gemini returns observations about what it heard);
  otherwise it is "not_assessed", excluded from the maximum, and the result
  says so.
* Claiming is a conditional UPDATE, so concurrent / repeated requests can
  never evaluate (or count) one submission twice. A run stuck in EVALUATING
  for longer than STALE_AFTER may be claimed again.
* Every run (and every manual override) is appended to ai_evaluations; the
  API key and the student's text never appear in logs."""

import json
import math
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging.logger import logger
from app.models.lesson_skill import (
    EVAL_FAILED,
    EVAL_KIND_SPEAKING,
    EVAL_KIND_WRITING,
    EVAL_SOURCE_AI,
    EVAL_SOURCE_OVERRIDE,
    EVAL_SUCCEEDED,
    AiEvaluation,
)
from app.models.speaking import Speaking
from app.models.student_speaking import StudentSpeaking
from app.models.student_writing import StudentWriting
from app.models.writing import Writing
from app.services.mock_exam.ai_service import GEMINI_ENDPOINT, AIServiceError, _extract_json, _require_api_key

STATUS_SUBMITTED = "SUBMITTED"
STATUS_EVALUATING = "EVALUATING"
STATUS_GRADED = "GRADED"
STATUS_EVALUATION_FAILED = "EVALUATION_FAILED"
STALE_AFTER = timedelta(minutes=10)
MAX_ERRORS = 10

DEFAULT_WRITING_RUBRIC = [
    {"key": "task", "name": "Topshiriqni bajarish", "max": 25},
    {"key": "grammar", "name": "Grammatika", "max": 25},
    {"key": "vocabulary", "name": "Lug'at va mavzuga moslik", "max": 20},
    {"key": "coherence", "name": "Gaplar tuzilishi va mantiqiy bog'lanish", "max": 15},
    {"key": "spelling", "name": "Imlo va tinish belgilari", "max": 15},
]
DEFAULT_SPEAKING_RUBRIC = [
    {"key": "content", "name": "Savolga javob va mazmun", "max": 25},
    {"key": "grammar", "name": "Grammatika", "max": 20},
    {"key": "vocabulary", "name": "Lug'at", "max": 20},
    {"key": "pronunciation", "name": "Talaffuz", "max": 20},
    {"key": "fluency", "name": "Ravonlik va tushunarlilik", "max": 15},
]
PRONUNCIATION_KEY = "pronunciation"

LANGUAGE_NAMES = {"uz": "o'zbek (lotin yozuvida)", "de": "nemis", "en": "ingliz", "ru": "rus"}
NOT_ASSESSED_NOTE = {
    "uz": "Talaffuz baholanmadi: audio tahlili mavjud emas, faqat transkript asosida talaffuzni ishonchli baholab bo'lmaydi.",
    "de": "Aussprache nicht bewertet: keine Audioanalyse verfügbar, aus dem Transkript allein ist sie nicht verlässlich zu beurteilen.",
}


class InvalidAIResult(ValueError):
    """The AI answer does not match the required structure."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def round_half_up(value: float) -> int:
    return int(math.floor(value + 0.5))


def _normalise(value: str) -> str:
    return " ".join(str(value).split())


# ============================================================
# Rubric
# ============================================================


def validate_rubric(rubric) -> list[dict]:
    """Admin-defined rubric: [{"key","name","max"}...], keys unique slugs."""
    if not isinstance(rubric, list) or not 1 <= len(rubric) <= 10:
        raise ValueError("Rubric needs 1-10 criteria.")
    out, keys = [], set()
    for item in rubric:
        if not isinstance(item, dict):
            raise ValueError("Each criterion must be an object.")
        key = str(item.get("key", "")).strip().lower()
        name = str(item.get("name", "")).strip()
        try:
            maximum = int(item.get("max"))
        except (TypeError, ValueError):
            raise ValueError("Criterion max must be an integer.") from None
        if not key.replace("_", "").isalnum() or len(key) > 40 or key in keys:
            raise ValueError(f"Invalid or duplicate criterion key '{key}'.")
        if not name or len(name) > 120 or not 1 <= maximum <= 100:
            raise ValueError("Criterion needs a name and a max of 1-100 points.")
        keys.add(key)
        out.append({"key": key, "name": name, "max": maximum})
    return out


def effective_rubric(task, default: list[dict]) -> list[dict]:
    try:
        return validate_rubric(task.rubric) if task.rubric else [dict(c) for c in default]
    except ValueError:
        return [dict(c) for c in default]


# ============================================================
# Validation (pure, unit-tested)
# ============================================================


def verify_errors(source_text: str, raw_errors) -> list[dict]:
    haystack = _normalise(source_text)
    out, seen = [], set()
    for item in raw_errors if isinstance(raw_errors, list) else []:
        if not isinstance(item, dict):
            continue
        original = _normalise(item.get("original", ""))
        correction = _normalise(item.get("correction", ""))
        if not original or not correction or original == correction or original not in haystack or original in seen:
            continue
        seen.add(original)
        out.append({"original": original[:200], "correction": correction[:200], "explanation": str(item.get("explanation", "")).strip()[:400]})
        if len(out) >= MAX_ERRORS:
            break
    return out


def validate_result(raw, rubric: list[dict], source_text: str, assessed_keys: set[str], language: str = "uz") -> dict:
    """Builds the stored result from the AI JSON. Raises InvalidAIResult if
    any assessed criterion is missing or not an integer."""
    if not isinstance(raw, dict):
        raise InvalidAIResult("not an object")
    by_key = {}
    for item in raw.get("criteria") or []:
        if isinstance(item, dict) and item.get("key") is not None:
            by_key[str(item["key"]).strip().lower()] = item
    criteria, total, maximum = [], 0, 0
    for c in rubric:
        if c["key"] not in assessed_keys:
            criteria.append({**c, "score": None, "status": "not_assessed", "comment": NOT_ASSESSED_NOTE.get(language, NOT_ASSESSED_NOTE["uz"])})
            continue
        item = by_key.get(c["key"])
        if item is None:
            raise InvalidAIResult(f"criterion '{c['key']}' missing")
        value = item.get("score")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or float(value) != int(value):
            raise InvalidAIResult(f"criterion '{c['key']}' score is not an integer")
        score = max(0, min(c["max"], int(value)))
        total += score
        maximum += c["max"]
        criteria.append({**c, "score": score, "status": "assessed", "comment": str(item.get("comment", "")).strip()[:600]})
    if maximum == 0:
        raise InvalidAIResult("nothing assessed")
    strengths = [str(s).strip()[:300] for s in (raw.get("strengths") or []) if str(s).strip()][:5]
    return {
        "criteria": criteria,
        "points": total,
        "max_points": maximum,
        "score": max(0, min(100, round_half_up(total / maximum * 100))),
        "strengths": strengths,
        "errors": verify_errors(source_text, raw.get("errors")),
        "recommendation": str(raw.get("recommendation", "")).strip()[:800],
        "summary": str(raw.get("summary", "")).strip()[:1200],
        "limitations": [NOT_ASSESSED_NOTE.get(language, NOT_ASSESSED_NOTE["uz"])] if len(assessed_keys) < len(rubric) else [],
    }


# ============================================================
# Prompts
# ============================================================


def _rubric_lines(rubric: list[dict], assessed: set[str]) -> str:
    return "\n".join(f'- "{c["key"]}" — {c["name"]}: 0-{c["max"]} ball' for c in rubric if c["key"] in assessed)


def writing_prompt(task: Writing, text_value: str, rubric: list[dict]) -> str:
    lang = LANGUAGE_NAMES.get(task.feedback_language, task.feedback_language)
    assessed = {c["key"] for c in rubric}
    extra = f"\nO'qituvchining qo'shimcha ko'rsatmasi: {task.ai_instructions.strip()}" if task.ai_instructions else ""
    helper = f"\nYordamchi so'zlar: {task.helper_words.strip()}" if task.helper_words else ""
    return f"""Sen nemis tili o'qituvchisisan va A1 darajadagi o'quvchining yozma ishini baholaysan.

TOPSHIRIQ: {task.title}
{task.instruction}
So'zlar soni: {task.min_words}-{task.max_words}.{helper}{extra}

BAHOLASH MEZONLARI (butun sonlar):
{_rubric_lines(rubric, assessed)}

Qoidalar:
- Bu A1 darajasi: qisqa, oddiy gaplar kutiladi. B2/C1 talablarini qo'llama. Avvalo topshiriq talabi va mazmun bajarilganini bahola.
- Faqat matnda haqiqatan bor narsani bahola. Matnda yo'q xatoni o'ylab topma.
- "errors": har bir xato uchun "original" — o'quvchi matnidan AYNAN ko'chirilgan qism, "correction" — to'g'ri nemischa variant, "explanation" — qisqa izoh.
- Barcha izohlar (comment, strengths, explanation, recommendation, summary) {lang} tilida bo'lsin; nemischa misollar va tuzatishlar nemis tilida qolsin.
- Umumiy ballni hisoblama — faqat har bir mezon balli.

O'QUVCHI MATNI:
\"\"\"{text_value}\"\"\"

Faqat JSON qaytar:
{{"criteria": [{{"key": "<mezon kaliti>", "score": <butun son>, "comment": "..."}}], "strengths": ["..."], "errors": [{{"original": "...", "correction": "...", "explanation": "..."}}], "recommendation": "...", "summary": "..."}}"""


def speaking_prompt(task: Speaking, transcript: str, observations: dict | None, rubric: list[dict], assessed: set[str]) -> str:
    lang = LANGUAGE_NAMES.get(task.feedback_language, task.feedback_language)
    extra = f"\nO'qituvchining qo'shimcha ko'rsatmasi: {task.ai_instructions.strip()}" if task.ai_instructions else ""
    heard = ""
    if observations:
        heard = (
            "\nAUDIONI TINGLAGAN MODEL KUZATUVLARI (talaffuz va ravonlik uchun manba):\n"
            f"- tushunarlilik: {observations.get('intelligibility', '')}\n"
            f"- talaffuz: {observations.get('pronunciation', '')}\n"
            f"- ravonlik: {observations.get('fluency', '')}"
        )
    return f"""Sen nemis tili o'qituvchisisan va A1 darajadagi o'quvchining og'zaki javobini baholaysan.

TOPSHIRIQ: {task.title} — {task.topic}
{task.instruction}{extra}

BAHOLASH MEZONLARI (butun sonlar):
{_rubric_lines(rubric, assessed)}

Qoidalar:
- Bu A1 darajasi: qisqa, oddiy gaplar kutiladi. Yuqori daraja talablarini qo'llama.
- Transkript so'zma-so'z (xatolar tuzatilmagan). Faqat unda bor narsani bahola.
- "errors": "original" — transkriptdan AYNAN ko'chirilgan qism, "correction" — to'g'ri nemischa variant, "explanation" — qisqa izoh.
- Barcha izohlar {lang} tilida; nemischa misollar nemis tilida qolsin.
- Umumiy ballni hisoblama — faqat har bir mezon balli.{heard}

TRANSKRIPT:
\"\"\"{transcript}\"\"\"

Faqat JSON qaytar:
{{"criteria": [{{"key": "<mezon kaliti>", "score": <butun son>, "comment": "..."}}], "strengths": ["..."], "errors": [{{"original": "...", "correction": "...", "explanation": "..."}}], "recommendation": "...", "summary": "..."}}"""


# ============================================================
# Gemini (JSON mode, temperature 0) — key handling from ai_service
# ============================================================


def call_gemini_json(prompt: str) -> tuple[dict, str]:
    api_key = _require_api_key()
    payload = json.dumps(
        {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    ).encode("utf-8")
    models = [m for m in dict.fromkeys([settings.GEMINI_MODEL, settings.GEMINI_FALLBACK_MODEL]) if m]
    last: Exception | None = None
    for model in models:
        for _ in range(2):
            request = urllib.request.Request(
                GEMINI_ENDPOINT.format(model=model) + f"?key={api_key}",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    body = json.loads(response.read().decode("utf-8"))
                return _extract_json(body["candidates"][0]["content"]["parts"][0]["text"]), model
            except urllib.error.HTTPError as exc:  # never keep the URL (it carries the key)
                last = AIServiceError(f"HTTP {exc.code}")
            except (urllib.error.URLError, KeyError, IndexError, ValueError, AIServiceError, TimeoutError) as exc:
                last = AIServiceError(type(exc).__name__)
    raise AIServiceError(str(last) if last else "AI unavailable")


# ============================================================
# Claiming + persistence
# ============================================================


def _claim(db: Session, table: str, submission_id: UUID) -> bool:
    row = db.execute(
        text(
            f"""UPDATE {table} SET status = :evaluating, updated_at = now()
            WHERE id = :id AND (status IN (:submitted, :failed) OR (status = :evaluating AND updated_at < :stale))
            RETURNING id"""
        ),
        {
            "evaluating": STATUS_EVALUATING,
            "submitted": STATUS_SUBMITTED,
            "failed": STATUS_EVALUATION_FAILED,
            "id": submission_id,
            "stale": _now() - STALE_AFTER,
        },
    ).first()
    db.commit()
    return row is not None


def _fail(db: Session, kind: str, sub, reason: str, model: str | None = None) -> None:
    sub.status = STATUS_EVALUATION_FAILED
    sub.evaluation_error = reason[:500]
    sub.evaluation_runs = (sub.evaluation_runs or 0) + 1
    db.add(AiEvaluation(kind=kind, submission_id=sub.id, user_id=sub.user_id, source=EVAL_SOURCE_AI, status=EVAL_FAILED, error=reason[:500], model=model))
    db.commit()
    logger.warning("AI evaluation failed: kind=%s submission=%s reason=%s", kind, sub.id, reason[:120])


def _succeed(db: Session, kind: str, sub, result: dict, model: str | None) -> None:
    now = _now()
    sub.ai_evaluation = result
    sub.ai_score = result["score"]
    sub.score = result["score"]
    sub.feedback = result["summary"] or None
    sub.status = STATUS_GRADED
    sub.evaluated_at = now
    sub.evaluation_error = None
    sub.evaluation_runs = (sub.evaluation_runs or 0) + 1
    sub.reviewed_by_id = None
    sub.reviewed_at = None
    db.add(AiEvaluation(kind=kind, submission_id=sub.id, user_id=sub.user_id, source=EVAL_SOURCE_AI, status=EVAL_SUCCEEDED, score=result["score"], result=result, model=model))
    db.commit()
    # a graded Schreiben/Sprechen task counts towards lesson completion (same as teacher grading)
    from app.services.learning import refresh_lesson_completion

    task = sub.writing if kind == EVAL_KIND_WRITING else sub.speaking
    if task is not None:
        refresh_lesson_completion(db, sub.user_id, task.lesson_id)
    logger.info("AI evaluation done: kind=%s submission=%s score=%s", kind, sub.id, result["score"])


def evaluate_writing(db: Session, submission_id: UUID) -> None:
    if not _claim(db, "student_writings", submission_id):
        return
    sub = db.get(StudentWriting, submission_id)
    db.refresh(sub)
    task = db.get(Writing, sub.writing_id)
    if task is None or not task.ai_evaluation_enabled:
        sub.status = STATUS_SUBMITTED  # teacher grading
        db.commit()
        return
    rubric = effective_rubric(task, DEFAULT_WRITING_RUBRIC)
    model = None
    try:
        raw, model = call_gemini_json(writing_prompt(task, sub.answer_text, rubric))
        result = validate_result(raw, rubric, sub.answer_text, {c["key"] for c in rubric}, task.feedback_language)
    except (AIServiceError, InvalidAIResult) as exc:
        _fail(db, EVAL_KIND_WRITING, sub, f"{type(exc).__name__}: {exc}", model)
        return
    _succeed(db, EVAL_KIND_WRITING, sub, result, model)


def evaluate_speaking(db: Session, submission_id: UUID, audio_root: Path) -> None:
    from app.services.speech.speech_to_text_service import SpeechToTextError, SpeechToTextService

    if not _claim(db, "student_speakings", submission_id):
        return
    sub = db.get(StudentSpeaking, submission_id)
    db.refresh(sub)
    task = db.get(Speaking, sub.speaking_id)
    if task is None or not task.ai_evaluation_enabled:
        sub.status = STATUS_SUBMITTED
        db.commit()
        return
    rubric = effective_rubric(task, DEFAULT_SPEAKING_RUBRIC)
    previous = sub.ai_evaluation or {}
    observations = previous.get("stt_observations") if isinstance(previous, dict) else None
    if not sub.transcript:
        try:
            stt = SpeechToTextService().transcribe(audio_root / sub.storage_path, sub.content_type, "de", sub.duration_seconds)
        except (SpeechToTextError, OSError, TypeError) as exc:
            _fail(db, EVAL_KIND_SPEAKING, sub, f"SpeechToTextError: {type(exc).__name__}")
            return
        sub.transcript = stt.text or ""
        observations = stt.observations or None
        sub.ai_evaluation = {"stt_observations": observations, "stt_provider": stt.provider, "stt_confidence": stt.confidence}
        db.commit()
    # Pronunciation only when a model really listened to the audio.
    assessed = {c["key"] for c in rubric}
    if not (observations and observations.get("pronunciation")):
        assessed.discard(PRONUNCIATION_KEY)
    transcript = (sub.transcript or "").strip()
    model = None
    try:
        if not transcript:
            raw = {
                "criteria": [{"key": k, "score": 0, "comment": "Yozuvda nutq aniqlanmadi."} for k in assessed],
                "summary": "Yozuvda nemischa nutq aniqlanmadi. Iltimos, javobni qayta yozib yuboring.",
            }
        else:
            raw, model = call_gemini_json(speaking_prompt(task, transcript, observations, rubric, assessed))
        result = validate_result(raw, rubric, transcript, assessed, task.feedback_language)
    except (AIServiceError, InvalidAIResult) as exc:
        _fail(db, EVAL_KIND_SPEAKING, sub, f"{type(exc).__name__}: {exc}", model)
        return
    result["transcript"] = transcript
    result["stt_observations"] = observations
    _succeed(db, EVAL_KIND_SPEAKING, sub, result, model)


# ---- background entry points (own DB session) ----


def run_writing_evaluation(submission_id: UUID) -> None:
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        evaluate_writing(db, submission_id)
    except Exception:  # never let a background job crash silently without a trace
        logger.exception("Writing evaluation crashed: submission=%s", submission_id)
    finally:
        db.close()


def run_speaking_evaluation(submission_id: UUID) -> None:
    from app.db.session import SessionLocal
    from app.services.student_speaking.service import storage

    db = SessionLocal()
    try:
        evaluate_speaking(db, submission_id, storage.ROOT)
    except Exception:
        logger.exception("Speaking evaluation crashed: submission=%s", submission_id)
    finally:
        db.close()


def record_override(db: Session, kind: str, sub, actor_id: UUID, new_score: int, reason: str | None) -> None:
    """Manual correction of an (AI-)graded submission — the previous score
    and the original AI result stay in the history."""
    db.add(
        AiEvaluation(
            kind=kind,
            submission_id=sub.id,
            user_id=sub.user_id,
            source=EVAL_SOURCE_OVERRIDE,
            status=EVAL_SUCCEEDED,
            score=new_score,
            result={"previous_score": sub.score, "ai_score": sub.ai_score, "reason": (reason or "")[:1000]},
            actor_id=actor_id,
        )
    )
