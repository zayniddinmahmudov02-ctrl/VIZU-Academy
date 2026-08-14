from pydantic import BaseModel


class DashboardResponse(BaseModel):

    enrolled_courses: int

    completed_lessons: int

    completed_modules: int

    certificates: int

    # Was declared "study_hours" while the service actually returned
    # "study_minutes" — every call to GET /dashboard/{user_id} failed
    # response validation (500) as a result. Renamed to match reality
    # rather than converting the unit, since StudentProgress.study_minutes
    # is what's actually tracked.
    study_minutes: int

    progress: float

    current_course: str | None

    current_module: str | None

    current_lesson: str | None

    # Lets the frontend build a real "Continue Learning" link and fetch
    # this lesson's live score (GET /lessons/{id}/score) instead of
    # only having a display-only title string.
    current_lesson_id: str | None = None
    current_lesson_score: int | None = None
    current_lesson_max_score: int | None = None