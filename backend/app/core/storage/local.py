from pathlib import Path

from app.core.storage.base import BaseStorage


class LocalStorage(BaseStorage):

    ROOT = Path("uploads")

    CHUNK_SIZE = 1024 * 1024  # 1 MB — bounds peak RAM regardless of file size

    async def upload(
        self,
        file,
        path: str,
    ):

        destination = self.ROOT / path

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            destination,
            "wb",
        ) as buffer:

            while chunk := await file.read(self.CHUNK_SIZE):
                buffer.write(chunk)

        return str(destination)

    async def delete(
        self,
        path: str,
    ):

        target = self.ROOT / path

        if target.exists():
            target.unlink()

    def url(
        self,
        path: str,
    ):

        return f"/uploads/{path}"