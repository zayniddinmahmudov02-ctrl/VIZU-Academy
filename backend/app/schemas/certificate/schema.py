from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class CertificateBase(BaseSchema):

    user_id: UUID

    # Required only for source="COURSE" — validated in CertificateService.create(),
    # not here, since the requirement depends on another field's value.
    course_id: UUID | None = None

    source: str = "COURSE"

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
    """Manual/admin issuance payload.

    certificate_number and verification_code are intentionally optional —
    when omitted, CertificateService.create() auto-generates them via the
    same generate_number()/generate_verification_code() logic used by the
    automatic issuance path (CertificateService.issue()), so both routes
    share a single source of truth for these unique, non-null fields.
    """

    certificate_number: str | None = None

    verification_code: str | None = None


class CertificateUpdate(BaseSchema):

    user_id: UUID | None = None

    course_id: UUID | None = None

    source: str | None = None

    certificate_number: str | None = None

    verification_code: str | None = None

    provider: str | None = None

    level: str | None = None

    score: int | None = None

    lesen_score: int | None = None

    hoeren_score: int | None = None

    schreiben_score: int | None = None

    sprechen_score: int | None = None

    pdf_url: str | None = None

    qr_code_url: str | None = None

    is_valid: bool | None = None


class CertificateResponse(CertificateBase):

    id: UUID

    certificate_number: str

    verification_code: str

    issued_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
