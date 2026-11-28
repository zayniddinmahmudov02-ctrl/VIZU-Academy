"""AI grading of Multilevel Modelltest Schreiben / Sprechen (owner, 2026-11-28). Same provider setup and safety rules as the lesson AI grading
(lesson_skills/ai_evaluation.py: Gemini in JSON mode, temperature 0, the key only from settings, never in logs; the server validates every
number and computes every total itself).

Flow: a closed Schreiben / Sprechen section with work gets ai_status PENDING (multilevel_exam_service._close_section, or a Super Admin
"re-evaluate") → a worker claims it (conditional UPDATE … FOR UPDATE SKIP LOCKED, RUNNING) → evaluate → under the attempt lock the raw score
is stored and converted (apply_ai_result) → the attempt total / level are recomputed → one ai_evaluations row (kind ML_SECTION, source AI).
A Super Admin override is never replaced by an AI result (it only updates auto_score).

* Schreiben: one call with the three Teile; the AI gives Teil 1.1 0–5, Teil 1.2 0–7, Teil 2 0–24 (rounded here to steps of 0.5) with an
  explanation, comments per criterion (Teil 1: Aufgabe, Grammatik, Wortschatz, Satzbau, Kohärenz; Teil 2: Aufgabenbewältigung, Inhalt und
  Argumentation, Struktur und Kohärenz, Grammatik, Wortschatz, Sprachliche Angemessenheit), strengths, mistakes (quoted literally from the
  student's text, else dropped) and recommendations. An empty Teil is 0 without asking the AI. Raw 0–36 → the official table; a raw score
  the table does not cover leaves the section NEEDS_ADMIN (the Super Admin scores it or completes the table).
* Sprechen: every recording is transcribed by a model that LISTENS to the audio (speech.speech_to_text_service, Gemini) and reports what it
  heard about pronunciation / fluency. Six criteria per Teil, 0–5 each; Aussprache and Flüssigkeit are scored only when the model reported
  hearing them — otherwise they are "not assessed" and left out of raw and maximum (never guessed from the transcript). A Teil without a
  recording is 0. Raw → 0–75 linearly (no official table was given).
* Failures (no key, network, malformed answer) → FAILED, retried automatically up to MAX_AUTO_RUNS times (RETRY_AFTER apart); the text /
  audio stays; the Super Admin can re-run or score by hand."""

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.models.mock_attempt_section import AI_FAILED, AI_RUNNING, MockAttemptSection
from app.models.mock_speaking_submission import MockSpeakingSubmission
from app.models.mock_test_attempt import STATUS_GRADED, MockTestAttempt
from app.models.mock_writing_submission import MockWritingSubmission
from app.models.speaking_task import SpeakingTask
from app.models.teil import Teil
from app.models.writing_task import WritingTask
from app.services.mock_exam import multilevel_scoring as scoring

log = logging.getLogger(__name__)

INTERVAL = 15
LOCK_KEY = 7_302_412  # pg advisory lock of this worker (the special-lesson scheduler uses 7_302_411)
PER_ROUND = 3
STALE_AFTER = timedelta(minutes=15)
RETRY_AFTER = timedelta(minutes=5)
MAX_AUTO_RUNS = 3
_started = False
_guard = threading.Lock()

TEIL1_CRITERIA = ("Topshiriq talablari (Aufgabe)", "Grammatik", "Wortschatz", "Satzbau", "Kohärenz")
TEIL2_CRITERIA = ("Aufgabenbewältigung", "Inhalt und Argumentation", "Struktur und Kohärenz", "Grammatik", "Wortschatz",
                  "Sprachliche Angemessenheit")


