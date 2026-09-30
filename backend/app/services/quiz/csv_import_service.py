"""CSV import for the legacy Quiz/QuizQuestion/QuizOption system —
originally built to bring real Hören listening-comprehension quizzes
into a lesson (quiz_type=HOEREN, see app/models/quiz.py), but generic
over quiz_type so it can seed GRAMMAR/LESSON content the same way if
ever needed. Reuses the exact same tables/grading the legacy Quiz
system already has (server-side grading in
services/quiz/grading_service.py, student player in
frontend/.../quiz-section.tsx) — no new parallel test system.

CSV columns (case-insensitive): aufgabe (or task), question, type,
option_a, option_b, option_c, option_d, correct_answer, points, order.

`type` accepts MULTIPLE_CHOICE, TRUE_FALSE (or "Richtig/Falsch"), and
CLOZE (or "Lückentext") — CLOZE is stored as MULTIPLE_CHOICE, since in
this codebase's Quiz engine "CLOZE_TEXT" specifically means a free-text
input question (see grading_service.py's TEXT_ANSWER_TYPES), while an
option-based fill-in-the-blank (four lettered choices, exactly like
this CSV format gives) is graded identically to a normal multiple-choice
question — no information is lost, since the blank itself already lives
in the question text.

Idempotent: a question is matched by (quiz_id, order_index), an option
by (question_id, order_index) — re-importing the same CSV (or an edited
version of it) updates existing rows in place rather than duplicating
them, exactly like scripts/seed_vizu_mock_lesen.py's convention.
"""

import csv
import io
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.quiz import Quiz
from app.models.quiz_option import QuizOption
from app.models.quiz_question import QuizQuestion

OPTION_LETTER_TO_INDEX = {"A": 1, "B": 2, "C": 3, "D": 4}


class CsvImportError(Exception):
    pass


def _normalize_question_type(raw_type: str) -> str:
    value = (raw_type or "MULTIPLE_CHOICE").strip().upper().replace("/", "_").replace("Ü", "U")
    if value in ("TRUE_FALSE", "RICHTIG_FALSCH"):
        return "TRUE_FALSE"
    if value in ("CLOZE", "CLOZE_TEXT", "LUCKENTEXT"):
        # Option-based cloze — graded like MC, see module docstring.
        return "MULTIPLE_CHOICE"
    return "MULTIPLE_CHOICE"


def _get_or_create_quiz(db: Session, lesson_id: UUID, quiz_type: str, quiz_title: str) -> Quiz:
    quiz = db.query(Quiz).filter(Quiz.lesson_id == str(lesson_id), Quiz.quiz_type == quiz_type).first()
    if quiz is None:
        quiz = Quiz(lesson_id=lesson_id, quiz_type=quiz_type, title=quiz_title, is_published=True)
        db.add(quiz)
        db.flush()
    else:
        quiz.is_published = True
    return quiz


def import_rows(db: Session, lesson_id: UUID, quiz_type: str, quiz_title: str, rows: list[dict]) -> dict:
    quiz = _get_or_create_quiz(db, lesson_id, quiz_type, quiz_title)

    created_questions = 0
    updated_questions = 0

    for i, row in enumerate(rows, start=1):
        try:
            order_index = int(row.get("order") or i)
        except (TypeError, ValueError):
            raise CsvImportError(f"Row {i}: 'order' must be a number.")

        question_text = (row.get("question") or "").strip()
        if not question_text:
            raise CsvImportError(f"Row {i}: 'question' is required.")

        correct_letter = (row.get("correct_answer") or "").strip().upper()
        if correct_letter not in OPTION_LETTER_TO_INDEX:
            raise CsvImportError(f"Row {i}: 'correct_answer' must be A, B, C, or D.")

        question = (
            db.query(QuizQuestion)
            .filter(QuizQuestion.quiz_id == quiz.id, QuizQuestion.order_index == order_index)
            .first()
        )
        is_new = question is None
        if question is None:
            question = QuizQuestion(quiz_id=quiz.id, order_index=order_index)
            db.add(question)

        question.question = question_text
        question.question_type = _normalize_question_type(row.get("type", ""))
        try:
            question.points = int(row.get("points") or 1)
        except (TypeError, ValueError):
            raise CsvImportError(f"Row {i}: 'points' must be a number.")
        question.group_label = (row.get("aufgabe") or row.get("task") or "").strip() or None
        question.is_published = True
        db.flush()

        any_option = False
        for letter, opt_index in OPTION_LETTER_TO_INDEX.items():
            text = row.get(f"option_{letter.lower()}")
            if text is None or text.strip() == "":
                continue
            any_option = True
            option = (
                db.query(QuizOption)
                .filter(QuizOption.question_id == question.id, QuizOption.order_index == opt_index)
                .first()
            )
            if option is None:
                option = QuizOption(question_id=question.id, order_index=opt_index)
                db.add(option)
            option.option_text = text.strip()
            option.is_correct = letter == correct_letter

        if not any_option:
            raise CsvImportError(f"Row {i}: at least one option_a-d is required.")

        if is_new:
            created_questions += 1
        else:
            updated_questions += 1

    db.commit()
    return {
        "quiz_id": quiz.id,
        "quiz_type": quiz_type,
        "created_questions": created_questions,
        "updated_questions": updated_questions,
        "total_questions": created_questions + updated_questions,
    }


def import_csv_text(db: Session, lesson_id: UUID, quiz_type: str, quiz_title: str, csv_text: str) -> dict:
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = [{(k or "").strip().lower(): v for k, v in raw_row.items()} for raw_row in reader]
    if not rows:
        raise CsvImportError("CSV contains no rows.")
    return import_rows(db, lesson_id, quiz_type, quiz_title, rows)
