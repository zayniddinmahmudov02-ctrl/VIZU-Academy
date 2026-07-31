from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate


def get_courses(db: Session):
    return db.scalars(
        select(Course)
    ).all()


def create_course(
    db: Session,
    data: CourseCreate,
):
    course = Course(**data.model_dump())

    db.add(course)
    db.commit()
    db.refresh(course)

    return course


def update_course(
    db: Session,
    course_id: UUID,
    data: CourseUpdate,
):
    course = db.get(Course, course_id)

    if course is None:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(course, key, value)

    db.commit()
    db.refresh(course)

    return course