class InvalidAIResult(ValueError):
    """The AI answer does not have the required structure."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _texts(values, limit: int = 300, count: int = 5) -> list[str]:
    return [str(s).strip()[:limit] for s in (values if isinstance(values, list) else []) if str(s).strip()][:count]


def _half(value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidAIResult("score is not a number")
    return scoring.round_half_up(float(value) * 2) / 2


# ============================================================
# Schreiben
# ============================================================


def _writing_parts(db: Session, s: MockAttemptSection) -> list[dict]:
    """[{key, title, max, task, word_limit, answer}] for every Schreiben Teil of the section's Kompetenz."""
    teile = list(db.scalars(select(Teil).where(Teil.kompetenz_id == s.kompetenz_id).order_by(Teil.sort_order)))
    answers = {w.writing_task_id: w for w in db.scalars(select(MockWritingSubmission).where(MockWritingSubmission.attempt_id == s.attempt_id))}
    parts = []
    for teil in teile:
        key = scoring.schreiben_teil_key(teil.title)
        if key is None:
            raise InvalidAIResult(f"unknown Schreiben Teil {teil.title!r}")
        tasks = list(db.scalars(select(WritingTask).where(WritingTask.teil_id == teil.id)))
        answer = " ".join((answers[tasks[0].id].answer_text or "").split()) if tasks and tasks[0].id in answers else ""
        for t in tasks[1:]:
            if t.id in answers:
                answer = (answer + "\n" + (answers[t.id].answer_text or "")).strip()
        parts.append({"key": key, "title": teil.title, "max": scoring.SCHREIBEN_TEIL_MAX[key],
                      "task": "\n".join(t.task_text for t in tasks)[:4000], "word_limit": tasks[0].word_limit if tasks else None,
                      "answer": answer[:8000]})
    return parts


def schreiben_prompt(parts: list[dict]) -> str:
    blocks = []
    for p in parts:
        criteria = TEIL2_CRITERIA if p["key"] == "2" else TEIL1_CRITERIA
        words = f" (taxminan {p['word_limit']} so'z)" if p["word_limit"] else ""
        blocks.append(f"""=== TEIL {p['key']} — maksimal {p['max']:g} ball{words}
Mezonlar: {", ".join(criteria)}
TOPSHIRIQ:
\"\"\"{p['task']}\"\"\"
O'QUVCHI JAVOBI:
\"\"\"{p['answer']}\"\"\"""")
    return f"""Sen nemis tili imtihoni (Multilevel / Zertifikat, B1–C1) bo'yicha tajribali baholovchisan. O'quvchining Schreiben ishini bahola.

Qoidalar:
- Har bir Teil uchun bitta "score" ber: 0 dan shu Teil maksimumigacha, 0.5 qadam bilan (Teil 1.1: 0–5, Teil 1.2: 0–7, Teil 2: 0–24).
- "explanation": nima uchun aynan shu ball (topshiriq bajarilgani, til sifati) — 2–4 gap.
- "criteria": har bir mezon uchun {{"name": ..., "comment": ...}} — qisqa, aniq.
- "mistakes": {{"original": o'quvchi matnidan AYNAN ko'chirilgan qism, "correction": to'g'ri nemischa, "explanation": qisqa izoh}} — faqat haqiqiy xatolar.
- "strengths", "recommendations": qisqa ro'yxatlar.
- Faqat matnda bor narsani bahola; topshiriqqa javob bo'lmasa yoki mavzudan chetda bo'lsa past ball ber.
- Barcha izohlar o'zbek tilida (lotin yozuvida); nemischa misollar nemis tilida qolsin. Umumiy ballni hisoblama.

{chr(10).join(blocks)}

Faqat JSON qaytar:
{{"teile": [{{"teil": "1.1", "score": 0, "explanation": "...", "criteria": [{{"name": "...", "comment": "..."}}], "strengths": ["..."], "mistakes": [{{"original": "...", "correction": "...", "explanation": "..."}}], "recommendations": ["..."]}}], "summary": "...", "strengths": ["..."], "mistakes": ["..."], "recommendations": ["..."]}}"""


