from sqlalchemy.orm import Session

from app.models.certificate import Certificate

from app.repositories.base import BaseRepository

from app.schemas.certificate import (
    CertificateCreate,
    CertificateUpdate,
)


class CertificateRepository(BaseRepository[Certificate]):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            Certificate,
            db,
        )

    # =====================================
    # Create Certificate
    # =====================================

    def create(
        self,
        data: CertificateCreate,
    ) -> Certificate:

        certificate = Certificate(
            **data.model_dump(),
        )

        self.db.add(
            certificate,
        )

        self.db.commit()

        self.db.refresh(
            certificate,
        )

        return certificate

    # =====================================
    # Update Certificate
    # =====================================

    def update(
        self,
        certificate: Certificate,
        data: CertificateUpdate,
    ) -> Certificate:

        for key, value in data.model_dump(
            exclude_unset=True,
        ).items():
            setattr(
                certificate,
                key,
                value,
            )

        self.db.commit()

        self.db.refresh(
            certificate,
        )

        return certificate

    # =====================================
    # Delete Certificate
    # =====================================

    def delete(
        self,
        certificate: Certificate,
    ) -> None:

        self.db.delete(
            certificate,
        )

        self.db.commit()

    # =====================================
    # Verify Certificate
    # =====================================

    def get_by_verification_code(
        self,
        verification_code: str,
    ) -> Certificate | None:

        return (
            self.db.query(
                Certificate,
            )
            .filter(
                Certificate.verification_code
                == verification_code,
            )
            .first()
        )

    # =====================================
    # User Certificates
    # =====================================

    def get_by_user(
        self,
        user_id: str,
    ) -> list[Certificate]:

        return (
            self.db.query(
                Certificate,
            )
            .filter(
                Certificate.user_id == user_id,
            )
            .all()
        )

    # =====================================
    # Course Certificates
    # =====================================

    def get_by_course(
        self,
        course_id: str,
    ) -> list[Certificate]:

        return (
            self.db.query(
                Certificate,
            )
            .filter(
                Certificate.course_id == course_id,
            )
            .all()
        )