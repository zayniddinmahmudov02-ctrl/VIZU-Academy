"""VIZU-Multilevel Lesen content import from a structured JSON file
(`app/content/vizu_multilevel/lesen.json`).

Importing REPLACES the Lesen content: only `skill = LESEN` tasks (and, by
cascade, their questions/options) are removed, then the dataset is
inserted — all in one transaction, so a failure rolls back and leaves the
previous content untouched. Re-importing an identical dataset is detected
and does nothing (no duplicates, no churn). Hören, Schreiben, Sprechen,
courses and attempts are never touched; attempts keep their stored
Lesen score / level / counts.

The internal CEFR level of each Aufgabe is derived from its position
(the first fifth = A1, ... the last fifth = C1) and is admin-side data
only — it is never sent to students."""

import json
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.models.vizu_multilevel_content import (
    CEFR_LEVELS,
    SKILL_LESEN,
    VizuMultilevelOption,
    VizuMultilevelQuestion,
    VizuMultilevelTask,
)

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "content" / "vizu_multilevel" / "lesen.json"

# JSON question type -> stored question_type. All are graded identically
# (exactly one correct option); the type only describes the task format.
TYPE_MAP = {
    "multiple_choice": "MULTIPLE_CHOICE",
    "richtig_falsch": "TRUE_FALSE",
    "lueckentext": "CLOZE_TEXT",
    "ueberschrift_zuordnen": "HEADLINE_MATCH",
    "anzeige_zuordnen": "AD_MATCH",
    "passende_information": "INFO_MATCH",
    "textverstaendnis": "COMPREHENSION",
}


class LesenImportError(Exception):
    """The dataset is invalid — nothing was changed."""


def load_default() -> dict:
    return json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))


def level_for_position(order: int, total: int) -> str:
    """Internal level of the order-th Aufgabe out of `total` (20 -> 4 each)."""
    return CEFR_LEVELS[min(len(CEFR_LEVELS) - 1, (order - 1) * len(CEFR_LEVELS) // total)]


def _parse(data: dict) -> list[dict]:
    """Validates the dataset and returns normalised Aufgaben."""
    if not isinstance(data, dict) or data.get("module") != "lesen":
        raise LesenImportError('module must be "lesen".')
    aufgaben = data.get("aufgaben")
    if not isinstance(aufgaben, list) or not aufgaben:
        raise LesenImportError("aufgaben must be a non-empty list.")

    points_per_question = data.get("points_per_question")
    parsed: list[dict] = []
    seen_orders: set[int] = set()
    seen_question_orders: set[int] = set()
    total_points = 0

    for item in aufgaben:
        order = item.get("order")
        text = (item.get("text") or "").strip()
        questions = item.get("questions") or []
        if not isinstance(order, int) or order < 1 or order in seen_orders:
            raise LesenImportError(f"Aufgabe order {order!r} is missing or duplicated.")
        seen_orders.add(order)
        if not text:
            raise LesenImportError(f"Aufgabe {order} has no text.")
        if not questions:
            raise LesenImportError(f"Aufgabe {order} has no question.")

        parsed_questions = []
        for question in questions:
            q_order = question.get("order")
            if not isinstance(q_order, int) or q_order < 1 or q_order in seen_question_orders:
                raise LesenImportError(f"Question order {q_order!r} is missing or duplicated.")
            seen_question_orders.add(q_order)

            q_type = TYPE_MAP.get(question.get("type"))
            if q_type is None:
                raise LesenImportError(f"Question {q_order}: unknown type {question.get('type')!r}.")
            prompt = (question.get("question") or "").strip()
            if not prompt:
                raise LesenImportError(f"Question {q_order} has no question text.")

            options = question.get("options") or []
            keys = [o.get("key") for o in options]
            if len(options) != 4 or keys != ["A", "B", "C", "D"] or any(not (o.get("text") or "").strip() for o in options):
                raise LesenImportError(f"Question {q_order} must have exactly the 4 options A-D with text.")
            correct = question.get("correct_answer")
            if correct not in keys:
                raise LesenImportError(f"Question {q_order}: correct_answer {correct!r} is not one of A-D.")

            points = question.get("points")
            if points != points_per_question or not isinstance(points, (int, float)) or points <= 0:
                raise LesenImportError(f"Question {q_order}: points must equal points_per_question.")
            total_points += points

            parsed_questions.append(
                {
                    "order": q_order,
                    "type": q_type,
                    "prompt": prompt,
                    "points": float(points),
                    "options": [(o["text"].strip(), o["key"] == correct) for o in options],
                }
            )
        parsed.append({"order": order, "text": text, "questions": parsed_questions})

    parsed.sort(key=lambda a: a["order"])
    question_count = sum(len(a["questions"]) for a in parsed)
    if data.get("total_questions") != question_count:
        raise LesenImportError("total_questions does not match the number of questions.")
    if data.get("max_score") != total_points:
        raise LesenImportError("max_score does not match the sum of the question points.")
    for a in parsed:
        a["level"] = level_for_position(a["order"], len(parsed))
    return parsed


def _signature_of_parsed(parsed: list[dict]) -> list:
    return [
        (
            a["order"],
            a["level"],
            a["text"],
            [(q["order"], q["type"], q["prompt"], q["points"], q["options"]) for q in a["questions"]],
        )
        for a in parsed
    ]


def _signature_of_db(db: Session) -> list:
    tasks = db.scalars(
        select(VizuMultilevelTask)
        .where(VizuMultilevelTask.skill == SKILL_LESEN)
        .options(joinedload(VizuMultilevelTask.questions).joinedload(VizuMultilevelQuestion.options))
        .order_by(VizuMultilevelTask.order_index)
    ).unique()
    return [
        (
            t.order_index,
            t.level,
            (t.passage_text or "").strip(),
            [
                (
                    q.order_index,
                    q.question_type,
                    q.prompt,
                    float(q.points),
                    [(o.option_text, o.is_correct) for o in q.options],
                )
                for q in t.questions
                if q.is_active
            ],
        )
        for t in tasks
        if t.is_published
    ]


def import_lesen(db: Session, data: dict) -> dict:
    parsed = _parse(data)  # validate everything BEFORE touching the database

    if _signature_of_db(db) == _signature_of_parsed(parsed):
        return {"status": "unchanged", "aufgaben": len(parsed), "questions": sum(len(a["questions"]) for a in parsed)}

    try:
        # Lesen only. Questions/options go via the FK cascade; Hören etc. are
        # different skills and are not matched by this statement.
        db.execute(delete(VizuMultilevelTask).where(VizuMultilevelTask.skill == SKILL_LESEN))
        for a in parsed:
            task = VizuMultilevelTask(
                skill=SKILL_LESEN, level=a["level"], order_index=a["order"], passage_text=a["text"], is_published=True
            )
            for q in a["questions"]:
                question = VizuMultilevelQuestion(
                    question_type=q["type"], prompt=q["prompt"], order_index=q["order"], points=q["points"], is_active=True
                )
                for index, (text, is_correct) in enumerate(q["options"], start=1):
                    question.options.append(VizuMultilevelOption(option_text=text, is_correct=is_correct, order_index=index))
                task.questions.append(question)
            db.add(task)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"status": "imported", "aufgaben": len(parsed), "questions": sum(len(a["questions"]) for a in parsed)}


def import_default(db: Session) -> dict:
    return import_lesen(db, load_default())
