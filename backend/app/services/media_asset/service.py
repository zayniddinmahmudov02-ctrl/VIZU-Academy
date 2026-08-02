from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.media_asset import MediaAsset
from app.services.upload import UploadService

FOLDER_MEDIA_TYPE = {
    "videos": "video",
    "audio": "audio",
    "images": "image",
    "thumbnails": "image",
    "documents": "document",
}


def _infer_media_type(folder: str, content_type: str | None) -> str:
    if folder in FOLDER_MEDIA_TYPE:
        return FOLDER_MEDIA_TYPE[folder]

    if content_type:
        if content_type.startswith("video/"):
            return "video"
        if content_type.startswith("audio/"):
            return "audio"
        if content_type.startswith("image/"):
            return "image"

    return "document"


class MediaAssetService:

    def __init__(self, db: Session):
        self.db = db
        self.upload_service = UploadService()

    def list(
        self,
        folder: str | None = None,
        media_type: str | None = None,
    ):
        query = select(MediaAsset).order_by(MediaAsset.created_at.desc())

        if folder:
            query = query.where(MediaAsset.folder == folder)

        if media_type:
            query = query.where(MediaAsset.media_type == media_type)

        return self.db.scalars(query).all()

    async def upload(
        self,
        file: UploadFile,
        folder: str,
        uploaded_by: UUID | None,
    ) -> MediaAsset:
        original_name = file.filename or "file"
        # Dedupe: the underlying UploadService writes to `{folder}/{filename}`
        # with no collision handling, so two uploads of "photo.jpg" would
        # silently overwrite each other without this prefix.
        file.filename = f"{uuid4().hex}_{original_name}"

        result = await self.upload_service.upload(file, folder)

        asset = MediaAsset(
            filename=original_name,
            url=result["url"],
            folder=folder,
            media_type=_infer_media_type(folder, file.content_type),
            content_type=file.content_type,
            size_bytes=getattr(file, "size", None),
            uploaded_by=uploaded_by,
        )

        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)

        return asset

    def delete(self, asset_id: UUID) -> bool:
        asset = self.db.get(MediaAsset, asset_id)

        if asset is None:
            return False

        self.db.delete(asset)
        self.db.commit()

        return True
