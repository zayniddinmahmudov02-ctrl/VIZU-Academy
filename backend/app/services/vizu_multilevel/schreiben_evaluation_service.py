"""Server-side AI evaluation of VIZU-Mock Schreiben (5 Aufgaben x 20 = 100).

Pipeline per Aufgabe — two specialised passes on the project's existing
Gemini infrastructure (app/services/mock_exam/ai_service.py), then strict
server-side validation:

1. Error-analysis agent: finds GENUINE errors and must quote each one
   verbatim from the student's text (grammar, orthography, vocabulary,
   style), with a correction and a short reason.
2. Server check: every error whose `original` is not literally present in
   the submitted text is DROPPED — the AI cannot invent errors; overlapping
   quotes of the same spot are merged.
2b. Confirmation agent: a second, independent pass keeps only the errors it
   confirms as genuinely wrong (no style preferences, no valid variants).
3. Rubric agent: scores each criterion of the Aufgabe's rubric (task
   fulfilment, vocabulary, grammar, coherence/comprehensibility,
   orthography) using the verified errors, and writes strengths, feedback
   and next steps.
4. Server scoring: every criterion score is clamped to [0, max]; the task
   total is the SUM of the clamped scores (never the model's own
   arithmetic) — so a task never exceeds 20 and the module never 100.

Both passes run with temperature 0. Nothing here claims an official
Goethe/telc/ÖSD score. The client can neither send nor change points: the
only writer of scores is this module."""

import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.vizu_multilevel_attempt import VizuMultilevelAttempt
from app.models.vizu_multilevel_writing import (
    VizuMultilevelWritingCriterionScore,
    VizuMultilevelWritingSubmission,
    VizuMultilevelWritingTask,
)
from app.services.mock_exam.ai_service import GEMINI_ENDPOINT, AIServiceError, _extract_json, _require_api_key

PENDING = "PENDING"
RUNNING = "RUNNING"
DONE = "DONE"
FAILED = "FAILED"

MAX_ERRORS = 10

ERROR_PROMPT = """Du bist erfahrene/r Prüfer/in für Deutsch als Fremdsprache. Analysiere den Text eines Lernenden.

AUFGABE:
{task}

TEXT DES LERNENDEN (zwischen <<< und >>>):
<<<{text}>>>

Finde nur ECHTE sprachliche Fehler (Grammatik, Rechtschreibung, Wortwahl/Wortschatz, Zeichensetzung nur wenn sinnentstellend).
Strenge Regeln:
- "original" MUSS eine exakte, buchstabengetreue Kopie eines Ausschnitts aus dem Text sein (gleiche Groß-/Kleinschreibung, gleiche Zeichen). Erfinde nichts.
- Nimm einen kurzen Ausschnitt (1-6 Wörter), der den Fehler enthält.
- "correction" ist die korrigierte Fassung genau dieses Ausschnitts.
- Melde keine Stilvorlieben als Fehler. Wenn der Text keine Fehler hat, gib eine leere Liste zurück.
- Höchstens {max_errors} Fehler, die wichtigsten zuerst.

Antworte NUR mit JSON in genau dieser Form:
{{"errors": [{{"original": "...", "correction": "...", "explanation": "kurze Begründung auf Deutsch", "category": "grammatik|rechtschreibung|wortschatz|zeichensetzung"}}]}}"""

CONFIRM_PROMPT = """Du bist eine zweite, unabhängige Prüferin für Deutsch als Fremdsprache. Eine erste Prüfung hat in einem Lernertext mögliche Fehler gemeldet. Prüfe JEDEN Eintrag streng: Ist der Ausschnitt "original" im Kontext des Textes nach der deutschen Standardsprache (aktuelle Rechtschreibung und Grammatik) wirklich FALSCH?

Bestätige NICHT:
- Formulierungen, die korrekt sind und nur anders/stilistisch "schöner" sein könnten,
- Varianten, die ebenfalls richtig sind,
- Einträge, deren Korrektur nichts verbessert.

TEXT DES LERNENDEN (zwischen <<< und >>>):
<<<{text}>>>

GEMELDETE EINTRÄGE:
{items}

Antworte NUR mit JSON: {{"confirmed": [<Nummern der wirklich falschen Einträge>]}}"""

