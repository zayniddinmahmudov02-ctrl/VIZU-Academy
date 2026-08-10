"""Task-type validator/scorer registry for the universal Assessment engine.

Every one of the 13 task types is registered to a scoring *handler* —
there are only 5 distinct scoring algorithms (single-correct-option,
multi-correct-option, matching, ordering, free-text), so this maps many
task types onto few handler classes rather than writing 13 near-identical
ones. Adding a genuinely new task type (a 14th) only ever means: add its
TASK_TYPE_* constant, pick or write a handler, and add one line to
TASK_TYPE_REGISTRY below — no existing handler or task type is touched.

`answer_data` on Answer is JSON text (mirrors the existing
MockQuestionAnswer.answer_data convention in app/services/mock_exam/
attempt_service.py):
  - single/multi-select types: JSON list of selected TaskOption id strings
  - matching-family types:     JSON object {option_id: submitted_match_value}
  - SENTENCE_ORDERING:         JSON list of TaskOption id strings, in the
                                order the student placed them
  - CLOZE_TEXT / SHORT_ANSWER: JSON string (the free-text answer)
"""

import json
from abc import ABC, abstractmethod

from app.models.assessment_task import (
    TYPE_ADVERTISEMENT_MATCHING,
    TYPE_CATEGORY_SORTING,
    TYPE_CLOZE_TEXT,
    TYPE_DRAG_DROP,
    TYPE_GAP_MATCHING,
    TYPE_HEADING_MATCHING,
    TYPE_IMAGE_SELECTION,
    TYPE_MULTIPLE_CHOICE,
    TYPE_MULTIPLE_SELECT,
    TYPE_SENTENCE_ORDERING,
    TYPE_SHORT_ANSWER,
    TYPE_TEXT_MATCHING,
    TYPE_TRUE_FALSE,
)
from app.models.task_question import TaskQuestion


def _safe_json_loads(raw: str | None):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


class TaskTypeHandler(ABC):
    """One scoring algorithm, shared by every task type registered to it."""

    @abstractmethod
    def score(self, question: TaskQuestion, answer_data: str | None) -> tuple[bool | None, int]:
        """Returns (is_correct, points_earned). is_correct is None when the
        answer can't be auto-graded (never happens for the 13 supported
        types today, but keeps the contract honest for a future free-text
        essay-style type that would need manual/AI grading instead)."""

    def validate_task(self, questions: list[TaskQuestion]) -> list[str]:
        """Admin-builder-time sanity checks — e.g. "needs at least one
        correct option". Returns a list of human-readable problems; an
        empty list means the task is publishable."""
        return []


class SingleCorrectOptionHandler(TaskTypeHandler):
    """TRUE_FALSE, MULTIPLE_CHOICE — exactly one option must be correct;
    the student's single selection must match it exactly."""

    def score(self, question: TaskQuestion, answer_data: str | None) -> tuple[bool | None, int]:
        parsed = _safe_json_loads(answer_data)
        if not isinstance(parsed, list) or len(parsed) != 1:
            return False, 0

        correct_ids = {str(o.id) for o in question.options if o.is_correct}
        is_correct = {str(parsed[0])} == correct_ids
        return is_correct, question.points if is_correct else 0

    def validate_task(self, questions: list[TaskQuestion]) -> list[str]:
        errors = []
        for q in questions:
            correct_count = sum(1 for o in q.options if o.is_correct)
            if correct_count != 1:
                errors.append(f'"{q.prompt[:40]}" must have exactly one correct option (has {correct_count}).')
        return errors


class MultiCorrectOptionHandler(TaskTypeHandler):
    """MULTIPLE_SELECT, IMAGE_SELECTION — one or more options may be
    correct; full credit only if the submitted set exactly matches."""

    def score(self, question: TaskQuestion, answer_data: str | None) -> tuple[bool | None, int]:
        parsed = _safe_json_loads(answer_data)
        if not isinstance(parsed, list):
            return False, 0

        correct_ids = {str(o.id) for o in question.options if o.is_correct}
        submitted_ids = {str(v) for v in parsed}
        is_correct = submitted_ids == correct_ids
        return is_correct, question.points if is_correct else 0

    def validate_task(self, questions: list[TaskQuestion]) -> list[str]:
        errors = []
        for q in questions:
            if not any(o.is_correct for o in q.options):
                errors.append(f'"{q.prompt[:40]}" needs at least one correct option.')
        return errors


