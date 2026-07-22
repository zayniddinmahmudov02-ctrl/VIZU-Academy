from sqlalchemy.orm import Session

from app.models.lesson import Lesson

from app.models.student_progress import StudentProgress


class LessonUnlockService:

    def __init__(self, db: Session):
        self.db = db

    def unlocked_lessons(
        self,
        user_id: str,
        module_id: str,
    ):

        lessons = (
            self.db.query(Lesson)
            .filter(
                Lesson.module_id == module_id
            )
            .order_by(Lesson.number)
            .all()
        )

        unlocked = []

        for index, lesson in enumerate(lessons):

            if index == 0:
                unlocked.append(lesson.id)
                continue

            previous = lessons[index - 1]

            progress = (
                self.db.query(StudentProgress)
                .filter(
                    StudentProgress.user_id == user_id,
                    StudentProgress.lesson_id == previous.id,
                    StudentProgress.lesson_completed == True,
                )
                .first()
            )

            if progress:
                unlocked.append(lesson.id)

        return unlocked