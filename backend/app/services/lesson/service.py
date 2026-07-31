from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lesson import Lesson
from app.models.listening import Listening
from app.models.student_progress import StudentProgress

from app.repositories.lesson import LessonRepository
from app.schemas.lesson import LessonCreate, LessonUpdate


class LessonService:
    """Admin CRUD for lessons — separate from the plain-function reads
    above (`get_all_lessons`/`get_lesson_detail`), which serve the
    student-facing shape (`LessonListItem`/`LessonDetail`, progress-aware)
    that this class has no reason to duplicate."""

    def __init__(self, db: Session):
        self.repository = LessonRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(self, lesson_id: str):
        return self.repository.get(lesson_id)

    def get_by_module(self, module_id: str):
        return self.repository.get_by_module(module_id)

    def create(self, data: LessonCreate):
        return self.repository.create(data)

    def update(self, lesson_id: str, data: LessonUpdate):
        lesson = self.repository.get(lesson_id)

        if not lesson:
            return None

        return self.repository.update(lesson, data)

    def delete(self, lesson_id: str):
        lesson = self.repository.get(lesson_id)

        if not lesson:
            return False

        self.repository.delete(lesson)

        return True


def _progress_percent(progress: StudentProgress | None) -> int:
    return 100 if (progress is not None and progress.lesson_completed) else 0


def get_lessons_for_module(db: Session, module_id: str):
    return db.scalars(
        select(Lesson)
        .where(Lesson.module_id == module_id)
        .order_by(Lesson.number)
    ).all()


def get_all_lessons(db: Session, user_id: str) -> list[dict]:
    lessons = db.scalars(
        select(Lesson).order_by(Lesson.number)
    ).all()

    progress_by_lesson = {
        row.lesson_id: row
        for row in db.scalars(
            select(StudentProgress).where(StudentProgress.user_id == user_id)
        ).all()
    }

    return [
        {
            "id": str(lesson.id),
            "module_id": str(lesson.module_id),
            "number": lesson.number,
            "title": lesson.title,
            "duration": lesson.duration,
            "video_url": lesson.video_url,
            "is_free": lesson.is_free,
            "progress": _progress_percent(progress_by_lesson.get(lesson.id)),
        }
        for lesson in lessons
    ]


def get_lesson_detail(db: Session, lesson_id: str, user_id: str) -> dict | None:
    lesson = db.get(Lesson, UUID(lesson_id))

    if lesson is None:
        return None

    listening = db.scalars(
        select(Listening)
        .where(
            Listening.lesson_id == lesson.id,
            Listening.is_published.is_(True),
        )
        .order_by(Listening.order_index)
        .limit(1)
    ).first()

    progress = db.scalars(
        select(StudentProgress).where(
            StudentProgress.user_id == user_id,
            StudentProgress.lesson_id == lesson.id,
        )
    ).first()

    return {
        "id": str(lesson.id),
        "module_id": str(lesson.module_id),
        "number": lesson.number,
        "title": lesson.title,
        "duration": lesson.duration,
        "video_url": lesson.video_url,
        "audio_url": listening.audio_url if listening else None,
        "is_free": lesson.is_free,
        "progress": _progress_percent(progress),
    }