def validate_schreiben(raw, parts: list[dict]) -> dict:
    from app.services.lesson_skills.ai_evaluation import verify_errors

    if not isinstance(raw, dict):
        raise InvalidAIResult("not an object")
    by_key = {}
    for item in raw.get("teile") or []:
        if isinstance(item, dict) and item.get("teil") is not None:
            by_key[str(item["teil"]).replace("Teil", "").strip().replace(",", ".")] = item
    teile, total, maximum = [], 0.0, 0.0
    for p in parts:
        maximum += p["max"]
        if not p["answer"]:
            teile.append({"teil": p["key"], "title": p["title"], "score": 0.0, "max": p["max"], "explanation": "Javob yozilmagan — 0 ball.",
                          "criteria": [], "strengths": [], "mistakes": [], "recommendations": [], "answered": False})
            continue
        item = by_key.get(p["key"])
        if item is None:
            raise InvalidAIResult(f"Teil {p['key']} missing")
        score = _half(item.get("score"))
        if not 0 <= score <= p["max"]:
            raise InvalidAIResult(f"Teil {p['key']} score {score} outside 0–{p['max']:g}")
        total += score
        teile.append({"teil": p["key"], "title": p["title"], "score": score, "max": p["max"],
                      "explanation": str(item.get("explanation", "")).strip()[:1200],
                      "criteria": [{"name": str(c.get("name", "")).strip()[:80], "comment": str(c.get("comment", "")).strip()[:500]}
                                   for c in (item.get("criteria") or []) if isinstance(c, dict)][:8],
                      "strengths": _texts(item.get("strengths")), "mistakes": verify_errors(p["answer"], item.get("mistakes")),
                      "recommendations": _texts(item.get("recommendations")), "answered": True})
    if maximum <= 0:
        raise InvalidAIResult("no Teil")
    raw36 = total if maximum == scoring.SCHREIBEN_RAW_MAX else _half(total * scoring.SCHREIBEN_RAW_MAX / maximum)
    return {"kind": "SCHREIBEN", "raw": raw36, "raw_max": scoring.SCHREIBEN_RAW_MAX, "teile": teile,
            "summary": str(raw.get("summary", "")).strip()[:1500], "strengths": _texts(raw.get("strengths")),
            "mistakes": _texts(raw.get("mistakes")), "recommendations": _texts(raw.get("recommendations")), "limitations": []}


# ============================================================
# Sprechen
# ============================================================


def _speaking_parts(db: Session, s: MockAttemptSection) -> list[dict]:
    teile = list(db.scalars(select(Teil).where(Teil.kompetenz_id == s.kompetenz_id).order_by(Teil.sort_order)))
    subs = {r.speaking_task_id: r for r in db.scalars(select(MockSpeakingSubmission).where(MockSpeakingSubmission.attempt_id == s.attempt_id))}
    parts = []
    for teil in teile:
        tasks = list(db.scalars(select(SpeakingTask).where(SpeakingTask.teil_id == teil.id)))
        sub = next((subs[t.id] for t in tasks if t.id in subs), None)
        parts.append({"key": teil.title, "title": teil.title, "task": "\n".join(t.task_text for t in tasks)[:3000], "submission": sub})
    return parts


def _transcribe(parts: list[dict]) -> None:
    from app.services.mock_exam.multilevel_exam_service import AUDIO_MEDIA, speaking_storage
    from app.services.speech.speech_to_text_service import SpeechToTextService

    service = SpeechToTextService()
    for p in parts:
        sub = p["submission"]
        p["transcript"], p["observations"] = "", None
        if sub is None:
            continue
        path = speaking_storage._inside_root(sub.audio_url)
        result = service.transcribe(path, AUDIO_MEDIA.get(path.suffix.lstrip("."), "audio/webm"), "de", None)
        p["transcript"], p["observations"] = (result.text or "").strip()[:6000], result.observations or None


