"""Server-side Sprechen pipeline for VIZU-Multilevel (5 Aufgaben x 20 = 100).

Per saved answer (runs in the background right after upload):

1. Speech-to-Text agent   — SpeechToTextService: verbatim transcript (learner
                            errors kept) + what it HEARD (intelligibility,
                            pronunciation, fluency).          -> TRANSCRIBED
2. Language Analysis agent — genuine errors, each quoted verbatim from the
                            transcript (server drops anything not literally
                            present — the AI cannot invent errors), plus a
                            short range/accuracy/coherence profile.
3. CEFR Evaluation agent  — scores the 5 criteria against the descriptors of
                            the Aufgabe's TARGET level (an A1 answer is never
                            judged by C1 standards and vice versa), using the
                            transcript, duration, STT confidence and the audio
                            observations — never length alone.
4. Feedback agent         — strengths, improvements, a concrete tip and
                            corrected examples from the student's own words.
5. Final Score Validator  — server code: every criterion an int clamped to
                            its max, task score = exact sum (0-20), feedback
                            present; malformed AI JSON is repaired by re-asking
                            (max. 2 repairs).                  -> EVALUATED
Any failure -> FAILED (audio and transcript kept; retry resumes where it
stopped). Students can neither send nor change scores — this module is the
only writer of ai_score/ai_criteria/ai_feedback.
"""

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.vizu_multilevel_attempt import VizuMultilevelAttempt
from app.models.vizu_multilevel_speaking import VizuMultilevelSpeakingSubmission, VizuMultilevelSpeakingTask
from app.services.speech.speech_to_text_service import SpeechToTextError, SpeechToTextService
from app.services.vizu_multilevel import sprechen_service
from app.services.vizu_multilevel.schreiben_evaluation_service import _call_json, verify_errors
from app.services.vizu_multilevel.sprechen_service import EVALUATED, EVALUATING, FAILED, PROCESSING, TRANSCRIBED

# (key, label, max) — 5 + 4 + 4 + 3 + 4 = 20
CRITERIA = [
    ("task_completion", "Aufgabenbewältigung", 5),
    ("vocabulary", "Sprachumfang / Wortschatz", 4),
    ("grammar", "Grammatik", 4),
    ("fluency_coherence", "Flüssigkeit / Kohärenz", 3),
    ("pronunciation_clarity", "Aussprache / Verständlichkeit", 4),
]
TASK_MAX = sum(m for _, _, m in CRITERIA)
MAX_ERRORS = 8
MAX_REPAIRS = 2
STALE_AFTER = timedelta(minutes=10)

LEVEL_DESCRIPTORS = {
    "A1": "einfache, isolierte Sätze; grundlegende persönliche Informationen; sehr elementarer Wortschatz und Grundgrammatik; kurze, aber verständliche Antworten genügen. Viele Fehler sind auf A1 normal, solange die Mitteilung verständlich ist.",
    "A2": "Alltagsthemen; einfache, mit „und“, „aber“, „weil“, „dann“ verbundene Sätze; kurz Gründe und Meinungen nennen; grundlegende Interaktion.",
    "B1": "zusammenhängendes Sprechen über Erfahrungen und Ereignisse; eigene Meinung begründen; Ursachen und Folgen erklären; überwiegend verständlich trotz Fehlern.",
    "B2": "komplexere Themen klar und detailliert darstellen; Argumente entwickeln, Vor- und Nachteile abwägen, vergleichen; Position verteidigen; gute Kohärenz und relativ gute grammatische Kontrolle.",
    "C1": "flüssig, spontan und präzise über komplexe Themen; nuancierte Argumentation; breiter, idiomatischer Wortschatz; hohe grammatische Kontrolle mit komplexen Strukturen; natürlicher Diskursaufbau mit Verknüpfungsmitteln.",
}

