from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin

from app.db.session import get_db

from app.models.user import User

from app.schemas.certificate import (
    CertificateCreate,
    CertificateResponse,
    CertificateUpdate,
)

from app.services.certificate import (
    CertificatePDFService,
    CertificateQRService,
    CertificateService,
    CertificateVerificationService,
)

router = APIRouter(
    prefix="/certificates",
    tags=["Certificates"],
)


# ==================================================
# GET ALL CERTIFICATES
# ==================================================

@router.get("")
def get_certificates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    service = CertificateService(db)

    return service.get_all()


# ==================================================
# GET CERTIFICATE
# ==================================================

@router.get("/{certificate_id}")
def get_certificate(
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    service = CertificateService(db)

    certificate = service.get(
        certificate_id,
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    return certificate


# ==================================================
# CREATE CERTIFICATE (manual issuance / correction)
# ==================================================

@router.post(
    "",
    response_model=CertificateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_certificate(
    data: CertificateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    service = CertificateService(db)

    return service.create(data)


# ==================================================
# UPDATE CERTIFICATE (correct metadata)
# ==================================================

@router.put(
    "/{certificate_id}",
    response_model=CertificateResponse,
)
def update_certificate(
    certificate_id: str,
    data: CertificateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    service = CertificateService(db)

    certificate = service.update(
        certificate_id,
        data,
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    return certificate


# ==================================================
# DELETE CERTIFICATE (revoke)
# ==================================================

@router.delete(
    "/{certificate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_certificate(
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    service = CertificateService(db)

    deleted = service.delete(
        certificate_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==================================================
# VERIFY CERTIFICATE
# ==================================================

@router.get("/verify/{verification_code}")
def verify_certificate(
    verification_code: str,
    db: Session = Depends(get_db),
):
    service = CertificateVerificationService(
        db,
    )

    certificate = service.verify(
        verification_code,
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    return certificate


# ==================================================
# GENERATE PDF
# ==================================================

@router.post("/{certificate_id}/pdf")
def generate_pdf(
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    service = CertificateService(db)

    certificate = service.get(
        certificate_id,
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    pdf_service = CertificatePDFService()

    path = pdf_service.generate(
        certificate,
    )

    certificate.pdf_url = path

    db.commit()

    db.refresh(
        certificate,
    )

    return {
        "message": "PDF generated successfully",
        "pdf_url": path,
    }


# ==================================================
# GENERATE QR
# ==================================================

@router.post("/{certificate_id}/qr")
def generate_qr(
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    service = CertificateService(db)

    certificate = service.get(
        certificate_id,
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    qr_service = CertificateQRService()

    path = qr_service.generate(
        certificate,
    )

    certificate.qr_code_url = path

    db.commit()

    db.refresh(
        certificate,
    )

    return {
        "message": "QR generated successfully",
        "qr_url": path,
    }


# ==================================================
# DOWNLOAD CERTIFICATE
# ==================================================

@router.get("/download/{certificate_id}")
def download_certificate(
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    service = CertificateService(db)

    certificate = service.get(
        certificate_id,
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    if not certificate.pdf_url:
        raise HTTPException(
            status_code=404,
            detail="Certificate PDF not found",
        )

    return FileResponse(
        path=certificate.pdf_url,
        media_type="application/pdf",
        filename=f"{certificate.certificate_number}.pdf",
    )