RUBRIC_PROMPT = """Du bist erfahrene/r Prüfer/in für Deutsch als Fremdsprache und bewertest eine Schreibaufgabe nach einem analytischen Raster (Aufgabenerfüllung, Wortschatz, Grammatik, Kohärenz/Verständlichkeit, Rechtschreibung) — angelehnt an etablierte Prinzipien der Bewertung schriftlicher Leistungen, ohne eine offizielle Prüfungsnote zu behaupten.

AUFGABE:
{task}
Geforderte Länge: {min_words}-{max_words} Wörter. Tatsächliche Länge: {word_count} Wörter.

TEXT DES LERNENDEN (zwischen <<< und >>>):
<<<{text}>>>

BEREITS GEPRÜFTE, TATSÄCHLICH VORHANDENE FEHLER:
{errors}

BEWERTUNGSRASTER (ganze Punkte, jeweils 0 bis Maximum):
{criteria}

Regeln:
- Bewerte nur, was wirklich im Text steht. Fehlende Inhaltspunkte der Aufgabe senken "Aufgabenbearbeitung".
- Deutlich zu kurze Texte erhalten in der Aufgabenbearbeitung weniger Punkte.
- "strengths": 2-4 konkrete Beobachtungen, die sich auf den Text beziehen (gern mit kurzem Zitat).
- "feedback": 2-4 natürliche Sätze wie eine Lehrkraft: was gut gelungen ist und was besser werden muss.
- "next_steps": 1-3 konkrete Empfehlungen für die nächste Schreibaufgabe.
- Alles auf Deutsch.

Antworte NUR mit JSON in genau dieser Form:
{{"criteria": [{{"name": "<exakter Kriteriumsname>", "score": <ganze Zahl>, "justification": "kurz"}}], "strengths": ["..."], "feedback": "...", "next_steps": ["..."]}}"""


# ============================================================
# Gemini call (temperature 0, JSON mode) — reuses ai_service's key handling
# ============================================================


def _call_json(prompt: str) -> dict:
    api_key = _require_api_key()
    payload = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }
    ).encode("utf-8")
    models = [settings.GEMINI_MODEL] + ([settings.GEMINI_FALLBACK_MODEL] if settings.GEMINI_FALLBACK_MODEL else [])
    last_error: Exception | None = None
    for model in models:
        for _attempt in range(2):
            url = GEMINI_ENDPOINT.format(model=model) + f"?key={api_key}"
            request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    body = json.loads(response.read().decode("utf-8"))
                return _extract_json(body["candidates"][0]["content"]["parts"][0]["text"])
            except (urllib.error.URLError, KeyError, IndexError, ValueError, AIServiceError) as exc:
                last_error = exc
    raise AIServiceError(f"AI evaluation failed: {last_error}")


# ============================================================
# Pure, testable validation / scoring
# ============================================================


def _normalise(text: str) -> str:
    return " ".join(text.split())


def verify_errors(text: str, raw_errors: list) -> list[dict]:
    """Keeps only errors whose `original` really occurs in the student's
    text (whitespace-normalised) and whose correction actually differs.
    Everything else is dropped — the AI cannot invent errors."""
    haystack = _normalise(text)
    seen: set[str] = set()
    verified = []
    for item in raw_errors if isinstance(raw_errors, list) else []:
        if not isinstance(item, dict):
            continue
        original = _normalise(str(item.get("original", "")))
        correction = _normalise(str(item.get("correction", "")))
        explanation = str(item.get("explanation", "")).strip()
        if not original or not correction or original == correction or original not in haystack or original in seen:
            continue
        # Overlapping quotes ("Cafe" and "im Cafe") describe the same spot —
        # keep only the first one.
        if any(original in kept or kept in original for kept in seen):
            continue
        seen.add(original)
        verified.append(
            {
                "original": original,
                "correction": correction,
                "explanation": explanation[:300],
                "category": str(item.get("category", "")).strip().lower()[:30],
            }
        )
        if len(verified) >= MAX_ERRORS:
            break
    return verified


def confirm_errors(errors: list[dict], confirmed) -> list[dict]:
    """Keeps the errors whose 1-based number the confirmation agent
    returned. Anything malformed confirms nothing (never invents)."""
    if not isinstance(confirmed, list):
        return []
    numbers = set()
    for value in confirmed:
        try:
            numbers.add(int(value))
        except (TypeError, ValueError):
            continue
    return [e for i, e in enumerate(errors, start=1) if i in numbers]


