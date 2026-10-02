"""VIZU-Multilevel Hören content import from `app/content/vizu_multilevel/
hoeren.json`: 5 Aufgaben x 4 multiple-choice questions, 1 point each = 20.

Same contract as the Lesen import (lesen_json_import_service): replaces ONLY
the Hören tasks, in one transaction, and is a no-op for an identical
dataset. Additionally the uploaded audio is preserved: audio rows are keyed
by Aufgabe number, not by task id, so replacing the questions never loses
or detaches an uploaded file. `audio_script` is stored as the task's
transcript — admin-side only, never sent to students."""

import json
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.models.vizu_multilevel_content import (
    SKILL_HOEREN,
    VizuMultilevelOption,
    VizuMultilevelQuestion,
    VizuMultilevelTask,
)
from app.services.vizu_multilevel.lesen_json_import_service import TYPE_MAP, level_for_position

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "content" / "vizu_multilevel" / "hoeren.json"


class HoerenImportError(Exception):
    """The dataset is invalid — nothing was changed."""


def load_default() -> dict:
    return json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))


def _parse(data: dict) -> list[dict]:
    if not isinstance(data, dict) or data.get("module") != "hoeren":
        raise HoerenImportError('module must be "hoeren".')
    aufgaben = data.get("aufgaben")
    if not isinstance(aufgaben, list) or not aufgaben:
        raise HoerenImportError("aufgaben must be a non-empty list.")

    points_per_question = data.get("points_per_question")
    parsed: list[dict] = []
    seen_orders: set[int] = set()
    seen_question_orders: set[int] = set()
    total_points = 0

    for item in aufgaben:
        order = item.get("order")
        script = (item.get("audio_script") or "").strip()
        if not isinstance(order, int) or order < 1 or order in seen_orders:
            raise HoerenImportError(f"Aufgabe order {order!r} is missing or duplicated.")
        seen_orders.add(order)
        if not script:
            raise HoerenImportError(f"Aufgabe {order} has no audio_script.")
        questions = item.get("questions") or []
        if not questions:
            raise HoerenImportError(f"Aufgabe {order} has no question.")

        parsed_questions = []
        for question in questions:
            q_order = question.get("order")
            if not isinstance(q_order, int) or q_order < 1 or q_order in seen_question_orders:
                raise HoerenImportError(f"Question order {q_order!r} is missing or duplicated.")
            seen_question_orders.add(q_order)
            q_type = TYPE_MAP.get(question.get("type"))
            if q_type is None:
                raise HoerenImportError(f"Question {q_order}: unknown type {question.get('type')!r}.")
            prompt = (question.get("question") or "").strip()
            if not prompt:
                raise HoerenImportError(f"Question {q_order} has no question text.")
            options = question.get("options") or []
            keys = [o.get("key") for o in options]
            if len(options) != 4 or keys != ["A", "B", "C", "D"] or any(not (o.get("text") or "").strip() for o in options):
                raise HoerenImportError(f"Question {q_order} must have exactly the 4 options A-D with text.")
            correct = question.get("correct_answer")
            if correct not in keys:
                raise HoerenImportError(f"Question {q_order}: correct_answer {correct!r} is not one of A-D.")
            points = question.get("points")
            if not isinstance(points, (int, float)) or points <= 0 or points != points_per_question:
                raise HoerenImportError(f"Question {q_order}: points must equal points_per_question.")
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
        parsed.append({"order": order, "script": script, "questions": parsed_questions})

    parsed.sort(key=lambda a: a["order"])
    if data.get("total_questions") != sum(len(a["questions"]) for a in parsed):
        raise HoerenImportError("total_questions does not match the number of questions.")
    if data.get("max_score") != total_points:
        raise HoerenImportError("max_score does not match the sum of the question points.")
    for a in parsed:
        a["level"] = level_for_position(a["order"], len(parsed))
    return parsed


def _signature_of_parsed(parsed: list[dict]) -> list:
    return [
        (a["order"], a["level"], a["script"], [(q["order"], q["type"], q["prompt"], q["points"], q["options"]) for q in a["questions"]])
        for a in parsed
    ]


def _signature_of_db(db: Session) -> list:
    tasks = db.scalars(
        select(VizuMultilevelTask)
        .where(VizuMultilevelTask.skill == SKILL_HOEREN)
        .options(joinedload(VizuMultilevelTask.questions).joinedload(VizuMultilevelQuestion.options))
        .order_by(VizuMultilevelTask.order_index)
    ).unique()
    return [
        (
            t.order_index,
            t.level,
            (t.transcript or "").strip(),
            [
                (q.order_index, q.question_type, q.prompt, float(q.points), [(o.option_text, o.is_correct) for o in q.options])
                for q in t.questions
            ],
        )
        for t in tasks
        if t.is_published
    ]


def import_hoeren(db: Session, data: dict) -> dict:
    parsed = _parse(data)  # validate everything BEFORE touching the database
    summary = {"aufgaben": len(parsed), "questions": sum(len(a["questions"]) for a in parsed)}

    if _signature_of_db(db) == _signature_of_parsed(parsed):
        return {"status": "unchanged", **summary}

    try:
        # Hören tasks only; questions/options go via the FK cascade. Audio rows
        # are keyed by Aufgabe number and are not touched (their optional
        # task link is set to NULL by the FK and restored below).
        db.execute(delete(VizuMultilevelTask).where(VizuMultilevelTask.skill == SKILL_HOEREN))
        tasks_by_order: dict[int, VizuMultilevelTask] = {}
        for a in parsed:
            task = VizuMultilevelTask(
                skill=SKILL_HOEREN, level=a["level"], order_index=a["order"], transcript=a["script"], is_published=True
            )
            for q in a["questions"]:
                question = VizuMultilevelQuestion(
                    question_type=q["type"], prompt=q["prompt"], order_index=q["order"], points=q["points"], is_active=True
                )
                for index, (text, is_correct) in enumerate(q["options"], start=1):
                    question.options.append(VizuMultilevelOption(option_text=text, is_correct=is_correct, order_index=index))
                task.questions.append(question)
            db.add(task)
            tasks_by_order[a["order"]] = task
        db.flush()

        from app.models.vizu_multilevel_audio import VizuMultilevelAudio

        for audio in db.scalars(select(VizuMultilevelAudio).where(VizuMultilevelAudio.aufgabe_number.isnot(None))):
            task = tasks_by_order.get(audio.aufgabe_number)
            audio.task_id = task.id if task else None
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"status": "imported", **summary}


def import_default(db: Session) -> dict:
    return import_hoeren(db, load_default())
