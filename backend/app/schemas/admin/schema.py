from datetime import datetime

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class AdminDashboardResponse(BaseSchema):
    """Legacy summary shape — kept for backward compatibility."""

    users: int

    teachers: int

    students: int

    languages: int

    courses: int

    modules: int

    lessons: int

    enrollments: int

    certificates: int

    payments: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class DashboardStats(BaseSchema):

    total_users: int

    premium_users: int

    trial_users: int

    revenue_today: int

    revenue_month: int

    revenue_year: int

    certificates: int

    courses: int

    lessons: int


class ChartPoint(BaseSchema):

    label: str

    value: int


class PopularCourse(BaseSchema):

    id: str

    title: str

    level: str

    enrollments: int


class ActiveUser(BaseSchema):

    id: str

    username: str

    email: str

    last_login: datetime | None


class RecentRegistration(BaseSchema):

    id: str

    username: str

    email: str

    role: str

    created_at: datetime


class RecentPayment(BaseSchema):

    id: str

    user_email: str

    course_title: str

    amount: int

    currency: str

    status: str

    created_at: datetime


class RecentCertificate(BaseSchema):

    id: str

    user_email: str

    course_title: str

    level: str

    issued_at: datetime


class ActivityItem(BaseSchema):

    type: str

    title: str

    timestamp: datetime


class AdminDashboardOverview(BaseSchema):

    server_status: str

    stats: DashboardStats

    revenue_chart: list[ChartPoint]

    user_growth_chart: list[ChartPoint]

    popular_courses: list[PopularCourse]

    active_users: list[ActiveUser]

    recent_registrations: list[RecentRegistration]

    recent_payments: list[RecentPayment]

    recent_certificates: list[RecentCertificate]

    recent_activities: list[ActivityItem]
