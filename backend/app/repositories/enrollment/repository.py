from sqlalchemy.orm import Session

from app.models.enrollment import Enrollment

from app.repositories.base import BaseRepository

from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentUpdate,
)


class EnrollmentRepository(BaseRepository[Enrollment]):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            Enrollment,
            db,
        )

    # =====================================
    # Create Enrollment
    # =====================================

    def create(
        self,
        data: EnrollmentCreate,
    ) -> Enrollment:

        enrollment = Enrollment(
            **data.model_dump(),
        )

        self.db.add(
            enrollment,
        )

        self.db.commit()

        self.db.refresh(
            enrollment,
        )

        return enrollment

    # =====================================
    # Update Enrollment
    # =====================================

    def update(
        self,
        enrollment: Enrollment,
        data: EnrollmentUpdate,
    ) -> Enrollment:

        for key, value in data.model_dump(
            exclude_unset=True,
        ).items():
            setattr(
                enrollment,
                key,
                value,
            )

        self.db.commit()

        self.db.refresh(
            enrollment,
        )

        return enrollment

    # =====================================
    # Delete Enrollment
    # =====================================

    def delete(
        self,
        enrollment: Enrollment,
    ) -> None:

        self.db.delete(
            enrollment,
        )

        self.db.commit()

    # =====================================
    # Get By User
    # =====================================

    def get_by_user(
        self,
        user_id: str,
    ) -> list[Enrollment]:

        return (
            self.db.query(
                Enrollment,
            )
            .filter(
                Enrollment.user_id == user_id,
            )
            .all()
        )

    # =====================================
    # Get By Course
    # =====================================

    def get_by_course(
        self,
        course_id: str,
    ) -> list[Enrollment]:

        return (
            self.db.query(
                Enrollment,
            )
            .filter(
                Enrollment.course_id == course_id,
            )
            .all()
        )

    # =====================================
    # Has Active Enrollment
    # =====================================

    def has_active_enrollment(
        self,
        user_id: str,
        course_id: str,
    ) -> bool:

        return (
            self.db.query(
                Enrollment,
            )
            .filter(
                Enrollment.user_id == user_id,
                Enrollment.course_id == course_id,
                Enrollment.is_active.is_(True),
            )
            .first()
            is not None
        )