"""Regression tests for the "POST/GET /api/v1/admin/books -> 422"
production incident.

Root cause (traced through the actual code, not guessed):
BaseSchema (app/schemas/base.py) sets `extra="forbid"` globally, so
Pydantic rejects the ENTIRE request with 422 if the body contains any
field the schema doesn't declare. The Book model (app/models/book.py)
and BookResponse both already have `cover_url`, but BookBase/
BookCreate/BookUpdate never did - meanwhile the admin form
(book-manager.tsx) always includes `cover_url` in its submitted
payload (empty string on create, the FileUploadField's media_library
URL once a cover is chosen), so every single create/update request
422'd, regardless of title/level/other fields being perfectly valid.

Not the same class of bug as the earlier UUID/str lesson_id mismatch
(that was a Python-side set-membership bug) - this is a pure schema/
payload contract gap. No DB schema change needed - the `cover_url`
column already existed; only the Pydantic schema was missing it.

Also verifies: `require_admin_panel_access` (401 vs 403 boundary),
`upload_pdf`'s content-type validation, and that this fix didn't
loosen `extra="forbid"` for genuinely unknown fields - a typo'd field
name must still 422, only `cover_url` specifically was ever the gap.
"""

import asyncio
import unittest
from unittest.mock import MagicMock

from fastapi import HTTPException
from pydantic import ValidationError

from app.api.dependencies.auth import require_admin_panel_access
from app.schemas.book import BookCreate, BookUpdate
from app.services.book.service import BookService


class TestBookCreateAcceptsCoverUrl(unittest.TestCase):
    """The exact field the admin form always sends and the pre-fix
    schema always rejected."""

    def test_create_with_cover_url_is_valid(self):
        payload = BookCreate(
            title="Der Weg",
            level="A1",
            cover_url="https://vizu-deutsch.com/uploads/images/cover.jpg",
        )
        self.assertEqual(payload.cover_url, "https://vizu-deutsch.com/uploads/images/cover.jpg")

    def test_create_with_empty_string_cover_url_is_valid(self):
        # Exactly what the admin form's EMPTY_FORM sends on first save,
        # before any cover has been chosen.
        payload = BookCreate(title="Der Weg", level="A1", cover_url="")
        self.assertEqual(payload.cover_url, "")

    def test_create_without_cover_url_still_works(self):
        payload = BookCreate(title="Der Weg", level="A1")
        self.assertIsNone(payload.cover_url)

    def test_update_with_cover_url_is_valid(self):
        payload = BookUpdate(cover_url="https://vizu-deutsch.com/uploads/images/new-cover.jpg")
        self.assertEqual(payload.cover_url, "https://vizu-deutsch.com/uploads/images/new-cover.jpg")


class TestExtraForbidStillRejectsUnknownFields(unittest.TestCase):
    """The fix adds exactly the one missing field - it must not loosen
    extra="forbid" for a genuinely unknown field (e.g. a typo, or a
    stray lesson_id - Books are level-tagged only, never lesson-scoped,
    see app/models/book.py's own docstring)."""

    def test_create_rejects_unknown_field(self):
        with self.assertRaises(ValidationError) as ctx:
            BookCreate(title="Der Weg", level="A1", lesson_id="some-lesson-id")
        self.assertIn("extra_forbidden", str(ctx.exception))

    def test_update_rejects_unknown_field(self):
        with self.assertRaises(ValidationError):
            BookUpdate(cover_urll="typo")


class TestRequireAdminPanelAccess(unittest.TestCase):
    """401 (no/invalid token) happens upstream in get_current_user, not
    here - this dependency only decides 403 (wrong role) vs pass-
    through, using the exact same shared dependency every other admin
    router (videos, quizzes, ...) already relies on - nothing
    Books-specific about it."""

    def _run(self, coro):
        return asyncio.run(coro)

    def test_admin_panel_role_passes(self):
        for role in ("SUPER_ADMIN", "ADMIN", "CONTENT_MANAGER"):
            with self.subTest(role=role):
                user = MagicMock(role=role)
                result = self._run(require_admin_panel_access(current_user=user))
                self.assertIs(result, user)

    def test_student_role_is_403_not_401(self):
        user = MagicMock(role="STUDENT")
        with self.assertRaises(HTTPException) as ctx:
            self._run(require_admin_panel_access(current_user=user))
        self.assertEqual(ctx.exception.status_code, 403)


class TestUploadPdfContentTypeValidation(unittest.TestCase):
    def _run(self, coro):
        return asyncio.run(coro)

    def _make_upload_file(self, content_type: str, content: bytes = b"%PDF-1.4 fake"):
        upload = MagicMock()
        upload.content_type = content_type
        upload.filename = "book.pdf"

        async def _read():
            return content

        async def _seek(pos):
            return None

        upload.read = _read
        upload.seek = _seek
        return upload

    def test_non_pdf_content_type_is_rejected_with_400_not_422(self):
        service = BookService(db=MagicMock())
        book = MagicMock(storage_key=None)
        upload = self._make_upload_file("image/png")

        with self.assertRaises(HTTPException) as ctx:
            self._run(service.upload_pdf(book, upload))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_pdf_content_type_is_accepted(self):
        db = MagicMock()
        service = BookService(db=db)
        book = MagicMock(storage_key=None)
        upload = self._make_upload_file("application/pdf")

        # storage.upload is an actual filesystem write in production —
        # stub it out for this unit test (same reasoning as every other
        # upload_pdf/replace_video-style test in this codebase: content-
        # type validation is what's under test here, not disk I/O).
        async def _noop_upload(file, key):
            return None

        import app.services.book.service as book_service_module

        original_upload = book_service_module.storage.upload
        book_service_module.storage.upload = _noop_upload
        try:
            result = self._run(service.upload_pdf(book, upload))
        finally:
            book_service_module.storage.upload = original_upload

        self.assertTrue(result.storage_key.endswith(".pdf"))


if __name__ == "__main__":
    unittest.main()
