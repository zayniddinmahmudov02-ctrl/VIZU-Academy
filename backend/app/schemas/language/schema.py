from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseSchema


class LanguageResponse(BaseSchema):
    id: UUID
    code: str
    locale: str
    name: str
    native_name: str | None = None
    english_name: str | None = None
    flag_file: str | None = None
    primary_color: str | None = None
    description: str | None = None
    is_default: bool
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    # Denormalized counts for the admin Languages table — computed once in
    # get_languages()/get_language() rather than making the frontend fire a
    # separate request per row.
    learners_count: int = 0
    levels_count: int = 0
    modules_count: int = 0
    lessons_count: int = 0


class LanguageCreate(BaseSchema):
    code: str
    locale: str
    name: str
    native_name: str | None = None
    english_name: str | None = None
    flag_file: str | None = None
    primary_color: str | None = None
    description: str | None = None
    is_default: bool = False
    is_active: bool = True
    sort_order: int = 1


class LanguageUpdate(BaseSchema):
    code: str | None = None
    locale: str | None = None
    name: str | None = None
    native_name: str | None = None
    english_name: str | None = None
    flag_file: str | None = None
    primary_color: str | None = None
    description: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class LanguageStatistics(BaseSchema):
    language_id: UUID
    learners: int
    active_learners: int
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
    certificates: int


class LanguageLearnerItem(BaseSchema):
    id: UUID
    username: str
    email: str
    is_primary: bool
    joined_at: datetime
    last_activity: datetime | None = None


class LanguageLearnersResponse(BaseSchema):
    items: list[LanguageLearnerItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class LanguageSettingsResponse(BaseSchema):
    language_id: UUID
    certificates_enabled: bool
    leaderboard_enabled: bool
    vocabulary_enabled: bool
    grammar_enabled: bool
    reading_enabled: bool
    listening_enabled: bool
    writing_enabled: bool
    speaking_enabled: bool
    homework_enabled: bool
    quiz_enabled: bool
    ai_writing_enabled: bool
    ai_speaking_enabled: bool
    mock_exams_enabled: bool
    video_lessons_enabled: bool
    media_library_enabled: bool


class LanguageSettingsUpdate(BaseSchema):
    certificates_enabled: bool | None = None
    leaderboard_enabled: bool | None = None
    vocabulary_enabled: bool | None = None
    grammar_enabled: bool | None = None
    reading_enabled: bool | None = None
    listening_enabled: bool | None = None
    writing_enabled: bool | None = None
    speaking_enabled: bool | None = None
    homework_enabled: bool | None = None
    quiz_enabled: bool | None = None
    ai_writing_enabled: bool | None = None
    ai_speaking_enabled: bool | None = None
    mock_exams_enabled: bool | None = None
    video_lessons_enabled: bool | None = None
    media_library_enabled: bool | None = None
