from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.api.upload.router import ALLOWED_FOLDERS
from app.db.session import get_db
from app.models.user import User
from app.schemas.media_asset import MediaAssetResponse
from app.services.media_asset import MediaAssetService

router = APIRouter(
    prefix="/media-library",
    tags=["Media Library"],
)


@router.get(
    "/",
    response_model=list[MediaAssetResponse],
)
def list_assets(
    folder: str | None = Query(default=None),
    media_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return MediaAssetService(db).list(folder=folder, media_type=media_type)


@router.post(
    "/upload",
    response_model=MediaAssetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_asset(
    folder: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    if folder not in ALLOWED_FOLDERS:
        raise HTTPException(
            status_code=400,
            detail="Invalid upload folder",
        )

    return await MediaAssetService(db).upload(
        file,
        folder,
        uploaded_by=current_user.id,
    )


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    deleted = MediaAssetService(db).delete(asset_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media asset not found.",
        )
