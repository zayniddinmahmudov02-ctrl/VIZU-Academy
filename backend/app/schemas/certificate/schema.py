from datetime import datetime

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class CertificateBase(BaseSchema):

    user_id: str

    course_id: str

    certificate_number: str

    verification_code: str

    provider: str = "VIZU"

    level: str

    score: int = 0

    lesen_score: int = 0

    hoeren_score: int = 0

    schreiben_score: int = 0

    sprechen_score: int = 0

    pdf_url: str | None = None

    qr_code_url: str | None = None

    is_valid: bool = True


class CertificateCreate(CertificateBase):
    pass


class CertificateUpdate(BaseSchema):

    score: int | None = None

    lesen_score: int | None = None

    hoeren_score: int | None = None

    schreiben_score: int | None = None

    sprechen_score: int | None = None

    pdf_url: str | None = None

    qr_code_url: str | None = None

    is_valid: bool | None = None


class CertificateResponse(CertificateBase):

    id: str

    issued_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )