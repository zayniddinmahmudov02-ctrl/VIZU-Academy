from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.student_writing import StudentWriting
from app.models.user import User
from app.models.writing import Writing

from app.schemas.student_writing import (
    StudentWritingCreate,
    StudentWritingUpdate,
)


class StudentWritingRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(StudentWriting).all()

    def get(self, item_id: str):
        return (
            self.db.query(StudentWriting)
            .filter(StudentWriting.id == item_id)
            .first()
        )

    def get_by_user_and_writing(self, user_id, writing_id):
        return (
            self.db.query(StudentWriting)
            .filter(StudentWriting.user_id == str(user_id), StudentWriting.writing_id == str(writing_id))
            .first()
        )

    def _base_teacher_query(self, course_ids: list[str]):
        return (
            self.db.query(StudentWriting, Writing, Lesson, Module, Course, User)
            .join(Writing, Writing.id == StudentWriting.writing_id)
            .join(Lesson, Lesson.id == Writing.lesson_id)
            .join(Module, Module.id == Lesson.module_id)
            .join(Course, Course.id == Module.course_id)
            .join(User, User.id == StudentWriting.user_id)
            .filter(Module.course_id.in_(course_ids))
            .filter(StudentWriting.status != "DRAFT")
        )

    def list_for_teacher(
        self,
        course_ids: list[str],
        status: str | None = None,
        course_id: str | None = None,
        level: str | None = None,
        lesson_id: str | None = None,
        search: str | None = None,
    ):
        if not course_ids:
            return []

        query = self._base_teacher_query(course_ids)

        if status is not None:
            query = query.filter(StudentWriting.status == status)
        if course_id is not None:
            query = query.filter(Course.id == course_id)
        if level is not None:
            query = query.filter(Course.level == level)
        if lesson_id is not None:
            query = query.filter(Lesson.id == lesson_id)
        if search:
            like = f"%{search.lower()}%"
            query = query.filter(
                (User.email.ilike(like))
                | (User.username.ilike(like))
                | (User.first_name.ilike(like))
                | (User.last_name.ilike(like))
            )

        return query.order_by(StudentWriting.submitted_at.desc()).all()

    def get_for_teacher(self, course_ids: list[str], submission_id):
        if not course_ids:
            return None
        return self._base_teacher_query(course_ids).filter(StudentWriting.id == str(submission_id)).first()

    def create(
        self,
        data: StudentWritingCreate,
    ):
        item = StudentWriting(**data.model_dump())

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def update(
        self,
        item: StudentWriting,
        data: StudentWritingUpdate,
    ):
        for key, value in data.model_dump(
            exclude_unset=True
        ).items():
            setattr(item, key, value)

        self.db.commit()
        self.db.refresh(item)

        return item

    def delete(
        self,
        item: StudentWriting,
    ):
        self.db.delete(item)
        self.db.commit()