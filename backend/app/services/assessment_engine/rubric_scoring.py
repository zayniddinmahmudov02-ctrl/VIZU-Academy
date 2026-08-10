"""The universal rubric-scoring layer — shared by every skill that's
graded by admin-defined criteria rather than auto-scored (Schreiben today,
Sprechen too). One function, one place that ever clamps a score against
its criterion's max and recomputes the total: neither writing_service nor
speaking_service (nor an AI response, nor a teacher's typed-in number) is
ever trusted to have already done this correctly."""

from app.models.writing_rubric_criterion import WritingRubricCriterion


def clamp_rubric_scores(
    raw_scores: dict,
    criteria: list[WritingRubricCriterion],
    max_points: int,
) -> tuple[dict[str, int], int]:
    """`raw_scores` may be keyed by criterion id (teacher review payloads)
    or by criterion name (AI responses) — whichever key matches a given
    criterion is used; unmatched/missing criteria default to 0. Returns
    (scores keyed by criterion id as strings, total clamped to max_points)."""
    clamped: dict[str, int] = {}
    total = 0
    for criterion in criteria:
        raw = raw_scores.get(str(criterion.id), raw_scores.get(criterion.name, 0))
        try:
            score = int(raw)
        except (TypeError, ValueError):
            score = 0
        score = max(0, min(score, criterion.max_score))
        clamped[str(criterion.id)] = score
        total += score
    total = min(total, max_points)
    return clamped, total
