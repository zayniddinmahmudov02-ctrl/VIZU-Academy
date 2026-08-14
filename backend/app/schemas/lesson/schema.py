from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LessonScoreComponent(BaseModel):
    label: str
    points: int
    max_points: int


class LessonQuizResult(BaseModel):
    percentage: int
    has_result: bool


class LessonScore(BaseModel):
    lesson_id: UUID
    total_score: int
    max_score: int
    percentage: int
    breakdown: dict[str, LessonScoreComponent]
    feedback: str
    strengths: list[str]
    weak_areas: list[str]
    lesson_quiz: LessonQuizResult


class LessonBase(BaseModel):
    module_id: UUID
    number: int
    title: str
    duration: int
    is_free: bool = False
    video_url: str | None = None


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    number: int | None = None
    title: str | None = None
    duration: int | None = None
    is_free: bool | None = None
    video_url: str | None = None


class LessonResponse(LessonBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    # Computed relative to the requesting user — see
    # app.services.vizu_pay.access.can_access_lesson. Never persisted;
    # always recomputed per-request so a premium purchase/expiry is
    # reflected immediately.
    is_locked: bool = False
    requires_premium: bool = False


class LessonListItem(BaseModel):
    id: str
    module_id: str
    number: int
    title: str
    duration: int
    video_url: str | None
    is_free: bool
    progress: int
    is_locked: bool = False
    requires_premium: bool = False


class LessonDetail(LessonListItem):
    audio_url: str | None


class LessonContentStatus(BaseModel):
    lesson_id: str
    number: int
    title: str
    has_video: bool
    has_grammar: bool
    has_grammar_quiz: bool
    has_vocabulary: bool
    has_lesen: bool
    has_lesen_quiz: bool
    has_hoeren: bool
    has_hoeren_quiz: bool
    has_schreiben: bool
    has_sprechen: bool
    has_lesson_quiz: bool
    # Position-based only (not the viewing admin's own access) — "would a
    # free student be locked out of this lesson", independent of has_*
    # (content can exist and still be locked for free users).
    is_locked: bool = False