ANALYSIS_PROMPT = """Du bist Sprachanalyst/in für Deutsch als Fremdsprache. Analysiere das TRANSKRIPT einer MÜNDLICHEN Prüfungsantwort.

AUFGABE (Zielniveau {level}): {task}

TRANSKRIPT (wörtlich, zwischen <<< und >>>):
<<<{transcript}>>>

Regeln:
- Es ist gesprochene Sprache: ignoriere Zeichensetzung, Groß-/Kleinschreibung und Rechtschreibung vollständig.
- Melde nur ECHTE, sichere Fehler in Grammatik (Kasus, Artikel, Verbposition, Konjugation, Präpositionen), Wortwahl oder Satzbau. Keine Stilvorlieben, keine korrekten Varianten.
- "original" muss ein WÖRTLICHES, kurzes Zitat aus dem Transkript sein (genau so geschrieben). "correction" ist dieselbe Stelle korrigiert. "explanation": ein kurzer Satz auf Deutsch.
- Höchstens {max_errors} Fehler, die wichtigsten zuerst. Wenn keine sicheren Fehler: leere Liste.
- "profile": je 1 kurzer Satz zu Spektrum (range), Korrektheit (accuracy) und Zusammenhang (coherence); "connectors": benutzte Verknüpfungswörter.

Antworte NUR mit JSON:
{{"errors": [{{"original": "...", "correction": "...", "explanation": "...", "category": "grammatik|wortschatz|satzbau"}}], "profile": {{"range": "...", "accuracy": "...", "coherence": "..."}}, "connectors": ["..."]}}"""

CEFR_PROMPT = """Du bist erfahrene/r, faire/r Prüfer/in für mündliche Deutschprüfungen nach dem GER (CEFR). Bewerte EINE Antwort.

AUFGABE: {task}
ZIELNIVEAU dieser Aufgabe: {level} — erwartet wird: {descriptor}
Empfohlene Sprechzeit: {min_s}-{max_s} s. Tatsächliche Dauer: {duration}.

TRANSKRIPT (wörtlich, Fehler bewusst nicht korrigiert):
<<<{transcript}>>>

Automatische Erkennungssicherheit: {confidence}
Was beim HÖREN der Aufnahme auffiel: {observations}

Gesicherte Fehler (aus der Analyse): {errors}
Sprachprofil: {profile}

BEWERTUNGSRASTER (ganze Zahlen, jeweils 0 bis Maximum):
- task_completion (0-5): Aufgabenbewältigung — alle Inhaltspunkte, passend zur Aufgabe und kommunikativ angemessen.
- vocabulary (0-4): Sprachumfang / Wortschatz — Spektrum und Passung.
- grammar (0-4): Grammatik — Korrektheit und Komplexität.
- fluency_coherence (0-3): Flüssigkeit / Kohärenz — Redefluss, Zusammenhang, Verknüpfungen.
- pronunciation_clarity (0-4): Aussprache / Verständlichkeit — stütze dich auf die Höreindrücke und die Erkennungssicherheit.

Regeln (GER-gerecht):
- Bewerte am ZIELNIVEAU {level}: Eine A1-Antwort wird nicht mit C1-Maßstäben gemessen; auf B2/C1 bringen einfache Sätze keine hohen Punkte.
- Ein einzelner Fehler kostet nie viele Punkte; maßgeblich sind Verständlichkeit, Spektrum, Korrektheit und Kommunikation insgesamt.
- Nicht nach Länge allein bewerten. Deutlich zu kurze oder themenfremde Antworten senken task_completion.
- Keine Sprache / nur Geräusche: alle Kriterien 0.

Antworte NUR mit JSON:
{{"criteria": {{"task_completion": 0, "vocabulary": 0, "grammar": 0, "fluency_coherence": 0, "pronunciation_clarity": 0}}, "score": 0, "justification": {{"task_completion": "...", "vocabulary": "...", "grammar": "...", "fluency_coherence": "...", "pronunciation_clarity": "..."}}}}"""

