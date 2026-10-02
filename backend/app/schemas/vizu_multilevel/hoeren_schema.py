from uuid import UUID

from app.schemas.base import BaseSchema

from .schema import VizuMultilevelAnswerSubmit, VizuMultilevelLevelScore, VizuMultilevelQuestionPublic


class VizuMultilevelHoerenTaskPublic(BaseSchema):
    """Same shape as VizuMultilevelTaskPublic (Lesen), plus `audio_url` — the
    one field a Hören Aufgabe needs that a Lesen Aufgabe doesn't. Never
    exposes the audio's filename/admin metadata, just the playable URL;
    the script/transcript is never sent to the client at all (there is
    no field for it on VizuMultilevelTask/VizuMultilevelQuestion for Hören content —
    passage_text simply stays None)."""

    id: UUID
    skill: str
    order_index: int
    passage_text: str | None
    audio_url: str | None
    questions: list[VizuMultilevelQuestionPublic]


class VizuMultilevelHoerenSubmitRequest(BaseSchema):
    answers: list[VizuMultilevelAnswerSubmit]


class VizuMultilevelHoerenResult(BaseSchema):
    attempt_id: UUID
    total_points: float
    max_points: float
    level_scores: list[VizuMultilevelLevelScore]
    hoeren_level: str | None
