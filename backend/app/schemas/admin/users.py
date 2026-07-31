from datetime import datetime

from pydantic import ConfigDict, field_validator

from app.core.security.roles import UserRole
from app.schemas.base import BaseSchema


class UserTagItem(BaseSchema):
    id: str
    label: str


class UserListItem(BaseSchema):
    id: str
    email: str
    username: str
    role: str
    is_active: bool
    is_verified: bool
    is_banned: bool
    is_suspended: bool
    is_premium: bool
    premium_until: datetime | None
    last_login: datetime | None
    created_at: datetime
    tags: list[UserTagItem]


class UserListResponse(BaseSchema):
    items: list[UserListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserDetail(BaseSchema):
    id: str
    email: str
    username: str
    role: str
    is_active: bool
    is_verified: bool
    is_banned: bool
    ban_reason: str | None
    banned_at: datetime | None
    is_suspended: bool
    suspended_until: datetime | None
    suspend_reason: str | None
    is_premium: bool
    premium_until: datetime | None
    last_login: datetime | None
    created_at: datetime
    tags: list[UserTagItem]
    enrollments_count: int
    certificates_count: int
    payments_total: int


class UserProgressLesson(BaseSchema):
    lesson_id: str
    lesson_title: str
    course_title: str
    total_score: int
    lesson_completed: bool
    video_completed: bool
    grammar_completed: bool
    reading_completed: bool
    listening_completed: bool
    writing_completed: bool
    speaking_completed: bool
    quiz_completed: bool


class UserProgressResponse(BaseSchema):
    total_lessons_started: int
    total_lessons_completed: int
    total_experience: int
    total_study_minutes: int
    longest_streak_days: int
    lessons: list[UserProgressLesson]


class LoginHistoryItem(BaseSchema):
    id: str
    ip_address: str | None
    device: str
    os: str
    browser: str
    success: bool
    created_at: datetime


class LoginHistoryResponse(BaseSchema):
    items: list[LoginHistoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class DeviceHistoryItem(BaseSchema):
    device: str
    os: str
    browser: str
    ip_address: str | None
    first_seen: datetime
    last_seen: datetime
    login_count: int


class ActivityTimelineItem(BaseSchema):
    type: str
    title: str
    timestamp: datetime


class PaymentHistoryItem(BaseSchema):
    id: str
    course_title: str
    amount: int
    currency: str
    provider: str
    status: str
    transaction_id: str | None
    created_at: datetime


class SubscriptionInfo(BaseSchema):
    is_premium: bool
    premium_until: datetime | None
    is_trial: bool
    total_paid: int
    payments_count: int


class GrantPremiumRequest(BaseSchema):
    days: int


class ExtendSubscriptionRequest(BaseSchema):
    days: int


class RoleUpdateRequest(BaseSchema):
    role: str

    @field_validator("role")
    @classmethod
    def role_must_be_known(cls, value: str) -> str:
        if value not in UserRole.ALL_ROLES:
            raise ValueError(
                f"Unknown role '{value}'. Must be one of: "
                f"{', '.join(sorted(UserRole.ALL_ROLES))}"
            )
        return value


class BanRequest(BaseSchema):
    reason: str


class SuspendRequest(BaseSchema):
    days: int
    reason: str


class TagRequest(BaseSchema):
    label: str


class ResetPasswordResponse(BaseSchema):
    temporary_password: str


class ImpersonateResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    user: UserListItem

    model_config = ConfigDict(from_attributes=False)


class AuditLogItem(BaseSchema):
    id: str
    actor_email: str | None
    action: str
    details: str | None
    ip_address: str | None
    created_at: datetime


class AuditLogResponse(BaseSchema):
    items: list[AuditLogItem]
    total: int
    page: int
    page_size: int
    total_pages: int