def sprechen_prompt(parts: list[dict]) -> str:
    names = ", ".join(f'"{k}" ({n})' for k, n in scoring.SPRECHEN_CRITERIA)
    blocks = []
    for p in parts:
        if not p["submission"]:
            continue
        heard = p["observations"] or {}
        listened = (f"\nAUDIONI TINGLAGAN MODEL KUZATUVLARI: tushunarlilik: {heard.get('intelligibility', '')}; talaffuz: {heard.get('pronunciation', '')}; "
                    f"ravonlik: {heard.get('fluency', '')}") if heard else "\nAudio kuzatuvi yo'q: Aussprache va Flüssigkeit BAHOLANMAYDI (ularni yozma)."
        blocks.append(f"""=== {p['key']}
TOPSHIRIQ:
\"\"\"{p['task']}\"\"\"
TRANSKRIPT (so'zma-so'z):
\"\"\"{p['transcript']}\"\"\"{listened}""")
    return f"""Sen nemis tili og'zaki imtihoni (Multilevel / Zertifikat, B1–C1) bo'yicha tajribali baholovchisan. O'quvchining Sprechen javoblarini bahola.

Har bir Teil uchun mezonlar (har biri 0–5 butun son): {names}.
Qoidalar:
- Aussprache va Flüssigkeitni faqat audio kuzatuvlari berilgan Teilda bahola; transkriptdan taxmin qilma.
- Faqat transkriptda bor narsani bahola. Javob topshiriqqa mos kelmasa, Aufgabenbewältigung past bo'lsin.
- "mistakes": {{"original": transkriptdan AYNAN ko'chirilgan qism, "correction": to'g'ri nemischa, "explanation": qisqa izoh}}.
- "strengths", "recommendations": qisqa ro'yxatlar. Har bir mezonga qisqa "comment".
- Barcha izohlar o'zbek tilida (lotin yozuvida); nemischa misollar nemis tilida qolsin. Umumiy ballni hisoblama.

{chr(10).join(blocks)}

Faqat JSON qaytar:
{{"teile": [{{"teil": "<Teil nomi>", "criteria": [{{"key": "aufgabe", "score": 0, "comment": "..."}}], "strengths": ["..."], "mistakes": [{{"original": "...", "correction": "...", "explanation": "..."}}], "recommendations": ["..."]}}], "summary": "...", "strengths": ["..."], "mistakes": ["..."], "recommendations": ["..."]}}"""


def validate_sprechen(raw, parts: list[dict]) -> dict:
    from app.services.lesson_skills.ai_evaluation import verify_errors

    if not isinstance(raw, dict):
        raise InvalidAIResult("not an object")
    by_key = {str(i.get("teil", "")).strip().lower(): i for i in (raw.get("teile") or []) if isinstance(i, dict)}
    names = dict(scoring.SPRECHEN_CRITERIA)
    teile, total, maximum, limited = [], 0, 0, False
    for p in parts:
        # no recording at all: 0 of the full maximum; a recording nobody could hear (no observations): the audio-only criteria are left out
        heard = not p["submission"] or bool(p.get("observations") and p["observations"].get("pronunciation"))
        assessed = [k for k, _ in scoring.SPRECHEN_CRITERIA if heard or k not in scoring.AUDIO_ONLY]
        limited |= len(assessed) < len(scoring.SPRECHEN_CRITERIA) and bool(p["submission"])
        part_max = scoring.SPRECHEN_CRITERION_MAX * len(assessed)
        maximum += part_max
        if not p["submission"] or not p["transcript"]:
            note = "Javob yozib olinmagan — 0 ball." if not p["submission"] else "Yozuvda nemischa nutq aniqlanmadi — 0 ball."
            teile.append({"teil": p["key"], "title": p["title"], "score": 0, "max": part_max, "criteria": [], "transcript": p.get("transcript", ""),
                          "explanation": note, "strengths": [], "mistakes": [], "recommendations": [], "answered": bool(p["submission"])})
            continue
        item = by_key.get(p["key"].strip().lower())
        if item is None:
            raise InvalidAIResult(f"{p['key']} missing")
        crit_in = {str(c.get("key", "")).strip().lower(): c for c in (item.get("criteria") or []) if isinstance(c, dict)}
        criteria, part_total = [], 0
        for key, name in scoring.SPRECHEN_CRITERIA:
            if key not in assessed:
                criteria.append({"key": key, "name": name, "score": None, "max": scoring.SPRECHEN_CRITERION_MAX, "status": "not_assessed",
                                 "comment": "Audio tahlili yo'q — transkriptdan baholanmaydi."})
                continue
            c = crit_in.get(key)
            value = c.get("score") if c else None
            if c is None or isinstance(value, bool) or not isinstance(value, (int, float)) or float(value) != int(value):
                raise InvalidAIResult(f"{p['key']}: criterion {key} missing or not an integer")
            score = max(0, min(scoring.SPRECHEN_CRITERION_MAX, int(value)))
            part_total += score
            criteria.append({"key": key, "name": name, "score": score, "max": scoring.SPRECHEN_CRITERION_MAX, "status": "assessed",
                             "comment": str(c.get("comment", "")).strip()[:500]})
        total += part_total
        teile.append({"teil": p["key"], "title": p["title"], "score": part_total, "max": part_max, "criteria": criteria,
                      "transcript": p["transcript"], "heard": p.get("observations"), "explanation": "",
                      "strengths": _texts(item.get("strengths")), "mistakes": verify_errors(p["transcript"], item.get("mistakes")),
                      "recommendations": _texts(item.get("recommendations")), "answered": True})
    if maximum <= 0:
        raise InvalidAIResult("no Teil")
    return {"kind": "SPRECHEN", "raw": float(total), "raw_max": float(maximum), "teile": teile, "criteria_names": names,
            "summary": str(raw.get("summary", "")).strip()[:1500], "strengths": _texts(raw.get("strengths")),
            "mistakes": _texts(raw.get("mistakes")), "recommendations": _texts(raw.get("recommendations")),
            "limitations": ["Aussprache / Flüssigkeit: audio tahlili bo'lmagan qismlarda baholanmadi."] if limited else []}


