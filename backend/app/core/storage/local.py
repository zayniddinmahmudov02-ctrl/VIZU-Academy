import asyncio
from pathlib import Path

from app.core.storage.base import BaseStorage


class LocalStorage(BaseStorage):

    ROOT = Path("uploads")

    CHUNK_SIZE = 1024 * 1024  # 1 MB — bounds peak RAM regardless of file size

    async def upload(
        self,
        file,
        path: str,
        max_bytes: int | None = None,
    ):

        destination = self.ROOT / path

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # buffer.write() is a blocking disk-I/O call; run on a worker
        # thread instead of the event loop it's called from. Uncorked,
        # every chunk of a large upload would stall this single-process
        # server's event loop for the write's duration — freezing every
        # other request (API calls, other students' pages) until the
        # upload finishes, since nothing else can run in between.
        written = 0

        try:
            with open(
                destination,
                "wb",
            ) as buffer:

                while chunk := await file.read(self.CHUNK_SIZE):
                    written += len(chunk)

                    if max_bytes is not None and written > max_bytes:
                        raise ValueError(
                            f"Upload exceeds the {max_bytes}-byte limit"
                        )

                    await asyncio.to_thread(buffer.write, chunk)
        except ValueError:
            destination.unlink(missing_ok=True)
            raise

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