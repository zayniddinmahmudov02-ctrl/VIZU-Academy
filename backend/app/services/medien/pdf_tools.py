"""PDF helpers of the Bibliothek: page count and the PREVIEW file of a paid book.

A student who has not bought a paid book gets a separate PDF that contains only its first N pages (N = `preview_pages_count`, default 10),
built here on the server with pypdf — the original file is never streamed to them, and a request for page 11+ has nothing to return.
The preview copies the page objects (content, fonts, images that those pages use) into a new document; annotations / links are dropped
(a link could point at a later page) and no document metadata, outline, attachment or form is carried over.
Previews are cached under `previews/<book id>-<file stem>-<N>.pdf`: replacing the PDF or changing N gives a new name, old ones are removed."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PyPdfError

log = logging.getLogger("vizu.medien.pdf")

MAX_PREVIEW_PAGES = 500


class PdfUnreadable(Exception):
    """The file is not a readable (or is a password protected) PDF."""


def _open(path: Path) -> PdfReader:
    try:
        reader = PdfReader(str(path), strict=False)
        if reader.is_encrypted and not reader.decrypt(""):
            raise PdfUnreadable("encrypted")
        len(reader.pages)  # forces the page tree to load
        return reader
    except PdfUnreadable:
        raise
    except (PyPdfError, OSError, ValueError, KeyError, RecursionError, AttributeError, TypeError, IndexError) as exc:
        raise PdfUnreadable(type(exc).__name__) from exc


def page_count(path: Path) -> int | None:
    """Number of pages, or None when the file cannot be read (the upload is still kept; the preview is then unavailable)."""
    try:
        return len(_open(path).pages)
    except PdfUnreadable as exc:
        log.warning("pdf page count unavailable: %s", exc)
        return None


def build_preview(src: Path, pages: int, dest: Path) -> int:
    """Writes the first `pages` pages of `src` to `dest` (atomic) and returns how many were written."""
    reader = _open(src)
    n = max(1, min(int(pages), len(reader.pages), MAX_PREVIEW_PAGES))
    writer = PdfWriter()
    for i in range(n):
        page = reader.pages[i]
        if "/Annots" in page:
            del page["/Annots"]  # links may reference later pages
        writer.add_page(page)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(dest.parent), suffix=".part")
    try:
        with os.fdopen(fd, "wb") as handle:
            writer.write(handle)
        os.replace(tmp, dest)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    log.info("pdf preview built: %s pages", n)
    return n
