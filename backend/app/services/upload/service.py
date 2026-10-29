import re

from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.core.storage import StorageFactory

MAX_FILENAME_LENGTH = 150
_UNSAFE_CHARS = re.compile(r"[^\w.\-]+")
# nginx serves /uploads/ straight from disk on the site's own origin: an
# uploaded .html / .svg would run script as vizu-deutsch.com (stored XSS).
BLOCKED_EXTENSIONS = {
    ".html", ".htm", ".xhtml", ".shtml", ".svg", ".svgz", ".xml", ".xsl", ".js", ".mjs",
    ".swf", ".php", ".phtml", ".py", ".sh", ".cgi", ".pl", ".exe", ".bat", ".cmd",
}


def safe_filename(name: str | None) -> str:
    """The multipart filename is client input ("../../app/main.py" arrives
    verbatim): keep only the last path segment and plain characters."""
    base = re.split(r"[\\/]", name or "")[-1]
    base = _UNSAFE_CHARS.sub("_", base).lstrip(".")
    if len(base) > MAX_FILENAME_LENGTH:
        stem, dot, ext = base.rpartition(".")
        ext = ext[:20] if dot else ""
        base = (stem if dot else base)[: MAX_FILENAME_LENGTH - len(ext) - 1] + (f".{ext}" if ext else "")
    return base or "file"


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

        filename = safe_filename(file.filename)

        extension = "." + filename.rpartition(".")[2].lower() if "." in filename else ""
        if extension in BLOCKED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"File type '{extension}' is not allowed")

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