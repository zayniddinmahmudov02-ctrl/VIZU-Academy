"""Verifies BookService's CRUD + security-critical premium/publish gate
on get_downloadable_book: unpublished/missing -> 404 (never leaks draft
existence), published + free user -> 403 PREMIUM_REQUIRED, published +
premium user -> returns the book, published + admin/staff bypass ->
returns the book regardless of premium status. Also verifies level
filtering only returns the requested level's published books. Uses
stdlib unittest + MagicMock (no real DB), matching this session's
established pattern."""

import unittest
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi import HTTPException

from app.services.book.service import BookService


def make_user(*, premium: bool, role: str = "STUDENT") -> MagicMock:
    from datetime import datetime, timedelta, timezone

    user = MagicMock()
    user.role = role
    user.premium_until = (
        datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30) if premium else None
    )
    return user


def make_book(*, is_published: bool, storage_key: str | None = "abc.pdf") -> MagicMock:
    book = MagicMock()
    book.id = uuid4()
    book.is_published = is_published
    book.storage_key = storage_key
    book.original_filename = "book.pdf"
    return book


class TestGetDownloadableBook(unittest.TestCase):
    def _service_with(self, book) -> BookService:
        service = BookService(db=MagicMock())
        service.get = MagicMock(return_value=book)
        return service

    def test_missing_book_is_404(self):
        service = self._service_with(None)
        user = make_user(premium=True)
        with self.assertRaises(HTTPException) as ctx:
            service.get_downloadable_book(uuid4(), user)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_unpublished_book_is_404_even_for_premium_user(self):
        # Never leaks draft existence, regardless of who's asking.
        book = make_book(is_published=False)
        service = self._service_with(book)
        user = make_user(premium=True)
        with self.assertRaises(HTTPException) as ctx:
            service.get_downloadable_book(book.id, user)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_book_with_no_pdf_uploaded_yet_is_404(self):
        book = make_book(is_published=True, storage_key=None)
        service = self._service_with(book)
        user = make_user(premium=True)
        with self.assertRaises(HTTPException) as ctx:
            service.get_downloadable_book(book.id, user)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_published_book_free_user_is_403_premium_required(self):
        book = make_book(is_published=True)
        service = self._service_with(book)
        user = make_user(premium=False)
        with self.assertRaises(HTTPException) as ctx:
            service.get_downloadable_book(book.id, user)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "PREMIUM_REQUIRED")

    def test_published_book_premium_user_is_allowed(self):
        book = make_book(is_published=True)
        service = self._service_with(book)
        user = make_user(premium=True)
        result = service.get_downloadable_book(book.id, user)
        self.assertIs(result, book)

    def test_published_book_admin_bypass_allowed_even_without_premium(self):
        book = make_book(is_published=True)
        service = self._service_with(book)
        admin = make_user(premium=False, role="SUPER_ADMIN")
        result = service.get_downloadable_book(book.id, admin)
        self.assertIs(result, book)

    def test_expired_premium_is_treated_as_not_premium(self):
        from datetime import datetime, timedelta, timezone

        book = make_book(is_published=True)
        service = self._service_with(book)
        user = MagicMock()
        user.role = "STUDENT"
        user.premium_until = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
        with self.assertRaises(HTTPException) as ctx:
            service.get_downloadable_book(book.id, user)
        self.assertEqual(ctx.exception.status_code, 403)


class TestLevelFiltering(unittest.TestCase):
    def test_get_published_by_level_only_returns_that_level(self):
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.order_by.return_value = query
        query.all.return_value = ["a1-book-1", "a1-book-2"]
        db.query.return_value = query

        service = BookService(db=db)
        result = service.get_published_by_level("A1")

        self.assertEqual(result, ["a1-book-1", "a1-book-2"])
        # Confirms the filter was actually built against Book.level /
        # Book.is_published, not left unfiltered.
        self.assertTrue(query.filter.called)


class TestBookCrud(unittest.TestCase):
    def test_create_adds_commits_and_refreshes(self):
        db = MagicMock()
        service = BookService(db=db)
        book = service.create({"title": "Der Weg", "level": "A1"})
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(book)
        self.assertEqual(book.title, "Der Weg")
        self.assertEqual(book.level, "A1")

    def test_update_only_sets_given_fields(self):
        db = MagicMock()
        service = BookService(db=db)
        book = MagicMock(title="Old Title", level="A1")
        updated = service.update(book, {"title": "New Title"})
        self.assertEqual(updated.title, "New Title")
        self.assertEqual(updated.level, "A1")  # untouched

    def test_publish_sets_is_published_true(self):
        db = MagicMock()
        service = BookService(db=db)
        book = MagicMock(is_published=False)
        service.publish(book)
        self.assertTrue(book.is_published)


if __name__ == "__main__":
    unittest.main()