def score_criteria(criteria: list[VizuMultilevelWritingCriterionScore] | list, ai_criteria: list) -> list[dict]:
    """Maps the AI's criterion scores onto the task's REAL rubric (by name),
    clamps each to [0, max] as an integer. A criterion the AI omitted gets
    0 — never a guess."""
    by_name = {}
    for item in ai_criteria if isinstance(ai_criteria, list) else []:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            by_name[item["name"].strip().lower()] = item
    result = []
    for criterion in criteria:
        item = by_name.get(criterion.name.strip().lower(), {})
        try:
            value = int(round(float(item.get("score", 0))))
        except (TypeError, ValueError):
            value = 0
        result.append(
            {
                "criterion_id": criterion.id,
                "name": criterion.name,
                "max": criterion.max_score,
                "score": max(0, min(criterion.max_score, value)),
                "justification": str(item.get("justification", "")).strip()[:300],
            }
        )
    return result


def _clean_list(value, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v).strip()[:400] for v in value if str(v).strip()][:limit]


# ============================================================
# Evaluation of one submission
# ============================================================


def _task_spec(task: VizuMultilevelWritingTask) -> SimpleNamespace:
    """Plain snapshot of a task (+ rubric) — worker threads never touch ORM
    objects or the session."""
    return SimpleNamespace(
        order_index=task.order_index,
        title=task.title,
        instruction=task.instruction,
        min_words=task.min_words,
        max_words=task.max_words,
        rubric_criteria=[SimpleNamespace(id=c.id, name=c.name, max_score=c.max_score) for c in task.rubric_criteria],
    )


def _task_prompt_text(task) -> str:
    return f"Aufgabe {task.order_index} — {task.title}\n{task.instruction}"


def _evaluate(task, submission_text: str, word_count: int) -> dict:
    """Runs both agents for one Aufgabe; pure w.r.t. the database."""
    task_text = _task_prompt_text(task)
    raw = _call_json(ERROR_PROMPT.format(task=task_text, text=submission_text, max_errors=MAX_ERRORS))
    errors = verify_errors(submission_text, raw.get("errors", []))
    if errors:
        # Second, independent agent: keeps only errors it confirms as real.
        items = "\n".join(
            f'{i}. "{e["original"]}" -> "{e["correction"]}" ({e["explanation"]})' for i, e in enumerate(errors, start=1)
        )
        verdict = _call_json(CONFIRM_PROMPT.format(text=submission_text, items=items))
        errors = confirm_errors(errors, verdict.get("confirmed"))

    errors_text = (
        "\n".join(f'- "{e["original"]}" -> "{e["correction"]}" ({e["explanation"]})' for e in errors) or "- keine"
    )
    criteria_text = "\n".join(f"- {c.name}: 0-{c.max_score}" for c in task.rubric_criteria)
    rubric = _call_json(
        RUBRIC_PROMPT.format(
            task=task_text,
            min_words=task.min_words,
            max_words=task.max_words,
            word_count=word_count,
            text=submission_text,
            errors=errors_text,
            criteria=criteria_text,
        )
    )
    scored = score_criteria(task.rubric_criteria, rubric.get("criteria", []))
    return {
        "criteria": scored,
        "errors": errors,
        "strengths": _clean_list(rubric.get("strengths"), 4),
        "feedback": str(rubric.get("feedback", "")).strip()[:1500],
        "next_steps": _clean_list(rubric.get("next_steps"), 3),
    }


def _claim(db: Session, submission_id: UUID) -> bool:
    """Atomically moves PENDING/FAILED -> RUNNING so a submission is never
    evaluated twice concurrently."""
    result = db.execute(
        update(VizuMultilevelWritingSubmission)
        .where(
            VizuMultilevelWritingSubmission.id == submission_id,
            VizuMultilevelWritingSubmission.evaluation_status.in_([PENDING, FAILED]),
        )
        .values(evaluation_status=RUNNING, evaluation_error=None)
    )
    db.commit()
    return result.rowcount == 1


