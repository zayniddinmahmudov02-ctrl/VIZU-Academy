"""CSV import for VIZU-Multilevel's Hören module — imports Aufgabe/question/
option content directly into the existing VizuMultilevelTask/VizuMultilevelQuestion/
VizuMultilevelOption tables (skill=HOEREN), the exact same architecture Lesen
already uses (see hoeren_service.py, scripts/seed_vizu_multilevel_hoeren.py).
No new tables, and completely independent of the regular course lesson's
Quiz/QuizQuestion system — VIZU-Multilevel and the regular course content are
deliberately separate products (see VizuMultilevelAudio's own docstring for
the same rationale).

CSV columns (case-insensitive): aufgabe (or task), question, type,
option_a, option_b, option_c, option_d, correct_answer, level, points,
order.

`level` (A1-C1) is the authoritative source for a question's points —
LEVEL_POINTS below maps it to the fixed scoring rule (A1=0.5, A2=1.0,
B1=1.5, B2=2.0, C1=2.5). A CSV `points` column is accepted but ignored
for scoring, so an admin can never accidentally desync a question's
score from its level by hand-editing one column and not the other.
Every question within one Aufgabe must share the same level (matching
the existing 1-Aufgabe-1-level content shape).

`type` accepts MULTIPLE_CHOICE, TRUE_FALSE (or "Richtig/Falsch"), and
CLOZE (or "Lückentext") — stored as VizuMultilevelQuestion.question_type
exactly like scripts/seed_vizu_multilevel_hoeren.py already does; grading is
always option-based (exactly one correct option), regardless of type.

Idempotent: a task (Aufgabe) is matched by its position among the CSV's
distinct `aufgabe` values (1st distinct label -> order_index 1, ...), a
question by (task_id, position within its Aufgabe), an option by
(question_id, its A-D slot) — same natural-key convention as
seed_vizu_multilevel_hoeren.py, so re-importing an edited CSV updates existing
rows in place instead of duplicating them.
"""

import csv
import io

from sqlalchemy.orm import Session

from app.models.vizu_multilevel_content import SKILL_HOEREN, VizuMultilevelOption, VizuMultilevelQuestion, VizuMultilevelTask

LEVEL_POINTS = {"A1": 0.5, "A2": 1.0, "B1": 1.5, "B2": 2.0, "C1": 2.5}
OPTION_LETTER_TO_INDEX = {"A": 1, "B": 2, "C": 3, "D": 4}


class CsvImportError(Exception):
    pass


def _normalize_question_type(raw_type: str) -> str:
    value = (raw_type or "MULTIPLE_CHOICE").strip().upper().replace("/", "_").replace("Ü", "U")
    if value in ("TRUE_FALSE", "RICHTIG_FALSCH"):
        return "TRUE_FALSE"
    if value in ("CLOZE", "CLOZE_TEXT", "LUCKENTEXT"):
        return "CLOZE_TEXT"
    return "MULTIPLE_CHOICE"


def import_rows(db: Session, rows: list[dict]) -> dict:
    if not rows:
        raise CsvImportError("CSV contains no rows.")

    groups: dict[str, list[dict]] = {}
    group_order: list[str] = []
    for i, row in enumerate(rows, start=1):
        aufgabe = (row.get("aufgabe") or row.get("task") or "").strip()
        if not aufgabe:
            raise CsvImportError(f"Row {i}: 'aufgabe' (or 'task') is required.")
        if aufgabe not in groups:
            groups[aufgabe] = []
            group_order.append(aufgabe)
        groups[aufgabe].append(row)

    tasks_created = 0
    tasks_updated = 0
    questions_created = 0
    questions_updated = 0

    for task_order, aufgabe in enumerate(group_order, start=1):
        group_rows = groups[aufgabe]

        levels_in_group = {(r.get("level") or "").strip().upper() for r in group_rows}
        levels_in_group.discard("")
        if len(levels_in_group) != 1:
            raise CsvImportError(
                f"Aufgabe '{aufgabe}': all its questions must share exactly one 'level' column "
                f"(found: {sorted(levels_in_group) or ['none']})."
            )
        level = next(iter(levels_in_group))
        if level not in LEVEL_POINTS:
            raise CsvImportError(f"Aufgabe '{aufgabe}': unknown level '{level}' — must be one of A1, A2, B1, B2, C1.")
        points = LEVEL_POINTS[level]

        task = db.query(VizuMultilevelTask).filter(
            VizuMultilevelTask.skill == SKILL_HOEREN, VizuMultilevelTask.order_index == task_order
        ).first()
        is_new_task = task is None
        if task is None:
            task = VizuMultilevelTask(skill=SKILL_HOEREN, order_index=task_order)
            db.add(task)
        task.level = level
        task.passage_text = None
        db.flush()
        tasks_created += int(is_new_task)
        tasks_updated += int(not is_new_task)

        for q_order, row in enumerate(group_rows, start=1):
            question_text = (row.get("question") or "").strip()
            if not question_text:
                raise CsvImportError(f"Aufgabe '{aufgabe}', question {q_order}: 'question' is required.")
            correct_letter = (row.get("correct_answer") or "").strip().upper()
            if correct_letter not in OPTION_LETTER_TO_INDEX:
                raise CsvImportError(f"Aufgabe '{aufgabe}', question {q_order}: 'correct_answer' must be A, B, C, or D.")

            question = db.query(VizuMultilevelQuestion).filter(
                VizuMultilevelQuestion.task_id == task.id, VizuMultilevelQuestion.order_index == q_order
            ).first()
            is_new_question = question is None
            if question is None:
                question = VizuMultilevelQuestion(task_id=task.id, order_index=q_order)
                db.add(question)
            question.question_type = _normalize_question_type(row.get("type", ""))
            question.passage_text = None
            question.prompt = question_text
            question.points = points
            db.flush()
            questions_created += int(is_new_question)
            questions_updated += int(not is_new_question)

            any_option = False
            for letter, opt_index in OPTION_LETTER_TO_INDEX.items():
                text = row.get(f"option_{letter.lower()}")
                if text is None or text.strip() == "":
                    continue
                any_option = True
                option = db.query(VizuMultilevelOption).filter(
                    VizuMultilevelOption.question_id == question.id, VizuMultilevelOption.order_index == opt_index
                ).first()
                if option is None:
                    option = VizuMultilevelOption(question_id=question.id, order_index=opt_index)
                    db.add(option)
                option.option_text = text.strip()
                option.is_correct = letter == correct_letter

            if not any_option:
                raise CsvImportError(f"Aufgabe '{aufgabe}', question {q_order}: at least one option_a-d is required.")

    db.commit()
    return {
        "tasks_created": tasks_created,
        "tasks_updated": tasks_updated,
        "questions_created": questions_created,
        "questions_updated": questions_updated,
        "total_questions": questions_created + questions_updated,
    }


def import_csv_text(db: Session, csv_text: str) -> dict:
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = [{(k or "").strip().lower(): v for k, v in raw_row.items()} for raw_row in reader]
    return import_rows(db, rows)
