from fastapi import UploadFile

from app.core.config import settings
from app.core.storage import StorageFactory


class UploadService:

    def __init__(self):

        self.storage = StorageFactory.create(
            settings.STORAGE_PROVIDER,
        )

    async def upload(
        self,
        file: UploadFile,
        folder: str,
    ):

        filename = file.filename

        path = f"{folder}/{filename}"

        await self.storage.upload(
            file,
            path,
        )

        return {
            "filename": filename,
            "path": path,
            "url": self.storage.url(path),
        }

    async def delete(
        self,
        path: str,
    ):

        await self.storage.delete(path)