def _empty_result(task) -> dict:
    return {
        "criteria": [
            {"criterion_id": c.id, "name": c.name, "max": c.max_score, "score": 0, "justification": ""}
            for c in task.rubric_criteria
        ],
        "errors": [],
        "strengths": [],
        "feedback": "Zu dieser Aufgabe wurde kein Text abgegeben.",
        "next_steps": ["Bearbeite jede Aufgabe — auch ein kurzer Text bringt Punkte."],
    }


def _store(db: Session, submission: VizuMultilevelWritingSubmission, evaluation: dict) -> None:
    existing = {
        cs.criterion_id: cs
        for cs in db.scalars(
            select(VizuMultilevelWritingCriterionScore).where(
                VizuMultilevelWritingCriterionScore.submission_id == submission.id
            )
        )
    }
    for item in evaluation["criteria"]:
        row = existing.get(item["criterion_id"])
        if row is None:
            db.add(
                VizuMultilevelWritingCriterionScore(
                    submission_id=submission.id, criterion_id=item["criterion_id"], score=item["score"]
                )
            )
        else:
            row.score = item["score"]
    # Deterministic total = sum of the clamped criterion scores.
    submission.teacher_score = sum(item["score"] for item in evaluation["criteria"])
    submission.ai_feedback = {
        "criteria": [{k: v for k, v in item.items() if k != "criterion_id"} for item in evaluation["criteria"]],
        "errors": evaluation["errors"],
        "strengths": evaluation["strengths"],
        "feedback": evaluation["feedback"],
        "next_steps": evaluation["next_steps"],
    }
    submission.evaluation_status = DONE
    submission.evaluation_error = None
    submission.evaluated_at = datetime.now(timezone.utc)


def mark_pending(db: Session, attempt_id: UUID) -> None:
    """Called inside the final submission: every Aufgabe of the attempt is
    queued for evaluation (one submission row per active task)."""
    tasks = list(db.scalars(select(VizuMultilevelWritingTask).where(VizuMultilevelWritingTask.is_active.is_(True))))
    subs = {
        s.task_id: s
        for s in db.scalars(
            select(VizuMultilevelWritingSubmission).where(VizuMultilevelWritingSubmission.attempt_id == attempt_id)
        )
    }
    for task in tasks:
        sub = subs.get(task.id)
        if sub is None:
            sub = VizuMultilevelWritingSubmission(attempt_id=attempt_id, task_id=task.id, content="", word_count=0)
            db.add(sub)
        sub.evaluation_status = PENDING


def run_for_attempt(attempt_id: UUID) -> None:
    """Background job: evaluates every PENDING/FAILED Aufgabe of the attempt
    (in parallel), stores the results, then recomputes the attempt's
    Schreiben score/level and the overall result. Uses its own session."""
    db = SessionLocal()
    try:
        subs = list(
            db.scalars(
                select(VizuMultilevelWritingSubmission)
                .where(
                    VizuMultilevelWritingSubmission.attempt_id == attempt_id,
                    VizuMultilevelWritingSubmission.evaluation_status.in_([PENDING, FAILED]),
                )
                .options(
                    joinedload(VizuMultilevelWritingSubmission.task).joinedload(VizuMultilevelWritingTask.rubric_criteria)
                )
            ).unique()
        )
        # Snapshot everything the workers need BEFORE claiming (a commit
        # expires ORM objects; threads must never lazy-load).
        specs = {s.id: (_task_spec(s.task), s.content, s.word_count) for s in subs}
        claimed = [sub_id for sub_id in specs if _claim(db, sub_id)]
        if not claimed:
            return

        results: dict = {}
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {
                sub_id: pool.submit(_evaluate, specs[sub_id][0], specs[sub_id][1], specs[sub_id][2])
                for sub_id in claimed
                if specs[sub_id][1].strip()
            }
            for sub_id, future in futures.items():
                try:
                    results[sub_id] = future.result()
                except Exception as exc:  # recorded per Aufgabe, retried later
                    results[sub_id] = exc

        for sub_id in claimed:
            sub = db.get(VizuMultilevelWritingSubmission, sub_id)
            spec, text, _wc = specs[sub_id]
            outcome = results.get(sub_id) if text.strip() else _empty_result(spec)
            if isinstance(outcome, Exception) or outcome is None:
                sub.evaluation_status = FAILED
                sub.evaluation_error = str(outcome)[:500]
            else:
                _store(db, sub, outcome)
        db.commit()

        attempt = db.get(VizuMultilevelAttempt, attempt_id)
        if attempt is not None:
            from app.services.teacher.vizu_multilevel_writing_review_service import _recompute_attempt
            from app.services.vizu_multilevel import service as flow

            _recompute_attempt(db, attempt)
            db.commit()
            flow.refresh_overall(db, attempt)
    finally:
        db.close()


# ============================================================
# Read model for the student
# ============================================================


def evaluation_status(subs: list[VizuMultilevelWritingSubmission]) -> str:
    """DONE when every Aufgabe is evaluated; FAILED when nothing is still
    running and at least one failed (retry possible); otherwise PENDING."""
    statuses = [s.evaluation_status for s in subs]
    if statuses and all(x == DONE for x in statuses):
        return DONE
    if statuses and FAILED in statuses and not any(x in (PENDING, RUNNING) for x in statuses):
        return FAILED
    return PENDING


def _summary(tasks: list[dict]) -> dict:
    """Overall feedback built from the student's REAL per-task results:
    strongest / weakest rubric areas (by percentage across all tasks), the
    most frequent error categories and the weakest task's next steps."""
    areas: dict[str, list[float]] = {}
    for task in tasks:
        for c in task["criteria"]:
            key = c["name"].split(" ")[0].split("/")[0]
            areas.setdefault(key, []).append(c["score"] / c["max"] if c["max"] else 0)
    ranked = sorted(((sum(v) / len(v), k) for k, v in areas.items()), reverse=True)
    good = [f"{name}: durchschnittlich {round(pct * 100)} % der Punkte." for pct, name in ranked[:2] if pct >= 0.6]
    strengths = [s for task in tasks for s in task["strengths"]][:2]
    improve = [f"{name}: nur {round(pct * 100)} % der Punkte." for pct, name in ranked[::-1][:2] if pct < 0.75]
    categories: dict[str, int] = {}
    for task in tasks:
        for e in task["errors"]:
            if e.get("category"):
                categories[e["category"]] = categories.get(e["category"], 0) + 1
    if categories:
        top = max(categories, key=categories.get)
        improve.append(f"Häufigste Fehlerart: {top} ({categories[top]}x in deinen Texten).")
    weakest = min(tasks, key=lambda t: t["score"] / t["max_score"] if t["max_score"] else 0) if tasks else None
    return {
        "good": (good + strengths) or ["Du hast alle Aufgaben bearbeitet — darauf kannst du aufbauen."],
        "improve": improve or ["Halte dein Niveau und achte weiter auf Genauigkeit."],
        "next": (weakest["next_steps"] if weakest else [])[:3],
    }


def build_student_result(db: Session, attempt: VizuMultilevelAttempt) -> dict:
    tasks = list(
        db.scalars(
            select(VizuMultilevelWritingTask)
            .where(VizuMultilevelWritingTask.is_active.is_(True))
            .order_by(VizuMultilevelWritingTask.order_index)
        )
    )
    subs = {
        s.task_id: s
        for s in db.scalars(
            select(VizuMultilevelWritingSubmission).where(VizuMultilevelWritingSubmission.attempt_id == attempt.id)
        )
    }
    relevant = [subs[t.id] for t in tasks if t.id in subs]
    status = evaluation_status(relevant) if attempt.schreiben_submitted_at else "NOT_SUBMITTED"
    done = sum(1 for s in relevant if s.evaluation_status == DONE)
    payload = {
        "status": status,
        "evaluated": done,
        "total_tasks": len(tasks),
        "total_score": None,
        "max_score": sum(t.points for t in tasks),
        "tasks": [],
        "summary": None,
    }
    if status != DONE:
        return payload

    task_results = []
    for task in tasks:
        sub = subs[task.id]
        fb = sub.ai_feedback or {}
        task_results.append(
            {
                "task_id": task.id,
                "order_index": task.order_index,
                "title": task.title,
                "score": sub.teacher_score or 0,
                "max_score": task.points,
                "word_count": sub.word_count,
                "criteria": fb.get("criteria", []),
                "strengths": fb.get("strengths", []),
                "errors": fb.get("errors", []),
                "feedback": fb.get("feedback", ""),
                "next_steps": fb.get("next_steps", []),
            }
        )
    payload["tasks"] = task_results
    payload["total_score"] = sum(t["score"] for t in task_results)
    payload["summary"] = _summary(task_results)
    return payload