FEEDBACK_PROMPT = """Du bist eine erfahrene, freundliche Deutschlehrkraft. Schreibe persönliches Feedback zu EINER mündlichen Antwort (Anrede „Sie“).

AUFGABE: {task}
TRANSKRIPT: <<<{transcript}>>>
Punkte: {score}/20 — {criteria}
Gesicherte Fehler: {errors}

Regeln:
- Beziehe dich konkret auf DIESE Antwort (gern kurze Zitate aus dem Transkript). Keine allgemeinen Floskeln, die auf jede Antwort passen.
- "strengths": 2-3 konkrete Stärken.
- "improvements": 1-3 konkrete Verbesserungspunkte (z. B. Artikel, Verbposition, längere Begründungen).
- "feedback": 2-3 natürliche Sätze Gesamteindruck.
- "next_step": EIN konkreter Tipp für die nächste Antwort (z. B. mit Beispielwörtern oder einem Mustersatz).
- Erfinde keine Fehler, die nicht in der Fehlerliste oder im Transkript stehen.
- Keine Begrüßung oder Briefanrede; nenne keinen Namen und setze kein Geschlecht voraus (kein „Frau …“/„Herr …“). Beginne direkt mit dem Inhalt.

Antworte NUR mit JSON:
{{"strengths": ["..."], "improvements": ["..."], "feedback": "...", "next_step": "..."}}"""


class EvaluationValidationError(ValueError):
    pass


# ============================================================
# Validators (pure)
# ============================================================


def validate_scores(raw: dict) -> dict:
    """Final Score Validator for the CEFR agent's output: every criterion
    present and an integer within [0, max]; the task score is the exact sum
    (the model's own "score" is never trusted)."""
    criteria_raw = raw.get("criteria") if isinstance(raw, dict) else None
    if not isinstance(criteria_raw, dict):
        raise EvaluationValidationError('"criteria" fehlt oder ist kein Objekt.')
    criteria = {}
    for key, _label, maximum in CRITERIA:
        if key not in criteria_raw:
            raise EvaluationValidationError(f'Kriterium "{key}" fehlt.')
        try:
            value = int(round(float(criteria_raw[key])))
        except (TypeError, ValueError) as exc:
            raise EvaluationValidationError(f'Kriterium "{key}" ist keine Zahl.') from exc
        criteria[key] = max(0, min(maximum, value))
    justification = raw.get("justification") if isinstance(raw.get("justification"), dict) else {}
    score = sum(criteria.values())
    assert 0 <= score <= TASK_MAX
    return {
        "criteria": criteria,
        "score": score,
        "justification": {k: str(justification.get(k, "")).strip()[:300] for k, _l, _m in CRITERIA},
    }


def _clean_list(value, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v).strip()[:400] for v in value if str(v).strip()][:limit]


def validate_feedback(raw: dict) -> dict:
    strengths = _clean_list(raw.get("strengths"), 3)
    improvements = _clean_list(raw.get("improvements"), 3)
    feedback = str(raw.get("feedback", "")).strip()[:1200]
    next_step = str(raw.get("next_step", "")).strip()[:500]
    if not strengths or not feedback or not next_step:
        raise EvaluationValidationError('"strengths", "feedback" und "next_step" müssen vorhanden sein.')
    return {"strengths": strengths, "improvements": improvements, "feedback": feedback, "next_step": next_step}


def validate_analysis(raw: dict, transcript: str) -> dict:
    if not isinstance(raw, dict) or not isinstance(raw.get("errors", []), list):
        raise EvaluationValidationError('"errors" muss eine Liste sein.')
    profile = raw.get("profile") if isinstance(raw.get("profile"), dict) else {}
    return {
        "errors": verify_errors(transcript, raw.get("errors", []))[:MAX_ERRORS],
        "profile": {k: str(profile.get(k, "")).strip()[:300] for k in ("range", "accuracy", "coherence")},
        "connectors": _clean_list(raw.get("connectors"), 12),
    }