# ============================================================
# One run
# ============================================================


def _call(prompt: str) -> tuple[dict, str]:
    from app.services.lesson_skills.ai_evaluation import call_gemini_json

    return call_gemini_json(prompt)


def evaluate(db: Session, s: MockAttemptSection) -> tuple[dict, str | None]:
    """(validated result, model). Raises InvalidAIResult / AIServiceError / SpeechToTextError on failure."""
    if s.section_type == "SCHREIBEN":
        parts = _writing_parts(db, s)
        if not any(p["answer"] for p in parts):
            return validate_schreiben({"teile": []}, parts), None
        raw, model = _call(schreiben_prompt(parts))
        return validate_schreiben(raw, parts), model
    parts = _speaking_parts(db, s)
    _transcribe(parts)
    if not any(p["transcript"] for p in parts):
        return validate_sprechen({"teile": []}, parts), None
    raw, model = _call(sprechen_prompt(parts))
    return validate_sprechen(raw, parts), model


def claim(db: Session, section_id: UUID | None = None) -> UUID | None:
    """Take one section to grade (or the given one if it may run): PENDING, a RUNNING one left stale, or a FAILED one due for a retry."""
    row = db.execute(text("""
        UPDATE mock_attempt_sections SET ai_status = 'RUNNING', ai_claimed_at = now()
        WHERE id = (
            SELECT id FROM mock_attempt_sections
            WHERE section_type IN ('SCHREIBEN', 'SPRECHEN') AND status <> 'OPEN' AND (CAST(:sid AS uuid) IS NULL OR id = CAST(:sid AS uuid))
              AND (ai_status = 'PENDING' OR (ai_status = 'RUNNING' AND ai_claimed_at < :stale)
                   OR (ai_status = 'FAILED' AND ai_runs < :max_runs AND ai_claimed_at < :retry))
            ORDER BY ai_claimed_at NULLS FIRST, submitted_at
            LIMIT 1 FOR UPDATE SKIP LOCKED)
        RETURNING id"""), {"sid": str(section_id) if section_id else None, "stale": _now() - STALE_AFTER, "max_runs": MAX_AUTO_RUNS,
                           "retry": _now() - RETRY_AFTER}).first()
    db.commit()
    return row[0] if row else None


