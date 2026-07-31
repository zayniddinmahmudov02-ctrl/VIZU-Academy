from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db
from app.models.course import Course
from app.models.user import User
from app.schemas.course import (
    CourseCreate,
    CourseResponse,
    CourseUpdate,
)
from app.services.course import (
    create_course,
    get_courses,
    update_course,
)

router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


@router.get(
    "/",
    response_model=list[CourseResponse],
)
def list_courses(
    db: Session = Depends(get_db),
):
    return get_courses(db)


@router.get(
    "/{course_id}",
    response_model=CourseResponse,
)
def get_course(
    course_id: UUID,
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    return course


@router.post(
    "/",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course_endpoint(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return create_course(
        db,
        payload,
    )


@router.put(
    "/{course_id}",
    response_model=CourseResponse,
)
def update_course_endpoint(
    course_id: UUID,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    course = update_course(
        db,
        course_id,
        payload,
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    return course


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_course(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    course = db.get(Course, course_id)

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    db.delete(course)
    db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )