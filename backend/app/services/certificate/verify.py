from sqlalchemy.orm import Session

from app.models.certificate import Certificate


class CertificateVerificationService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

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