def run_claimed(db: Session, section_id: UUID) -> str:
    """Evaluate a claimed section and store the outcome. Returns the new ai_status."""
    from app.models.lesson_skill import EVAL_FAILED, EVAL_SOURCE_AI, EVAL_SUCCEEDED, AiEvaluation
    from app.services.mock_exam import multilevel_exam_service as exam

    s = db.get(MockAttemptSection, section_id)
    attempt = db.get(MockTestAttempt, s.attempt_id) if s else None
    if s is None or attempt is None:
        return "GONE"
    model = None
    try:
        result, model = evaluate(db, s)
        error = None
    except Exception as exc:  # noqa: BLE001 — every failure is stored and retried; the text / audio stays
        result, error = None, f"{type(exc).__name__}: {str(exc)[:300]}"
    db.rollback()  # nothing of the reads above is kept open while we lock
    attempt = db.scalar(select(MockTestAttempt).where(MockTestAttempt.id == attempt.id).with_for_update())
    s = db.scalar(select(MockAttemptSection).where(MockAttemptSection.id == section_id).with_for_update())
    if s.ai_status != AI_RUNNING:  # re-queued or changed meanwhile: leave it to the next run
        db.commit()
        return s.ai_status or "UNCHANGED"
    s.ai_runs = (s.ai_runs or 0) + 1
    if result is None:
        s.ai_status, s.ai_claimed_at = AI_FAILED, _now()
        db.add(AiEvaluation(kind=exam.ML_SECTION_KIND, submission_id=s.id, user_id=attempt.user_id, source=EVAL_SOURCE_AI, status=EVAL_FAILED,
                            error=error[:500], model=model))
        db.commit()
        log.warning("multilevel AI grading failed: section=%s reason=%s", s.id, error[:120])
        return AI_FAILED
    settings = exam.get_settings(db)
    was_graded = attempt.status == STATUS_GRADED
    exam.apply_ai_result(db, s, result["raw"], result["raw_max"], settings)
    s.ai_claimed_at = None
    result["converted"] = s.auto_score
    result["conversion_missing"] = s.auto_score is None
    db.add(AiEvaluation(kind=exam.ML_SECTION_KIND, submission_id=s.id, user_id=attempt.user_id, source=EVAL_SOURCE_AI, status=EVAL_SUCCEEDED,
                        score=s.auto_score, result=result, model=model))
    exam._recompute(db, attempt, settings)
    if attempt.status == STATUS_GRADED and not was_graded:
        _notify_result(db, attempt)
    db.commit()
    log.info("multilevel AI grading done: section=%s raw=%s/%s score=%s", s.id, result["raw"], result["raw_max"], s.auto_score)
    return s.ai_status


def _notify_result(db: Session, attempt: MockTestAttempt) -> None:
    from app.models.notification import TYPE_COURSE, Notification

    db.add(Notification(user_id=attempt.user_id, type=TYPE_COURSE, link_path=f"/vorbereitung/multilevel/ergebnis/{attempt.id}",
                        title="Modelltest natijasi tayyor / Ergebnis ist da",
                        message=f"Natijangiz: {attempt.total_score} / {attempt.max_score or 300}. / Ihr Ergebnis: {attempt.total_score} / {attempt.max_score or 300}."))


def run_section(section_id: UUID) -> None:
    """Background entry (own session): grade this section now if it may run (BackgroundTasks after a Super Admin re-run)."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        sid = claim(db, section_id)
        if sid:
            run_claimed(db, sid)
    except Exception:  # noqa: BLE001
        db.rollback()
        log.exception("multilevel AI grading crashed: section=%s", section_id)
    finally:
        db.close()


def tick(db: Session, limit: int = PER_ROUND) -> int:
    done = 0
    for _ in range(limit):
        sid = claim(db)
        if sid is None:
            break
        run_claimed(db, sid)
        done += 1
    return done


# ============================================================
# Worker thread (one over all processes: advisory lock on its own connection)
# ============================================================


def _round() -> bool:
    from app.db.database import engine
    from app.db.session import SessionLocal

    with engine.connect() as lock:
        got = bool(lock.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": LOCK_KEY}).scalar())
        lock.commit()
        if not got:
            return False
        try:
            db = SessionLocal()
            try:
                tick(db)
            except Exception:  # noqa: BLE001
                db.rollback()
                log.exception("multilevel AI round failed")
            finally:
                db.close()
        finally:
            lock.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_KEY})
            lock.commit()
    return True


def _loop() -> None:
    while True:
        try:
            _round()
        except Exception:  # noqa: BLE001 — DB restart etc.
            log.exception("multilevel AI worker round failed")
        time.sleep(INTERVAL)


def on_startup() -> None:
    global _started
    if not app_settings.MULTILEVEL_AI_ENABLED or app_settings.APP_ENV == "test":
        return
    with _guard:
        if _started:
            return
        _started = True
    threading.Thread(target=_loop, name="multilevel-ai", daemon=True).start()
