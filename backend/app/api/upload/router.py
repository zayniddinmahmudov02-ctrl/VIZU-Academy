from fastapi import (
    APIRouter,
    File,
    UploadFile,
)

from app.services.upload import UploadService


router = APIRouter(
    prefix="/upload",
    tags=["Upload"],
)


@router.post("/{folder}")
async def upload_file(
    folder: str,
    file: UploadFile = File(...),
):

    return await UploadService().upload(
        file,
        folder,
    )