def validate_task_result(result: dict) -> dict:
    """Last gate before storing: 0-20, sum matches, feedback present."""
    criteria = result["criteria"]
    if set(criteria) != {k for k, _l, _m in CRITERIA}:
        raise EvaluationValidationError("Kriterien unvollständig.")
    if result["score"] != sum(criteria.values()) or not 0 <= result["score"] <= TASK_MAX:
        raise EvaluationValidationError("Punktsumme ungültig.")
    if not result["feedback"] or not result["strengths"]:
        raise EvaluationValidationError("Feedback fehlt.")
    return result


def _call_validated(prompt: str, validator) -> dict:
    """AI call + validation; on malformed / invalid JSON the model is asked
    again with the concrete problem (repair), at most MAX_REPAIRS times."""
    current = prompt
    last_error: Exception | None = None
    for _ in range(MAX_REPAIRS + 1):
        try:
            return validator(_call_json(current))
        except EvaluationValidationError as exc:
            last_error = exc
            current = (
                prompt
                + f"\n\nDeine letzte Antwort war ungültig: {exc} Antworte jetzt NUR mit gültigem JSON genau im geforderten Schema."
            )
    raise EvaluationValidationError(f"AI-Antwort nach {MAX_REPAIRS} Reparaturversuchen ungültig: {last_error}")


# ============================================================
# Evaluation of one answer (pure w.r.t. the database)
# ============================================================


def _task_text(task) -> str:
    return f"Aufgabe {task.order_index} — {task.title}: {task.instruction}"


def empty_result(reason: str) -> dict:
    return {
        "score": 0,
        "criteria": {k: 0 for k, _l, _m in CRITERIA},
        "justification": {k: "" for k, _l, _m in CRITERIA},
        "strengths": [],
        "improvements": ["Sprechen Sie zu jeder Aufgabe — auch eine kurze, verständliche Antwort bringt Punkte."],
        "errors": [],
        "feedback": reason,
        "next_step": "Beginnen Sie mit einem einfachen Satz zum Thema und erklären Sie dann einen Grund mit „weil“.",
        "profile": {},
    }


def evaluate_answer(task, transcript: str, duration_seconds, confidence, observations: dict | None) -> dict:
    """Agents 2-5 for one transcribed answer."""
    words = transcript.replace("[unverständlich]", " ").split()
    if len(words) < 2:
        return empty_result("Es wurde keine verständliche Antwort erkannt.")

    task_text = _task_text(task)
    analysis = _call_validated(
        ANALYSIS_PROMPT.format(level=task.level, task=task_text, transcript=transcript, max_errors=MAX_ERRORS),
        lambda raw: validate_analysis(raw, transcript),
    )
    errors_text = (
        "; ".join(f'"{e["original"]}" -> "{e["correction"]}" ({e["explanation"]})' for e in analysis["errors"]) or "keine"
    )
    scores = _call_validated(
        CEFR_PROMPT.format(
            task=task_text,
            level=task.level,
            descriptor=LEVEL_DESCRIPTORS.get(task.level, ""),
            min_s=task.min_seconds,
            max_s=task.max_seconds,
            duration=f"{duration_seconds} s" if duration_seconds else "unbekannt",
            transcript=transcript,
            confidence=f"{confidence:.2f}" if isinstance(confidence, (int, float)) else "unbekannt",
            observations=json.dumps(observations, ensure_ascii=False) if observations else "keine Angaben",
            errors=errors_text,
            profile=json.dumps(analysis["profile"], ensure_ascii=False),
        ),
        validate_scores,
    )
    criteria_text = ", ".join(f"{label} {scores['criteria'][key]}/{m}" for key, label, m in CRITERIA)
    feedback = _call_validated(
        FEEDBACK_PROMPT.format(task=task_text, transcript=transcript, score=scores["score"], criteria=criteria_text, errors=errors_text),
        validate_feedback,
    )
    return validate_task_result(
        {
            "score": scores["score"],
            "criteria": scores["criteria"],
            "justification": scores["justification"],
            "errors": [{k: e[k] for k in ("original", "correction", "explanation")} for e in analysis["errors"]],
            "profile": analysis["profile"],
            **feedback,
        }
    )


