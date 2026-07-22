from pydantic import BaseModel


class DashboardResponse(BaseModel):

    enrolled_courses: int

    completed_lessons: int

    completed_modules: int

    certificates: int

    study_hours: int

    progress: float

    current_course: str | None

    current_module: str | None

    current_lesson: str | None