class MatchingHandler(TaskTypeHandler):
    """HEADING_MATCHING, ADVERTISEMENT_MATCHING, TEXT_MATCHING,
    GAP_MATCHING, DRAG_DROP, CATEGORY_SORTING — each option is a left-side
    item with a correct right-side pairing (match_value). Partial credit:
    points are split evenly across the question's options, one share per
    correctly-paired option."""

    def score(self, question: TaskQuestion, answer_data: str | None) -> tuple[bool | None, int]:
        parsed = _safe_json_loads(answer_data)
        if not isinstance(parsed, dict) or not question.options:
            return False, 0

        per_item_points = question.points / len(question.options)
        earned = 0.0
        all_correct = True
        for option in question.options:
            submitted = parsed.get(str(option.id))
            if submitted is not None and submitted == option.match_value:
                earned += per_item_points
            else:
                all_correct = False

        return all_correct, round(earned)

    def validate_task(self, questions: list[TaskQuestion]) -> list[str]:
        errors = []
        for q in questions:
            if not q.options:
                errors.append(f'"{q.prompt[:40]}" has no items to match.')
            for o in q.options:
                if not o.match_value:
                    errors.append(f'"{o.option_text[:30]}" is missing its correct match.')
        return errors


class OrderingHandler(TaskTypeHandler):
    """SENTENCE_ORDERING — the admin arranges options in the correct
    sequence (option.sort_order); the student's submitted order must match
    exactly for credit."""

    def score(self, question: TaskQuestion, answer_data: str | None) -> tuple[bool | None, int]:
        parsed = _safe_json_loads(answer_data)
        if not isinstance(parsed, list):
            return False, 0

        correct_order = [str(o.id) for o in sorted(question.options, key=lambda o: o.sort_order)]
        is_correct = [str(v) for v in parsed] == correct_order
        return is_correct, question.points if is_correct else 0

    def validate_task(self, questions: list[TaskQuestion]) -> list[str]:
        return [
            f'"{q.prompt[:40]}" needs at least two items to order.'
            for q in questions
            if len(q.options) < 2
        ]


class TextAnswerHandler(TaskTypeHandler):
    """CLOZE_TEXT (one row per gap), SHORT_ANSWER — free-text exact match
    against correct_text_answer or any of alternative_answers, respecting
    case_sensitive."""

    def score(self, question: TaskQuestion, answer_data: str | None) -> tuple[bool | None, int]:
        parsed = _safe_json_loads(answer_data)
        submitted = parsed if isinstance(parsed, str) else (answer_data or "")
        submitted = submitted.strip()

        candidates = [question.correct_text_answer or ""]
        alternatives = _safe_json_loads(question.alternative_answers)
        if isinstance(alternatives, list):
            candidates.extend(str(a) for a in alternatives)

        if not question.case_sensitive:
            submitted_cmp = submitted.lower()
            candidates_cmp = [c.strip().lower() for c in candidates]
        else:
            submitted_cmp = submitted
            candidates_cmp = [c.strip() for c in candidates]

        is_correct = submitted_cmp in candidates_cmp and submitted_cmp != ""
        return is_correct, question.points if is_correct else 0

    def validate_task(self, questions: list[TaskQuestion]) -> list[str]:
        return [
            f'"{q.prompt[:40]}" has no correct answer set.'
            for q in questions
            if not q.correct_text_answer
        ]


_single_correct = SingleCorrectOptionHandler()
_multi_correct = MultiCorrectOptionHandler()
_matching = MatchingHandler()
_ordering = OrderingHandler()
_text_answer = TextAnswerHandler()

TASK_TYPE_REGISTRY: dict[str, TaskTypeHandler] = {
    TYPE_TRUE_FALSE: _single_correct,
    TYPE_MULTIPLE_CHOICE: _single_correct,
    TYPE_MULTIPLE_SELECT: _multi_correct,
    TYPE_IMAGE_SELECTION: _multi_correct,
    TYPE_HEADING_MATCHING: _matching,
    TYPE_ADVERTISEMENT_MATCHING: _matching,
    TYPE_TEXT_MATCHING: _matching,
    TYPE_GAP_MATCHING: _matching,
    TYPE_DRAG_DROP: _matching,
    TYPE_CATEGORY_SORTING: _matching,
    TYPE_SENTENCE_ORDERING: _ordering,
    TYPE_CLOZE_TEXT: _text_answer,
    TYPE_SHORT_ANSWER: _text_answer,
}


def get_handler(task_type: str) -> TaskTypeHandler:
    handler = TASK_TYPE_REGISTRY.get(task_type)
    if handler is None:
        raise ValueError(f"No scoring handler registered for task_type={task_type!r}")
    return handler
