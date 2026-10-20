from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseSchema

# ============================================================
# Phase 5 — Enterprise Super Admin Dashboard.
#
# One response model for the single GET /admin/dashboard endpoint —
# every widget on the dashboard reads from this one payload, never its
# own request. See app/services/admin/enterprise_dashboard_service.py.
# ============================================================


class DashboardKPIs(BaseSchema):
    total_users: int
    active_users_30d: int
    premium_members: int
    total_revenue: int | None  # None = the caller's role may not see revenue
    active_courses: int
    total_model_tests: int
    certificates_issued: int
    todays_registrations: int


class DashboardChartPoint(BaseSchema):
    label: str
    value: float


class DashboardCharts(BaseSchema):
    range: str
    revenue: list[DashboardChartPoint]
    new_users: list[DashboardChartPoint]
    learning_progress: list[DashboardChartPoint]


class NamedCount(BaseSchema):
    id: str
    title: str
    count: int


class LearningAnalytics(BaseSchema):
    most_active_course: NamedCount | None
    most_viewed_lesson: NamedCount | None
    most_solved_quiz: NamedCount | None
    most_failed_quiz: NamedCount | None
    course_completion_percent: float  # completed lesson-progress rows / all lesson-progress rows
    student_completion_percent: float  # students with >= 1 completed lesson / students with any progress
    active_learners: int = 0  # students with lesson progress
    lessons_completed: int = 0


class MockTestSkillAnalytics(BaseSchema):
    model_test_id: UUID
    title: str
    attempts: int
    average_score_percent: float
    pass_rate_percent: float
    fail_rate_percent: float
    average_reading_percent: float | None
    average_listening_percent: float | None
    average_writing_percent: float | None
    average_speaking_percent: float | None


class CertificateMockAnalytics(BaseSchema):
    provider_id: UUID
    code: str
    name: str
    total_attempts: int
    average_score_percent: float
    pass_rate_percent: float
    model_tests: list[MockTestSkillAnalytics]


class PaymentsSummary(BaseSchema):
    today_revenue: int
    week_revenue: int
    month_revenue: int
    pending_payments: int
    refunds: int
    premium_sales: int


class ContentCounts(BaseSchema):
    languages: int
    levels: int
    modules: int
    lessons: int
    videos: int
    vocabulary: int
    grammar: int
    reading: int
    listening: int
    writing: int
    speaking: int
    homework: int
    quiz: int
    mock_tests: int


class AIStats(BaseSchema):
    writing_checked_today: int
    speaking_checked_today: int
    pending_ai_reviews: int
    average_ai_score: float | None


class DashboardActivityItem(BaseSchema):
    type: str
    title: str
    timestamp: datetime


class ServerHealth(BaseSchema):
    backend: bool
    postgres: bool
    postgres_latency_ms: float | None
    storage_used_percent: float | None
    disk_used_percent: float | None
    cpu_percent: float | None
    ram_percent: float | None
    uptime_seconds: int


class VizuMultilevelStats(BaseSchema):
    attempts: int
    completed: int
    final_results: int
    certificates_issued: int
    average_result: float | None
    by_level: dict[str, int]


class EnterpriseDashboardResponse(BaseSchema):
    kpis: DashboardKPIs
    charts: DashboardCharts
    learning_analytics: LearningAnalytics
    mock_test_analytics: list[CertificateMockAnalytics]
    vizu_multilevel: VizuMultilevelStats | None = None
    payments: PaymentsSummary | None  # None = role without payment access
    content: ContentCounts
    ai: AIStats
    recent_activity: list[DashboardActivityItem]
    server_health: ServerHealth | None  # None = role without system access
    can_see_finance: bool = True
    can_see_system: bool = True
