from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


# ============================================================
# Overview — stat cards
# ============================================================


class VizuMockOverviewStats(BaseSchema):
    total_attempts: int
    today_attempts: int
    week_attempts: int
    month_attempts: int
    completed_attempts: int
    in_progress_attempts: int
    # None when there are no completed attempts with a lesen_score yet —
    # never a fabricated 0/placeholder value.
    average_score_percent: float | None
    most_common_level: str | None


# ============================================================
# Test Faolligi — activity trend
# ============================================================


class VizuMockActivityPoint(BaseSchema):
    label: str
    started: int
    completed: int


class VizuMockActivityStats(BaseSchema):
    days: int
    points: list[VizuMockActivityPoint]
    completion_rate_percent: float | None
    average_duration_minutes: float | None


# ============================================================
# Aniqlangan darajalar + Kompetenz natijalari
# ============================================================


class VizuMockLevelBucket(BaseSchema):
    level: str
    count: int
    percent: float


class VizuMockCompetencyStat(BaseSchema):
    skill: str
    average_percent: float | None
    submitted_count: int
    most_common_level: str | None


class VizuMockLevelAnalytics(BaseSchema):
    level_distribution: list[VizuMockLevelBucket]
    total_leveled: int
    competencies: list[VizuMockCompetencyStat]


# ============================================================
# Comprehensive Analytics tab
# ============================================================


class VizuMockTimeAnalytics(BaseSchema):
    average_completion_minutes: float | None
    abandonment_rate_percent: float | None


class VizuMockAnalytics(BaseSchema):
    overview: VizuMockOverviewStats
    activity_7d: VizuMockActivityStats
    activity_30d: VizuMockActivityStats
    level_analytics: VizuMockLevelAnalytics
    time_analytics: VizuMockTimeAnalytics


# ============================================================
# Recent Tests / Results — paginated attempts list
# ============================================================


class VizuMockAdminAttemptItem(BaseSchema):
    id: UUID
    user_id: UUID
    student_name: str
    username: str
    email: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    duration_minutes: float | None
    lesen_level: str | None
    hoeren_level: str | None
    schreiben_level: str | None
    sprechen_level: str | None
    overall_level: str | None
    lesen_score: int | None


class VizuMockAdminAttemptsPage(BaseSchema):
    items: list[VizuMockAdminAttemptItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================
# Hören Audio management
# ============================================================


class VizuMockAudioCreate(BaseSchema):
    title: str
    audio_url: str
    duration_seconds: int | None = None
    task_id: UUID | None = None


class VizuMockAudioUpdate(BaseSchema):
    title: str | None = None
    audio_url: str | None = None
    duration_seconds: int | None = None
    task_id: UUID | None = None
    is_active: bool | None = None


class VizuMockAudioResponse(BaseSchema):
    id: UUID
    title: str
    audio_url: str
    duration_seconds: int | None
    task_id: UUID | None
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
