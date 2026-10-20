"""The student's own certificates (student panel "Zertifikate").
Only ever the caller's own rows / attempts — another student's id is a 404."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.certificate import registry
from app.services.certificate.pdf_access import certificate_pdf

router = APIRouter(prefix="/my-certificates", tags=["Certificates - Student"])


@router.get("")
def my_certificates(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return registry.for_student(db, current_user)


@router.get("/{item_id}/pdf")
def my_certificate_pdf(item_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return certificate_pdf(db, item_id, owner=current_user)