# ============================================================
# Pipeline orchestration (own DB session — runs in the background)
# ============================================================


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _claim(db: Session, submission_id: UUID) -> bool:
    """Atomically marks the answer as being processed; an answer is never
    processed by two workers at once (a stale claim expires)."""
    result = db.execute(
        update(VizuMultilevelSpeakingSubmission)
        .where(
            VizuMultilevelSpeakingSubmission.id == submission_id,
            VizuMultilevelSpeakingSubmission.status.in_([PROCESSING, TRANSCRIBED, EVALUATING, FAILED]),
            or_(
                VizuMultilevelSpeakingSubmission.worker_started_at.is_(None),
                VizuMultilevelSpeakingSubmission.worker_started_at < _now() - STALE_AFTER,
            ),
        )
        .values(worker_started_at=_now())
    )
    db.commit()
    return result.rowcount == 1


def _snapshot(task: VizuMultilevelSpeakingTask) -> SimpleNamespace:
    return SimpleNamespace(
        order_index=task.order_index,
        title=task.title,
        instruction=task.instruction,
        level=task.level,
        min_seconds=task.min_seconds,
        max_seconds=task.max_seconds,
    )


def process_submission(submission_id: UUID) -> None:
    """STT (if not done yet) -> evaluation -> store; then finalizes the
    attempt's Sprechen result if everything is evaluated."""
    db = SessionLocal()
    try:
        if not _claim(db, submission_id):
            return
        sub = db.get(VizuMultilevelSpeakingSubmission, submission_id)
        task = _snapshot(sub.task)
        attempt_id = sub.attempt_id

        if sub.transcript is None:
            sub.status = PROCESSING
            sub.evaluation_error = None
            db.commit()
            try:
                result = SpeechToTextService().transcribe(
                    sprechen_service.resolve_audio_path(sub), sub.content_type, language="de", duration_seconds=sub.duration_seconds
                )
            except SpeechToTextError as exc:
                sub.status, sub.evaluation_error, sub.worker_started_at = FAILED, f"STT: {exc}"[:500], None
                db.commit()
                return
            sub.transcript = result.text
            sub.transcript_language = result.language
            sub.transcript_confidence = result.confidence
            sub.stt_provider = result.provider[:30]
            sub.audio_observations = result.observations
            sub.status = TRANSCRIBED
            db.commit()

        sub.status = EVALUATING
        db.commit()
        transcript, duration = sub.transcript, sub.duration_seconds
        confidence, observations = sub.transcript_confidence, sub.audio_observations
        try:
            outcome = evaluate_answer(task, transcript, duration, confidence, observations)
        except Exception as exc:  # AI unavailable / invalid after repairs — retryable
            sub = db.get(VizuMultilevelSpeakingSubmission, submission_id)
            sub.status, sub.evaluation_error, sub.worker_started_at = FAILED, f"AI: {exc}"[:500], None
            db.commit()
            return

        sub = db.get(VizuMultilevelSpeakingSubmission, submission_id)
        sub.ai_score = outcome["score"]
        sub.ai_criteria = outcome["criteria"]
        sub.ai_feedback = {k: v for k, v in outcome.items() if k not in ("score", "criteria")}
        sub.status = EVALUATED
        sub.evaluation_error = None
        sub.evaluated_at = _now()
        sub.worker_started_at = None
        db.commit()
        finalize_if_complete(db, attempt_id)
    finally:
        db.close()


def finalize_if_complete(db: Session, attempt_id: UUID) -> None:
    attempt = db.get(VizuMultilevelAttempt, attempt_id)
    if attempt is None or attempt.sprechen_submitted_at is None:
        return
    if not sprechen_service.is_graded_complete(db, attempt_id):
        return
    from app.services.vizu_multilevel import service as flow

    sprechen_service.recompute_attempt(db, attempt)
    db.commit()
    flow.refresh_overall(db, attempt)


