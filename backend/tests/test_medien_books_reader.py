"""Bibliothek reader: the server-side PREVIEW of PAID books (first N pages only — a separate PDF, never the original), full access for owners / free
books / staff, the access-checked PDF download, the page count, and the reading position (page + scroll + last opened).
Every page of the test PDFs carries uncompressed `PAGEMARK<nnn>` text, so a test can prove which pages a delivered file contains.
Integration test on a throwaway database (VIZU_WB_TEST_DB_URL)."""

import io
import re
import unittest

from tests.medien_base import MedienBase, make_pdf


def marks(data: bytes) -> set[int]:
    return {int(m) for m in re.findall(rb"PAGEMARK(\d{3})", data)}


class TestReader(MedienBase):
    def fetch(self, url, **kw):
        self.as_(None)
        return self.client.get(url, **kw)

    def test_1_page_count_default_preview_and_validation(self):
        from pypdf import PdfReader

        book = self.new_book("Count", access_type="PAID", price=40000)
        self.assertEqual((book["page_count"], book["preview_pages_count"]), (15, 10))
        free = self.new_book("FreeCount")
        self.assertEqual((free["page_count"], free["preview_pages_count"]), (15, 10))
        for bad in (-1, 501):
            self.api("put", f"/admin/medien/books/{book['id']}", "admin", expect=422, json={"preview_pages_count": bad})
        self.assertEqual(self.api("put", f"/admin/medien/books/{book['id']}", "admin", json={"preview_pages_count": 3}).json()["preview_pages_count"], 3)
        self.assertEqual(self.api("put", f"/admin/medien/books/{book['id']}", "admin", json={"preview_pages_count": 10}).json()["preview_pages_count"], 10)
        # a book created with its own preview length
        own = self.new_book("OwnPreview", access_type="PAID", price=1000, preview_pages_count=4)
        self.assertEqual(own["preview_pages_count"], 4)
        # an unreadable PDF is kept but has no page count (and so no preview)
        broken = self.api("post", "/admin/medien/books", "admin", json={"title": self.title("Broken"), "status": "PUBLISHED", "access_type": "PAID", "price": 5000}).json()
        broken = self.api("post", f"/admin/medien/books/{broken['id']}/file", "admin", files={"file": ("b.pdf", b"%PDF-1.4\nnot really a pdf\n%%EOF", "application/pdf")}).json()
        self.assertEqual((broken["page_count"], broken["file_status"]), (None, "ok"))
        self.api("post", f"/medien/books/{broken['id']}/open", "a", expect=403)  # nothing to preview: locked
        self.assertEqual(len(PdfReader(io.BytesIO(make_pdf(15))).pages), 15)

    def test_2_a_student_without_the_book_gets_only_the_first_pages(self):
        from pypdf import PdfReader

        book = self.new_book("Preview", access_type="PAID", price=40000)
        detail = self.api("get", f"/medien/books/{book['id']}", "a").json()
        self.assertEqual((detail["locked"], detail["preview_available"], detail["can_download"], detail["preview_pages_count"], detail["page_count"]), (True, True, False, 10, 15))
        opened = self.api("post", f"/medien/books/{book['id']}/open", "a").json()
        self.assertEqual((opened["mode"], opened["preview_pages"], opened["total_pages"], opened["can_download"]), ("preview", 10, 15, False))
        self.assertNotIn("previews", str(opened) + str(detail))  # no storage names
        pdf = self.fetch(opened["url"])
        self.assertEqual((pdf.status_code, pdf.headers["content-type"], pdf.headers["cache-control"], pdf.headers["x-content-type-options"]), (200, "application/pdf", "private, no-store", "nosniff"))
        self.assertEqual(len(PdfReader(io.BytesIO(pdf.content)).pages), 10)
        self.assertEqual(marks(pdf.content), set(range(1, 11)), "pages 1-10 are in the file, page 11 and later are not anywhere in it")
        self.assertLess(len(pdf.content), len(make_pdf(15)))
        # Range requests work (pdf.js reads like that)
        part = self.fetch(opened["url"], headers={"Range": "bytes=0-99"})
        self.assertEqual((part.status_code, len(part.content)), (206, 100))
        # the preview is a different file from the original, built once and cached
        files = {p for p in self.disk() if p.startswith("previews/")}
        self.assertEqual(len(files), 1)
        self.api("post", f"/medien/books/{book['id']}/open", "a")
        self.assertEqual({p for p in self.disk() if p.startswith("previews/")}, files)
        # no way to the whole file: no download, the preview token on other routes, the original's path
        self.api("post", f"/medien/books/{book['id']}/download-link", "a", expect=403)
        token = opened["url"].split("token=")[1]
        self.assertEqual(self.fetch(f"/api/v1/medien/download/book/{book['id']}?token={token}").status_code, 403)
        self.assertEqual(self.fetch(f"/api/v1/medien/stream/BOOK/{book['id']}").status_code, 422)
        self.assertEqual(self.fetch(f"/api/v1/medien/stream/BOOK/{book['id']}?token=garbage").status_code, 401)
        other = self.new_book("Other", access_type="PAID", price=1000)
        self.assertEqual(self.fetch(f"/api/v1/medien/stream/BOOK/{other['id']}?token={token}").status_code, 403)  # a token is for one book only
        self.assertEqual(self.fetch(f"/protected_storage/medien/{book['id']}.pdf").status_code, 404)
        # nobody else can hand the preview token out as a full-book token: the same token on the file route is still only the preview
        again = self.fetch(f"/api/v1/medien/stream/BOOK/{book['id']}?token={token}")
        self.assertEqual(marks(again.content), set(range(1, 11)))

    def test_3_changing_the_preview_length_or_the_pdf_changes_the_preview(self):
        book = self.new_book("Changing", access_type="PAID", price=40000)
        first = self.api("post", f"/medien/books/{book['id']}/open", "a").json()
        self.assertEqual(marks(self.fetch(first["url"]).content), set(range(1, 11)))
        self.api("put", f"/admin/medien/books/{book['id']}", "admin", json={"preview_pages_count": 3})
        self.assertFalse([p for p in self.disk() if p.startswith("previews/") and str(book["id"]) in p], "the old preview is removed")
        second = self.api("post", f"/medien/books/{book['id']}/open", "a").json()
        self.assertEqual((second["preview_pages"], marks(self.fetch(second["url"]).content)), (3, {1, 2, 3}))
        self.api("put", f"/admin/medien/books/{book['id']}", "admin", json={"preview_pages_count": 100})  # more than the book has: everything but the last page
        third = self.api("post", f"/medien/books/{book['id']}/open", "a").json()
        self.assertEqual((third["preview_pages"], marks(self.fetch(third["url"]).content)), (14, set(range(1, 15))))
        self.api("put", f"/admin/medien/books/{book['id']}", "admin", json={"preview_pages_count": 5})
        # a new PDF: other page count, other preview
        replaced = self.api("post", f"/admin/medien/books/{book['id']}/file", "admin", files={"file": ("b.pdf", make_pdf(8), "application/pdf")}).json()
        self.assertEqual(replaced["page_count"], 8)
        fourth = self.api("post", f"/medien/books/{book['id']}/open", "a").json()
        self.assertEqual((fourth["total_pages"], fourth["preview_pages"], marks(self.fetch(fourth["url"]).content)), (8, 5, {1, 2, 3, 4, 5}))
        # preview 0 = no preview at all
        self.api("put", f"/admin/medien/books/{book['id']}", "admin", json={"preview_pages_count": 0})
        self.api("post", f"/medien/books/{book['id']}/open", "a", expect=403)
        self.assertFalse(self.api("get", f"/medien/books/{book['id']}", "a").json()["preview_available"])
        # deleting the book removes its previews and files
        self.api("put", f"/admin/medien/books/{book['id']}", "admin", json={"preview_pages_count": 2})
        self.api("post", f"/medien/books/{book['id']}/open", "a")
        self.api("delete", f"/admin/medien/books/{book['id']}", "admin", expect=204)
        self.assertFalse([p for p in self.disk() if p.startswith(("previews/", "books/")) and str(book["id"]) in p])

    def test_3b_a_preview_never_hands_out_the_whole_book(self):
        """A short paid book with the default preview of 10 pages: its last page stays closed; a one-page book has no preview at all."""
        short = self.new_book("Short", pages=4, access_type="PAID", price=30000)
        detail = self.api("get", f"/medien/books/{short['id']}", "a").json()
        self.assertEqual((detail["preview_available"], detail["preview_pages_count"], detail["page_count"]), (True, 3, 4))
        opened = self.api("post", f"/medien/books/{short['id']}/open", "a").json()
        self.assertEqual((opened["preview_pages"], opened["total_pages"]), (3, 4))
        self.assertEqual(marks(self.fetch(opened["url"]).content), {1, 2, 3})
        # the reading position of a preview reader stays inside the free pages and the book's total is the book's, not the preview's
        saved = self.api("put", f"/medien/progress/BOOK/{short['id']}", "a", json={"position": 9, "total": 3, "completed": True}).json()
        self.assertEqual((saved["position"], saved["total"], saved["completed"]), (3, 4, False))
        one = self.new_book("OnePage", pages=1, access_type="PAID", price=30000)
        self.assertFalse(self.api("get", f"/medien/books/{one['id']}", "a").json()["preview_available"])
        self.api("post", f"/medien/books/{one['id']}/open", "a", expect=403)
        self.api("put", f"/medien/progress/BOOK/{one['id']}", "a", expect=403, json={"position": 1})

    def test_4_owners_free_books_and_staff_get_the_whole_pdf_and_may_download(self):
        paid = self.new_book("Owned", access_type="PAID", price=40000)
        original = make_pdf(15, "Owned")
        free = self.new_book("FreeRead")
        self.api("post", "/admin/medien/purchases/grant", "super", json={"kind": "BOOK", "content_id": paid["id"], "user_id": str(self.users["a"].id)})
        for who, book in (("a", paid), ("b", free), ("admin", paid)):
            opened = self.api("post", f"/medien/books/{book['id']}/open", who).json()
            self.assertEqual((opened["mode"], opened["preview_pages"], opened["total_pages"], opened["can_download"]), ("full", None, 15, True), who)
            self.assertEqual(marks(self.fetch(opened["url"]).content), set(range(1, 16)), who)
        self.api("post", f"/medien/books/{paid['id']}/open", "b", expect=200)  # b: preview of the paid one
        link = self.api("post", f"/medien/books/{paid['id']}/download-link", "a").json()
        self.assertEqual(link["filename"], f"{self.title('Owned')}.pdf")
        got = self.fetch(link["url"])
        self.assertEqual((got.status_code, got.headers["content-type"]), (200, "application/pdf"))
        self.assertRegex(got.headers["content-disposition"], r'^attachment; filename')
        self.assertIn("Owned", got.headers["content-disposition"])
        self.assertEqual(got.headers["cache-control"], "private, no-store")
        self.assertEqual(marks(got.content), set(range(1, 16)))
        self.assertEqual(len(got.content), len(self.api("get", f"/admin/medien/books/{paid['id']}/file", "admin").content), "the original, not re-encoded")
        self.assertEqual(self.api("post", f"/medien/books/{free['id']}/download-link", "b").json()["filename"], f"{self.title('FreeRead')}.pdf")
        # the link only works for its book, its user's access is re-checked on every request
        self.assertEqual(self.fetch(link["url"].replace(str(paid["id"]), str(free["id"]))).status_code, 403)
        self.assertEqual(self.fetch(link["url"].split("?")[0]).status_code, 422)
        self.api("post", f"/medien/books/{paid['id']}/download-link", "b", expect=403)
        purchases = self.api("get", "/admin/medien/purchases", "super").json()
        mine = next(p for p in purchases if p["content_id"] == paid["id"] and p["user_id"] == str(self.users["a"].id))
        self.api("post", f"/admin/medien/purchases/{mine['id']}/decision", "super", json={"status": "REVOKED"})
        self.assertEqual(self.fetch(link["url"]).status_code, 403, "revoked: the issued download link stops working")
        self.api("post", f"/medien/books/{paid['id']}/download-link", "a", expect=403)
        self.assertEqual(self.api("post", f"/medien/books/{paid['id']}/open", "a").json()["mode"], "preview")
        # anonymous / students on admin-only things
        self.as_(None)
        for method, url in (("post", f"/api/v1/medien/books/{paid['id']}/open"), ("post", f"/api/v1/medien/books/{paid['id']}/download-link")):
            self.assertEqual(getattr(self.client, method)(url).status_code, 401, url)

    def test_5_draft_and_hidden_books_have_no_preview(self):
        book = self.new_book("Draft", access_type="PAID", price=40000, status="DRAFT")
        self.api("post", f"/medien/books/{book['id']}/open", "a", expect=404)
        self.api("put", f"/medien/progress/BOOK/{book['id']}", "a", expect=404, json={"position": 1, "total": 15})
        self.assertEqual(self.api("post", f"/medien/books/{book['id']}/open", "admin").json()["mode"], "full")  # staff see drafts

    def test_6_reading_position_page_scroll_and_last_opened(self):
        free = self.new_book("Progress")
        detail = self.api("get", f"/medien/books/{free['id']}", "a").json()
        self.assertIsNone(detail["progress"])
        opened = self.api("post", f"/medien/books/{free['id']}/open", "a").json()
        self.assertEqual((opened["progress"]["position"], opened["progress"]["scroll"]) , (0, None))
        self.assertIsNotNone(opened["progress"]["opened_at"], "last opened is stored when the reader opens")
        saved = self.api("put", f"/medien/progress/BOOK/{free['id']}", "a", json={"position": 7, "total": 15, "scroll": 0.42}).json()
        self.assertEqual((saved["position"], saved["total"], saved["scroll"], saved["completed"]), (7, 15, 0.42, False))
        self.assertIsNotNone(saved["opened_at"])
        again = self.api("post", f"/medien/books/{free['id']}/open", "a").json()
        self.assertEqual((again["progress"]["position"], again["progress"]["scroll"]), (7, 0.42))  # "continue reading" has everything
        # a new page without a scroll value starts at the top; the same page keeps its scroll
        self.assertIsNone(self.api("put", f"/medien/progress/BOOK/{free['id']}", "a", json={"position": 8, "total": 15}).json()["scroll"])
        self.assertEqual(self.api("put", f"/medien/progress/BOOK/{free['id']}", "a", json={"position": 8, "total": 15, "scroll": 0.9}).json()["scroll"], 0.9)
        self.assertEqual(self.api("put", f"/medien/progress/BOOK/{free['id']}", "a", json={"position": 8, "total": 15}).json()["scroll"], 0.9)
        for bad in ({"position": 1, "scroll": 1.5}, {"position": 1, "scroll": -0.1}, {"position": 1, "scroll": "x"}, {"position": -1}):
            self.api("put", f"/medien/progress/BOOK/{free['id']}", "a", expect=422, json=bad)
        done = self.api("put", f"/medien/progress/BOOK/{free['id']}", "a", json={"position": 15, "total": 15, "scroll": 1}).json()
        self.assertTrue(done["completed"])
        # another student has their own position
        self.assertIsNone(self.api("get", f"/medien/books/{free['id']}", "b").json()["progress"])
        self.assertEqual(self.api("get", f"/medien/progress/BOOK/{free['id']}", "b").json(), None)

    def test_7_a_preview_reader_keeps_a_position_only_inside_the_free_pages(self):
        paid = self.new_book("PreviewProgress", access_type="PAID", price=40000)
        self.api("post", f"/medien/books/{paid['id']}/open", "a")
        saved = self.api("put", f"/medien/progress/BOOK/{paid['id']}", "a", json={"position": 14, "total": 15, "scroll": 0.3}).json()
        self.assertEqual((saved["position"], saved["completed"]), (10, False), "clamped to the preview, never 'finished'")
        self.assertEqual(self.api("post", f"/medien/books/{paid['id']}/open", "a").json()["progress"]["position"], 10)
        self.api("put", f"/admin/medien/books/{paid['id']}", "admin", json={"preview_pages_count": 0})
        self.api("put", f"/medien/progress/BOOK/{paid['id']}", "a", expect=403, json={"position": 2, "total": 15})  # no preview: no position either
        self.api("put", f"/medien/progress/BOOK/{paid['id']}", "b", expect=403, json={"position": 2, "total": 15})

    def test_8_older_books_without_a_page_count_get_one_when_first_opened(self):
        from app.models.medien import MediaBook

        book = self.new_book("Legacy", access_type="PAID", price=40000)
        row = self.refresh(MediaBook, book["id"])
        row.page_count = None
        self.sess.commit()
        self.assertEqual(self.api("get", f"/admin/medien/books?q={self.tag}%20Legacy", "admin").json()["items"][0]["page_count"], None)
        opened = self.api("post", f"/medien/books/{book['id']}/open", "a").json()
        self.assertEqual(opened["total_pages"], 15)
        self.assertEqual(self.refresh(MediaBook, book["id"]).page_count, 15)

    def test_9_safe_download_names(self):
        from app.services.medien import common as c

        self.assertEqual(c.safe_filename("Deutsch A1 – Das große Buch"), "Deutsch A1 Das große Buch.pdf")
        self.assertEqual(c.safe_filename('../../etc/passwd"\r\nX-Evil: 1'), "etc passwd X-Evil 1.pdf")
        self.assertEqual(c.safe_filename(""), "Buch.pdf")
        self.assertEqual(c.safe_filename(None, "txt"), "Buch.txt")
        self.assertLessEqual(len(c.safe_filename("x" * 500)), 104)
        self.assertNotRegex(c.safe_filename("a/b\\c:d*e?f|g<h>i"), r'[/\\:*?|<>"]')


if __name__ == "__main__":
    unittest.main()
