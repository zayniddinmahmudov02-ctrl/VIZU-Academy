from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.schemas.course import CourseCreate


def get_courses(db: Session):
    return db.scalars(
        select(Course)
    ).all()


def create_course(
    db: Session,
    data: CourseCreate,
):
    course = Course(
        name=data.name,
        code=data.code,
        language=data.language,
        level=data.level,
        modules_count=data.modules_count,
    )

    db.add(course)
    db.commit()
    db.refresh(course)

    return course