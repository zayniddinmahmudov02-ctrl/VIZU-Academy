from uuid import UUID

from app.schemas.base import BaseSchema

from .schema import VizuMockAnswerSubmit, VizuMockLevelScore, VizuMockQuestionPublic


class VizuMockHoerenTaskPublic(BaseSchema):
    """Same shape as VizuMockTaskPublic (Lesen), plus `audio_url` — the
    one field a Hören Aufgabe needs that a Lesen Aufgabe doesn't. Never
    exposes the audio's filename/admin metadata, just the playable URL;
    the script/transcript is never sent to the client at all (there is
    no field for it on VizuMockTask/VizuMockQuestion for Hören content —
    passage_text simply stays None)."""

    id: UUID
    skill: str
    level: str
    order_index: int
    passage_text: str | None
    audio_url: str | None
    questions: list[VizuMockQuestionPublic]


class VizuMockHoerenSubmitRequest(BaseSchema):
    answers: list[VizuMockAnswerSubmit]


class VizuMockHoerenResult(BaseSchema):
    attempt_id: UUID
    total_points: float
    max_points: float
    level_scores: list[VizuMockLevelScore]
    hoeren_level: str | None
