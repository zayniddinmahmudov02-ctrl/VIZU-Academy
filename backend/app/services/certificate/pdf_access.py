"""PDF of one registry item ("c:<certificate id>" or "ml:<attempt id>").
`owner` set = student access (only their own); None = admin access."""

from uuid import UUID

from fastapi import HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.models.certificate import Certificate
from app.models.user import User
from app.models.vizu_multilevel_attempt import VizuMultilevelAttempt
from app.services.certificate.registry import course_pdf_path


def _parse(item_id: str) -> tuple[str, UUID]:
    kind, _, raw = item_id.partition(":")
    try:
        return kind, UUID(raw)
    except ValueError:
        raise HTTPException(status_code=404, detail="Certificate not found") from None


def certificate_pdf(db: Session, item_id: str, owner: User | None) -> Response:
    kind, uid = _parse(item_id)
    if kind == "c":
        cert = db.get(Certificate, uid)
        if cert is None or (owner is not None and str(cert.user_id) != str(owner.id)):
            raise HTTPException(status_code=404, detail="Certificate not found")
        path = course_pdf_path(cert)
        if path is None:
            raise HTTPException(status_code=404, detail="CERTIFICATE_PDF_NOT_AVAILABLE")
        return FileResponse(path, media_type="application/pdf", filename=f"{cert.certificate_number}.pdf",
                            headers={"Cache-Control": "private, no-store"})
    if kind == "ml":
        from app.services.vizu_multilevel import certificate_pdf as ml_pdf
        from app.services.vizu_multilevel import certificate_service

        attempt = db.get(VizuMultilevelAttempt, uid)
        if attempt is None or (owner is not None and str(attempt.user_id) != str(owner.id)):
            raise HTTPException(status_code=404, detail="Certificate not found")
        holder = owner or db.get(User, attempt.user_id)
        try:
            data = certificate_service.build_certificate(db, attempt, holder)  # issues the number on first use, like the student view
        except certificate_service.CertificateUnavailable as exc:
            raise HTTPException(status_code=404, detail=f"NO_CERTIFICATE_{exc.reason}") from None
        return ml_pdf.certificate_pdf_response(data)
    raise HTTPException(status_code=404, detail="Certificate not found")
