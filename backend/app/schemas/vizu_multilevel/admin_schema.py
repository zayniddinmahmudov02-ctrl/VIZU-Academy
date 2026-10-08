from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


# ============================================================
# Overview — stat cards
# ============================================================


class VizuMultilevelOverviewStats(BaseSchema):
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


class VizuMultilevelActivityPoint(BaseSchema):
    label: str
    started: int
    completed: int


class VizuMultilevelActivityStats(BaseSchema):
    days: int
    points: list[VizuMultilevelActivityPoint]
    completion_rate_percent: float | None
    average_duration_minutes: float | None


# ============================================================
# Aniqlangan darajalar + Kompetenz natijalari
# ============================================================


class VizuMultilevelLevelBucket(BaseSchema):
    level: str
    count: int
    percent: float


class VizuMultilevelCompetencyStat(BaseSchema):
    skill: str
    average_percent: float | None
    submitted_count: int
    most_common_level: str | None


class VizuMultilevelLevelAnalytics(BaseSchema):
    level_distribution: list[VizuMultilevelLevelBucket]
    total_leveled: int
    competencies: list[VizuMultilevelCompetencyStat]


# ============================================================
# Comprehensive Analytics tab
# ============================================================


class VizuMultilevelTimeAnalytics(BaseSchema):
    average_completion_minutes: float | None
    abandonment_rate_percent: float | None


class VizuMultilevelAnalytics(BaseSchema):
    overview: VizuMultilevelOverviewStats
    activity_7d: VizuMultilevelActivityStats
    activity_30d: VizuMultilevelActivityStats
    level_analytics: VizuMultilevelLevelAnalytics
    time_analytics: VizuMultilevelTimeAnalytics


# ============================================================
# Recent Tests / Results — paginated attempts list
# ============================================================


class VizuMultilevelAdminAttemptItem(BaseSchema):
    id: UUID
    attempt_number: int | None = None
    result_score: int | None = None
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
    hoeren_score: float | None
    schreiben_score: int | None
    sprechen_score: int | None


class VizuMultilevelAdminAttemptsPage(BaseSchema):
    items: list[VizuMultilevelAdminAttemptItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class VizuMultilevelStudentAttempt(BaseSchema):
    id: UUID
    attempt_number: int | None
    status: str
    started_at: datetime
    completed_at: datetime | None
    result_score: int | None
    result_level: str | None
    certificate_available: bool
    certificate_number: str | None


class VizuMultilevelStudentRow(BaseSchema):
    """Admin analytics per student — "Bestes Ergebnis" is the headline."""

    user_id: UUID
    student_name: str
    email: str
    attempts_used: int
    attempts_remaining: int
    max_attempts: int
    best_score: int | None
    best_level: str | None
    best_attempt_number: int | None
    best_attempt_id: UUID | None
    last_attempt_id: UUID | None
    last_attempt_number: int | None
    last_attempt_status: str | None
    last_attempt_score: int | None
    last_attempt_level: str | None
    last_attempt_date: datetime | None
    attempts: list[VizuMultilevelStudentAttempt]


class VizuMultilevelStudentsPage(BaseSchema):
    items: list[VizuMultilevelStudentRow]
    total: int
    page: int
    page_size: int
    total_pages: int
    sort: str
    order: str


# ============================================================
# Statistics tab
# ============================================================


class VizuMultilevelResultBucket(BaseSchema):
    # "A1".."C1" or "BELOW_A1"
    result: str
    count: int


class VizuMultilevelCompetencyAverage(BaseSchema):
    skill: str
    average_percent: float
    finished_count: int


class VizuMultilevelStatistics(BaseSchema):
    """Every number is a real aggregate; with no data everything is 0 —
    never a placeholder. Attempts that are not kept in a student's history
    (below A1, abandoned) are counted through anonymous tally rows."""

    total_attempts: int
    completed_attempts: int
    in_progress_attempts: int
    abandoned_attempts: int
    pending_review_attempts: int
    results: list[VizuMultilevelResultBucket]
    average_score_percent: float
    competency_averages: list[VizuMultilevelCompetencyAverage]
    completion_rate_percent: float
