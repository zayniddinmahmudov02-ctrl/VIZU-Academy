from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from app.api.dependencies.auth import require_admin_panel_access

from app.models.user import User

from app.services.upload import UploadService

# Folder namespaces this generic uploader is allowed to write into. Kept as
# an explicit allowlist (rather than accepting any client-supplied string)
# to prevent path traversal via `folder` (e.g. "../../etc") — matches the
# storage-path conventions already used elsewhere in the codebase:
# `videos/...` and `videos/thumbnails/...` (app/services/video/service.py)
# and `payment-proofs/...` (app/services/vizu_pay/service.py).
ALLOWED_FOLDERS = {
    "videos",
    "thumbnails",
    "payment-proofs",
}

router = APIRouter(
    prefix="/upload",
    tags=["Upload"],
)


@router.post("/{folder}")
async def upload_file(
    folder: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin_panel_access),
):

    if folder not in ALLOWED_FOLDERS:
        raise HTTPException(
            status_code=400,
            detail="Invalid upload folder",
        )

    return await UploadService().upload(
        file,
        folder,
    )