def pending_submission_ids(db: Session, attempt_id: UUID) -> list[UUID]:
    """Answers that still need (re)processing: FAILED, or stuck mid-pipeline
    without a live worker."""
    rows = db.scalars(
        select(VizuMultilevelSpeakingSubmission).where(
            VizuMultilevelSpeakingSubmission.attempt_id == attempt_id,
            VizuMultilevelSpeakingSubmission.status.in_([PROCESSING, TRANSCRIBED, EVALUATING, FAILED]),
        )
    )
    stale = _now() - STALE_AFTER
    return [
        s.id
        for s in rows
        if s.status == FAILED or s.worker_started_at is None or s.worker_started_at < stale
    ]


def run_pending(attempt_id: UUID) -> None:
    db = SessionLocal()
    try:
        ids = pending_submission_ids(db, attempt_id)
    finally:
        db.close()
    for submission_id in ids:
        process_submission(submission_id)
    db = SessionLocal()
    try:
        finalize_if_complete(db, attempt_id)
    finally:
        db.close()


# ============================================================
# Student-facing result
# ============================================================


def overall_status(subs: list[VizuMultilevelSpeakingSubmission]) -> str:
    statuses = [s.status for s in subs]
    if statuses and all(x == EVALUATED or (x is None) for x in statuses):
        return "DONE"
    if FAILED in statuses and not any(x in (PROCESSING, TRANSCRIBED, EVALUATING) for x in statuses):
        return "FAILED"
    return "PENDING"


def _level_label(level: str | None) -> str:
    return level or "BELOW_A1"


def build_student_result(db: Session, attempt: VizuMultilevelAttempt) -> dict:
    tasks = sprechen_service.attempt_tasks(db, attempt.id)
    subs = {s.task_id: s for s in sprechen_service.get_own_submissions(db, attempt.id)}
    answered = [subs[t.id] for t in tasks if t.id in subs]
    progress = [
        {"task_id": t.id, "order_index": t.order_index, "status": subs[t.id].status if t.id in subs else None}
        for t in tasks
    ]
    payload = {
        "status": "NOT_SUBMITTED",
        "evaluated": sum(1 for s in answered if sprechen_service.effective_score(s) is not None),
        "total_tasks": len(tasks),
        "progress": progress,
        "total_score": None,
        "max_score": sum(t.points for t in tasks),
        "level": None,
        "tasks": [],
    }
    if attempt.sprechen_submitted_at is None:
        return payload
    status = overall_status(answered) if answered else "DONE"
    if status == "DONE" and not sprechen_service.is_graded_complete(db, attempt.id):
        status = "PENDING"
    payload["status"] = status
    if status != "DONE":
        return payload

    task_results = []
    for t in tasks:
        sub = subs.get(t.id)
        fb = (sub.ai_feedback or {}) if sub else {}
        criteria = (sub.ai_criteria or {}) if sub else {}
        score = sprechen_service.effective_score(sub) or 0
        task_results.append(
            {
                "task_id": t.id,
                "order_index": t.order_index,
                "title": t.title,
                "score": score,
                "max_score": t.points,
                "answered": sub is not None,
                "transcript": sub.transcript if sub else None,
                "criteria": [
                    {"key": key, "label": label, "score": int(criteria.get(key, 0)), "max": maximum}
                    for key, label, maximum in CRITERIA
                ],
                "strengths": fb.get("strengths", []),
                "improvements": fb.get("improvements", []),
                "errors": fb.get("errors", []),
                "feedback": fb.get("feedback", "") or ("Keine Antwort gespeichert." if sub is None else ""),
                "next_step": fb.get("next_step", ""),
                "teacher_comment": sub.teacher_comment if sub else None,
            }
        )
    total = sum(r["score"] for r in task_results)
    payload["tasks"] = task_results
    payload["total_score"] = total
    payload["level"] = _level_label(sprechen_service.level_for_score(total))
    return payload
