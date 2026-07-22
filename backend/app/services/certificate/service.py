from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.certificate import Certificate

from app.repositories.certificate import (
    CertificateRepository,
)

from app.schemas.certificate import (
    CertificateCreate,
    CertificateUpdate,
)


class CertificateService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.repository = CertificateRepository(db)

    # ==========================
    # CRUD
    # ==========================

    def get_all(self):
        return self.repository.get_all()

    def get(
        self,
        item_id: str,
    ):
        return self.repository.get(item_id)

    def create(
        self,
        data: CertificateCreate,
    ):
        return self.repository.create(data)

    def update(
        self,
        item_id: str,
        data: CertificateUpdate,
    ):
        item = self.repository.get(item_id)

        if not item:
            return None

        return self.repository.update(
            item,
            data,
        )

    def delete(
        self,
        item_id: str,
    ):
        item = self.repository.get(item_id)

        if not item:
            return False

        self.repository.delete(item)

        return True

    # ==========================
    # Certificate Engine
    # ==========================

    def generate_number(
        self,
    ):

        year = datetime.utcnow().year

        serial = uuid4().hex[:8].upper()

        return f"VIZU-{year}-{serial}"

    def generate_verification_code(
        self,
    ):

        return uuid4().hex.upper()

    def issue(
        self,
        *,
        user_id: str,
        course_id: str,
        level: str,
        lesen_score: int,
        hoeren_score: int,
        schreiben_score: int,
        sprechen_score: int,
        provider: str = "VIZU",
    ):

        total_score = (
            lesen_score
            + hoeren_score
            + schreiben_score
            + sprechen_score
        )

        certificate = Certificate(

            user_id=user_id,

            course_id=course_id,

            provider=provider,

            level=level,

            lesen_score=lesen_score,

            hoeren_score=hoeren_score,

            schreiben_score=schreiben_score,

            sprechen_score=sprechen_score,

            score=total_score,

            certificate_number=self.generate_number(),

            verification_code=self.generate_verification_code(),

            issued_at=datetime.utcnow(),

            is_valid=True,
        )

        self.db.add(certificate)

        self.db.commit()

        self.db.refresh(certificate)

        return certificate

    def verify(
        self,
        verification_code: str,
    ):

        return (
            self.db.query(Certificate)
            .filter(
                Certificate.verification_code
                == verification_code,
                Certificate.is_valid.is_(True),
            )
            .first()
        )

    def history(
        self,
        user_id: str,
    ):

        return (
            self.db.query(Certificate)
            .filter(
                Certificate.user_id == user_id,
            )
            .order_by(
                Certificate.issued_at.desc(),
            )
            .all()
        )

    def invalidate(
        self,
        certificate_id: str,
    ):

        certificate = self.get(certificate_id)

        if not certificate:
            return None

        certificate.is_valid = False

        self.db.commit()

        self.db.refresh(certificate)

        return certificate