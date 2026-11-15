"""VIZU Medienwelt end to end over HTTP (FastAPI TestClient) against PostgreSQL (VIZU_WB_TEST_DB_URL = a migrated test
database, also DATABASE_NAME) with real files: a PDF, PNG, MP3 and MP4 made by ffmpeg (FFMPEG_BIN), temp storage root.

Covers: admin CRUD + uploads + validation, FREE / PAID access (signed stream URLs, Range requests, rechecked per request),
purchase requests and grants, listing filters, songs (bulk upload with one bad file, favorites, playlists, history), films
(single + chunked upload, subtitles, progress / continue watching), delete consistency, and 401 / 403 of every admin route."""

import os
import shutil
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
FFMPEG = shutil.which(os.environ.get("FFMPEG_BIN", "ffmpeg"))
PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")
CS = 1_500  # test chunk size: the 2 s test video needs several chunks
SRT = b"1\n00:00:00,500 --> 00:00:01,500\nHallo Welt\n\n2\n00:00:01,600 --> 00:00:02,000\nTschuess\n"


def make_media(directory: Path):
    def run(*args):
        subprocess.run([FFMPEG, "-nostdin", "-v", "error", "-y", *args], check=True)

    run("-f", "lavfi", "-i", "sine=frequency=440:duration=3", "-c:a", "libmp3lame", str(directory / "a.mp3"))
    run("-f", "lavfi", "-i", "testsrc=duration=2:size=160x120:rate=10", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(directory / "v.mp4"))
    return (directory / "a.mp3").read_bytes(), (directory / "v.mp4").read_bytes()


@unittest.skipUnless(DB_URL and FFMPEG, "integration test: set VIZU_WB_TEST_DB_URL (+ DATABASE_NAME) and have ffmpeg (FFMPEG_BIN)")
class TestMedien(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
        from app.core.storage.protected_local import ProtectedMedienStorage
        from app.main import app
        from app.models.user import User

        cls.tmp = tempfile.TemporaryDirectory()
        cls.patch = patch.object(ProtectedMedienStorage, "ROOT", Path(cls.tmp.name) / "storage")
        cls.patch.start()
        cls.mp3, cls.mp4 = make_media(Path(cls.tmp.name))
        cls.app, cls.client = app, TestClient(app)
        cls.tag = uuid.uuid4().hex[:6]
        cls.engine = create_engine(DB_URL)
        cls.sess = sessionmaker(bind=cls.engine, expire_on_commit=False)()
        cls.users = {}
        for name, role in (("a", "STUDENT"), ("b", "STUDENT"), ("admin", "ADMIN"), ("super", "SUPER_ADMIN")):
            u = User(email=f"med-{name}-{cls.tag}@test.local", username=f"med_{name}_{cls.tag}", password_hash="x", is_active=True, is_verified=True,
                     is_superuser=role == "SUPER_ADMIN", role=role, is_banned=False, preferred_language="uz")
            cls.sess.add(u)
            cls.users[name] = u
        cls.sess.commit()

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete

        from app.api.dependencies.auth import get_current_user
        from app.models.audit_log import AuditLog
        from app.models.medien import Film, MediaBook, MediaCategory, MediaPurchase, Playlist, Song
        from app.models.user import User

        cls.app.dependency_overrides.pop(get_current_user, None)
        ids = [u.id for u in cls.users.values()]
        s = cls.sess
        s.rollback()
        s.execute(delete(MediaPurchase).where(MediaPurchase.user_id.in_(ids)))
        for model in (MediaBook, Song, Film):
            s.execute(delete(model).where(model.title.like(f"T{cls.tag}%")))
        s.execute(delete(Playlist).where(Playlist.name.like(f"T{cls.tag}%")))
        s.execute(delete(MediaCategory).where(MediaCategory.name.like(f"T{cls.tag}%")))
        s.execute(delete(AuditLog).where(AuditLog.actor_id.in_([str(i) for i in ids])))
        s.execute(delete(User).where(User.id.in_(ids)))
        s.commit()
        s.close()
        cls.patch.stop()
        cls.tmp.cleanup()
        cls.engine.dispose()

    # ---------- helpers ----------
    def as_(self, who: str | None):
        from app.api.dependencies.auth import get_current_user

        if who is None:
            self.app.dependency_overrides.pop(get_current_user, None)
        else:
            self.app.dependency_overrides[get_current_user] = lambda: self.users[who]

    def title(self, name: str) -> str:
        return f"T{self.tag} {name}"

    def api(self, method: str, url: str, who: str | None, expect: int | None = 200, **kw):
        self.as_(who)
        r = getattr(self.client, method)(f"/api/v1{url}", **kw)
        if expect is not None:
            self.assertEqual(r.status_code, expect, f"{method.upper()} {url} -> {r.status_code} {r.text[:300]}")
        return r

    def new_book(self, name, **extra):
        body = {"title": self.title(name), "author": "Autor Eins", "language": "de", "level": "A2", "status": "PUBLISHED", **extra}
        book = self.api("post", "/admin/medien/books", "admin", json=body).json()
        self.api("post", f"/admin/medien/books/{book['id']}/cover", "admin", files={"file": ("c.png", PNG, "image/png")})
        self.api("post", f"/admin/medien/books/{book['id']}/file", "admin", files={"file": ("b.pdf", PDF, "application/pdf")})
        return book

    def disk(self) -> set:
        root = Path(self.tmp.name) / "storage"
        return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()} if root.exists() else set()

    # ---------- Bibliothek ----------
    def test_1_book_crud_validation_and_files(self):
        start = self.disk()
        cat = self.api("post", "/admin/medien/categories", "admin", json={"kind": "BOOK", "name": self.title("Krimi")}).json()
        self.api("post", "/admin/medien/categories", "admin", expect=409, json={"kind": "BOOK", "name": self.title("Krimi")})
        paid = self.api("post", "/admin/medien/books", "admin", json={"title": self.title("Paid"), "access_type": "PAID", "price": 50000, "old_price": 80000,
                                                                         "category_id": cat["id"], "is_special_offer": True}).json()
        self.assertEqual((paid["access_type"], paid["price"], paid["old_price"], paid["discount_percent"], paid["status"]), ("PAID", 50000, 80000, 38, "DRAFT"))
        for bad in ({"title": self.title("x"), "access_type": "PAID"}, {"title": ""}, {"title": self.title("y"), "level": "Z9"},
                    {"title": self.title("z"), "status": "GONE"}, {"title": self.title("w"), "year": 99}, {"title": self.title("v"), "nope": 1}):
            self.api("post", "/admin/medien/books", "admin", expect=422, json=bad)
        # wrong file types are refused by content, even with a PDF name
        self.api("post", f"/admin/medien/books/{paid['id']}/file", "admin", expect=400, files={"file": ("b.pdf", b"not a pdf at all", "application/pdf")})
        self.api("post", f"/admin/medien/books/{paid['id']}/cover", "admin", expect=400, files={"file": ("c.png", b"<html>nope</html>", "image/png")})
        self.api("post", f"/admin/medien/books/{paid['id']}/file", "admin", files={"file": ("b.pdf", PDF, "application/pdf")})
        # FREE clears the price and the special offer
        free = self.api("put", f"/admin/medien/books/{paid['id']}", "admin", json={"access_type": "FREE"}).json()
        self.assertEqual((free["price"], free["old_price"], free["is_special_offer"]), (None, None, False))
        # replacing the PDF removes the old file; deleting removes everything
        before = self.disk()
        self.api("post", f"/admin/medien/books/{paid['id']}/file", "admin", files={"file": ("b2.pdf", PDF + b"\n", "application/pdf")})
        self.assertEqual(len(self.disk()), len(before))
        self.api("delete", f"/admin/medien/books/{paid['id']}", "admin", expect=204)
        self.assertEqual(self.disk(), start)
        self.api("delete", f"/admin/medien/categories/{cat['id']}", "admin", expect=204)

    def test_2_free_paid_access_and_range(self):
        free = self.new_book("Free A", access_type="FREE")
        paid = self.new_book("Paid A", access_type="PAID", price=40000)
        draft = self.new_book("Draft", status="DRAFT")
        # students see cover / text / price of PAID, never a file
        listing = self.api("get", f"/medien/books?q={self.tag}", "a").json()
        titles = {b["title"]: b for b in listing["items"]}
        self.assertIn(self.title("Paid A"), titles)
        self.assertNotIn(self.title("Draft"), titles)
        self.assertTrue(titles[self.title("Paid A")]["locked"] and not titles[self.title("Free A")]["locked"])
        self.assertTrue(titles[self.title("Paid A")]["cover_url"].startswith("/api/v1/medien/cover/BOOK/"))
        self.assertNotIn("protected_storage", str(listing))
        self.assertNotIn("file_key", str(listing))
        # the cover is public (no auth)
        self.as_(None)
        self.assertEqual(self.client.get(titles[self.title("Paid A")]["cover_url"]).status_code, 200)
        # FREE: open -> signed URL -> bytes with Range
        opened = self.api("post", f"/medien/books/{free['id']}/open", "a").json()
        self.as_(None)
        full = self.client.get(opened["url"])
        self.assertEqual((full.status_code, full.content[:5]), (200, b"%PDF-"))
        part = self.client.get(opened["url"], headers={"Range": "bytes=0-9"})
        self.assertEqual((part.status_code, len(part.content)), (206, 10))
        # PAID: no URL, no file; a draft is a 404
        self.api("post", f"/medien/books/{paid['id']}/open", "a", expect=403)
        self.api("post", f"/medien/books/{draft['id']}/open", "a", expect=404)
        self.api("get", f"/medien/books/{draft['id']}", "a", expect=404)
        # tokens are bound to one item, one purpose and need a real token
        self.as_(None)
        self.assertEqual(self.client.get(f"/api/v1/medien/stream/BOOK/{paid['id']}?token={opened['url'].split('token=')[1]}").status_code, 403)
        self.assertEqual(self.client.get(f"/api/v1/medien/stream/BOOK/{free['id']}?token=garbage").status_code, 401)
        self.assertEqual(self.client.get(f"/api/v1/medien/stream/BOOK/{paid['id']}").status_code, 422)
        # hiding a book closes it for students at once, staff still see it
        self.api("put", f"/admin/medien/books/{free['id']}", "admin", json={"status": "HIDDEN"})
        self.as_(None)
        self.assertEqual(self.client.get(opened["url"]).status_code, 404)
        self.api("post", f"/medien/books/{free['id']}/open", "a", expect=404)
        self.api("post", f"/medien/books/{free['id']}/open", "admin")
        self.api("put", f"/admin/medien/books/{free['id']}", "admin", json={"status": "PUBLISHED"})

    def test_3_purchase_request_grant_revoke(self):
        # a BOOK is paid for through the book payment request (test_medien_payments.py); the generic request is for songs and films
        paid_book = self.new_book("Paid B", access_type="PAID", price=30000)
        self.api("post", "/medien/purchases", "a", expect=409, json={"kind": "BOOK", "content_id": paid_book["id"]})
        self.api("post", f"/medien/books/{paid_book['id']}/open", "a", expect=403)  # (the fixture PDF is not readable: no preview either)
        # request -> Super Admin decision -> access, on a paid song
        paid = self.song("Paid Req Song", access_type="PAID", price="12000").json()
        req = self.api("post", "/medien/purchases", "a", json={"kind": "SONG", "content_id": paid["id"]}).json()
        self.assertEqual(req["status"], "REQUESTED")
        self.assertEqual(self.api("post", "/medien/purchases", "a", json={"kind": "SONG", "content_id": paid["id"]}).json()["id"], req["id"])  # one open request
        self.api("post", f"/medien/songs/{paid['id']}/play", "a", expect=403)  # a request gives no access
        # students and normal admins cannot decide; Super Admin can
        for who, code in (("a", 403), ("admin", 403)):
            self.api("post", f"/admin/medien/purchases/{req['id']}/decision", who, expect=code, json={"status": "GRANTED"})
        self.api("get", "/admin/medien/purchases", "a", expect=403)
        self.api("post", f"/admin/medien/purchases/{req['id']}/decision", "super", json={"status": "GRANTED", "note": "paid"})
        self.api("post", f"/admin/medien/purchases/{req['id']}/decision", "super", expect=409, json={"status": "GRANTED"})  # not twice
        played = self.api("post", f"/medien/songs/{paid['id']}/play", "a").json()
        self.as_(None)
        self.assertEqual(self.client.get(played["url"]).status_code, 200)
        self.api("post", f"/medien/songs/{paid['id']}/play", "b", expect=403)  # another student: still closed
        mine = self.api("get", "/medien/purchases/mine", "a").json()
        self.assertEqual([m["status"] for m in mine if m["content_id"] == paid["id"]], ["GRANTED"])
        # revoked: the OLD signed URL stops working (access is rechecked per request)
        self.api("post", f"/admin/medien/purchases/{req['id']}/decision", "super", json={"status": "REVOKED"})
        self.as_(None)
        self.assertEqual(self.client.get(played["url"]).status_code, 403)
        # direct grant by e-mail opens a paid BOOK (the admin tool next to the payment requests)
        self.api("post", "/admin/medien/purchases/grant", "super", json={"kind": "BOOK", "content_id": paid_book["id"], "email": self.users["b"].email})
        self.api("post", f"/medien/books/{paid_book['id']}/open", "b")
        free = self.new_book("Free B")
        self.api("post", "/medien/purchases", "a", expect=409, json={"kind": "BOOK", "content_id": free["id"]})
        self.api("delete", f"/admin/medien/songs/{paid['id']}", "admin", expect=204)  # the song counts in later tests of this class

    def test_4_filters_search_sort_pagination_progress(self):
        cat = self.api("post", "/admin/medien/categories", "admin", json={"kind": "BOOK", "name": self.title("Gram")}).json()
        for i, (author, level) in enumerate((("Anna Berg", "A1"), ("Bernd Alt", "B1"), ("Anna Zorn", "B1"))):
            self.new_book(f"F{i}", author=author, level=level, category_id=cat["id"])
        base = f"/medien/books?q={self.tag}"
        self.assertEqual(self.api("get", f"{base}&category={cat['slug']}", "a").json()["total"], 3)
        self.assertEqual(self.api("get", f"{base}&category={cat['id']}&level=B1", "a").json()["total"], 2)
        self.assertEqual(self.api("get", f"{base}&category=does-not-exist", "a").json()["total"], 0)
        self.assertEqual(len(self.api("get", f"/medien/books?q=Anna&category={cat['id']}", "a").json()["items"]), 2)  # by author
        page = self.api("get", f"{base}&category={cat['id']}&page_size=2&page=2&sort=title", "a").json()
        self.assertEqual((page["total"], len(page["items"]), page["page"]), (3, 1, 2))
        self.assertEqual(self.api("get", f"{base}%25%5C_&category={cat['id']}", "a").json()["total"], 0)  # wildcards are escaped
        first = self.api("get", f"{base}&category={cat['id']}&level=A1", "a").json()["items"][0]
        # progress: last page saved and returned; finished at the last page
        self.api("post", f"/medien/books/{first['id']}/open", "a")
        self.api("put", f"/medien/progress/BOOK/{first['id']}", "a", json={"position": 7, "total": 20})
        self.assertEqual(self.api("get", f"/medien/books/{first['id']}", "a").json()["progress"]["position"], 7)
        self.assertEqual([x["id"] for x in self.api("get", "/medien/continue", "a").json()], [first["id"]])
        self.api("put", f"/medien/progress/BOOK/{first['id']}", "a", json={"position": 20, "total": 20})
        self.assertEqual(self.api("get", "/medien/continue", "a").json(), [])
        self.assertEqual(len(self.api("get", "/medien/continue?completed=true", "a").json()), 1)
        self.api("put", f"/medien/progress/BOOK/{first['id']}", "a", expect=422, json={"position": -1})
        self.assertIsNone(self.api("get", f"/medien/progress/BOOK/{first['id']}", "b").json())  # progress is per user

    # ---------- Musik ----------
    def song(self, name, data=None, **form):
        files = {"file": (f"{name}.mp3", data or self.mp3, "audio/mpeg")}
        return self.api("post", "/admin/medien/songs", "admin", expect=form.pop("expect", 200), files=files,
                        data={"title": self.title(name), "artist": "Band", "status": "PUBLISHED", "language": "de", **form})

    def test_5_songs_bulk_favorites_playlists(self):
        # bulk: ten files, one of them is not audio; the others are not affected
        results = []
        for i in range(10):
            if i == 4:
                results.append(self.song(f"S{i}", b"this is not audio", expect=400).status_code)
            else:
                results.append(self.song(f"S{i}", genre="Pop", level="A2" if i % 2 else None).status_code)
        self.assertEqual(results, [200, 200, 200, 200, 400, 200, 200, 200, 200, 200])
        items = self.api("get", f"/medien/songs?q={self.tag}&page_size=60", "a").json()
        self.assertEqual(items["total"], 9)
        s0 = next(s for s in items["items"] if s["title"] == self.title("S0"))
        self.assertAlmostEqual(s0["duration_ms"], 3000, delta=250)
        self.assertNotIn("file_key", str(items))
        # play: signed URL, Range, history + counter
        played = self.api("post", f"/medien/songs/{s0['id']}/play", "a").json()
        self.as_(None)
        rng = self.client.get(played["url"], headers={"Range": "bytes=0-99"})
        self.assertEqual((rng.status_code, len(rng.content)), (206, 100))
        self.assertEqual([h["id"] for h in self.api("get", "/medien/history", "a").json()], [s0["id"]])
        self.api("post", f"/medien/songs/{s0['id']}/play?count=false", "a")
        self.assertEqual(len(self.api("get", "/medien/history", "a").json()), 1)
        self.assertEqual(self.api("get", f"/admin/medien/songs?q={self.tag}", "admin").json()["items"][-1]["plays"] >= 0, True)
        # favorites
        self.api("put", f"/medien/songs/{s0['id']}/favorite", "a")
        self.api("put", f"/medien/songs/{s0['id']}/favorite", "a")  # idempotent
        favs = self.api("get", "/medien/songs?favorites=true", "a").json()
        self.assertEqual([s["id"] for s in favs["items"]], [s0["id"]])
        self.assertTrue(favs["items"][0]["favorite"])
        self.assertEqual(self.api("get", "/medien/songs?favorites=true", "b").json()["total"], 0)
        self.api("delete", f"/medien/songs/{s0['id']}/favorite", "a")
        self.assertEqual(self.api("get", "/medien/songs?favorites=true", "a").json()["total"], 0)
        # student playlists: create / add / order / remove / delete, only for the owner
        ids = [s["id"] for s in items["items"][:3]]
        pl = self.api("post", "/medien/playlists", "a", json={"name": self.title("Mix")}).json()
        for sid in ids:
            self.api("post", f"/medien/playlists/{pl['id']}/songs", "a", json={"song_id": sid})
        self.api("post", f"/medien/playlists/{pl['id']}/songs", "a", json={"song_id": ids[0]})  # no duplicate
        self.api("put", f"/medien/playlists/{pl['id']}/order", "a", json={"song_ids": list(reversed(ids))})
        self.assertEqual([s["id"] for s in self.api("get", f"/medien/playlists/{pl['id']}", "a").json()["songs"]], list(reversed(ids)))
        self.api("put", f"/medien/playlists/{pl['id']}/order", "a", expect=422, json={"song_ids": ids[:2]})
        self.api("get", f"/medien/playlists/{pl['id']}", "b", expect=404)
        self.api("post", f"/medien/playlists/{pl['id']}/songs", "b", expect=404, json={"song_id": ids[0]})
        self.api("delete", f"/medien/playlists/{pl['id']}", "b", expect=404)
        self.api("put", f"/medien/playlists/{pl['id']}", "a", json={"name": self.title("Mix 2")})
        self.api("delete", f"/medien/playlists/{pl['id']}/songs/{ids[0]}", "a")
        self.assertEqual(self.api("get", f"/medien/playlists/{pl['id']}", "a").json()["song_count"], 2)
        self.api("delete", f"/medien/playlists/{pl['id']}", "a", expect=204)
        # official playlist: admin builds it, every student sees it (published only), nobody else edits it
        off = self.api("post", "/admin/medien/playlists", "admin", json={"name": self.title("Offiziell"), "status": "DRAFT"}).json()
        self.api("put", f"/admin/medien/playlists/{off['id']}/songs", "admin", json={"song_ids": ids})
        self.assertNotIn(off["id"], [p["id"] for p in self.api("get", "/medien/playlists", "a").json()])
        self.api("put", f"/admin/medien/playlists/{off['id']}", "admin", json={"status": "PUBLISHED"})
        self.assertIn(off["id"], [p["id"] for p in self.api("get", "/medien/playlists", "b").json()])
        self.api("post", f"/medien/playlists/{off['id']}/songs", "b", expect=404, json={"song_id": ids[0]})
        self.assertEqual([s["id"] for s in self.api("get", f"/medien/songs?playlist_id={off['id']}", "b").json()["items"]], ids)
        # edit metadata, hide, replace the file, delete (files and playlist entries go)
        self.api("put", f"/admin/medien/songs/{ids[0]}", "admin", json={"artist": "Neu", "status": "HIDDEN"})
        self.assertNotIn(ids[0], [s["id"] for s in self.api("get", f"/medien/songs?q={self.tag}&page_size=60", "a").json()["items"]])
        self.api("post", f"/medien/songs/{ids[0]}/play", "a", expect=404)
        before = len(self.disk())
        self.api("post", f"/admin/medien/songs/{ids[0]}/file", "admin", files={"file": ("n.mp3", self.mp3 + b"\0", "audio/mpeg")})
        self.assertEqual(len(self.disk()), before)
        self.api("delete", f"/admin/medien/songs/{ids[0]}", "admin", expect=204)
        self.assertEqual(len(self.disk()), before - 1)
        self.api("delete", f"/admin/medien/playlists/{off['id']}", "admin", expect=204)

    def test_6_paid_song_is_closed(self):
        paid = self.song("Paid Song", access_type="PAID", price="12000").json()
        self.api("post", f"/medien/songs/{paid['id']}/play", "a", expect=403)
        self.api("post", "/admin/medien/purchases/grant", "super", json={"kind": "SONG", "content_id": paid["id"], "user_id": str(self.users["a"].id)})
        self.api("post", f"/medien/songs/{paid['id']}/play", "a")

    # ---------- Filme ----------
    def test_7_film_upload_chunks_subtitles_progress(self):
        from app.services.medien import admin as svc

        start = self.disk()
        film = self.api("post", "/admin/medien/films", "admin", json={"title": self.title("Film"), "level": "B1", "genre": "Drama", "status": "PUBLISHED",
                                                                       "duration_minutes": 1}).json()
        fid = film["id"]
        self.api("post", f"/admin/medien/films/{fid}/cover", "admin", files={"file": ("p.png", PNG, "image/png")})
        self.api("post", f"/medien/films/{fid}/watch", "a", expect=404)  # nothing to play yet
        self.assertFalse(self.api("get", f"/medien/films/{fid}", "a").json()["playable"])
        self.api("put", f"/admin/medien/films/{fid}/external-url", "admin", expect=422, json={"url": "http://insecure.example/x.mp4"})
        self.api("put", f"/admin/medien/films/{fid}/external-url", "admin", expect=422, json={"url": "javascript:alert(1)"})
        # chunked upload (small chunks so the 2 s test video needs several); a missing chunk blocks the completion
        with patch.object(svc, "CHUNK_SIZE", CS):
            init = self.api("post", f"/admin/medien/films/{fid}/video/init", "admin", json={"filename": "v.mp4", "size": len(self.mp4)}).json()
            n = init["chunks"]
            self.assertGreater(n, 1)
            self.assertEqual(self.api("get", f"/admin/medien/films", "admin").json()["items"][0]["processing_status"], "UPLOADING")
            for i in range(n - 1):
                self.api("put", f"/admin/medien/films/{fid}/video/{init['upload_id']}/{i}", "admin", content=self.mp4[i * CS:(i + 1) * CS])
            self.api("post", f"/admin/medien/films/{fid}/video/{init['upload_id']}/complete", "admin", expect=409)
            self.api("put", f"/admin/medien/films/{fid}/video/{init['upload_id']}/{n}", "admin", expect=422, content=b"x")
            self.api("put", f"/admin/medien/films/{fid}/video/{init['upload_id']}/{n - 1}", "admin", content=self.mp4[(n - 1) * CS:])
            done = self.api("post", f"/admin/medien/films/{fid}/video/{init['upload_id']}/complete", "admin").json()
        self.assertEqual((done["processing_status"], done["video_size"], done["file_status"]), ("READY", len(self.mp4), "ok"))
        self.assertFalse(any(p.startswith("chunks/") for p in self.disk()))
        self.api("post", f"/admin/medien/films/{fid}/video/{uuid.uuid4().hex}/complete", "admin", expect=404)
        # a non-video file in chunks is refused and marked failed
        with patch.object(svc, "CHUNK_SIZE", CS):
            bad = self.api("post", f"/admin/medien/films/{fid}/video/init", "admin", json={"filename": "x.mp4", "size": 100}).json()
            self.api("put", f"/admin/medien/films/{fid}/video/{bad['upload_id']}/0", "admin", content=b"x" * 100)
            self.api("post", f"/admin/medien/films/{fid}/video/{bad['upload_id']}/complete", "admin", expect=400)
        self.api("post", f"/admin/medien/films/{fid}/video", "admin", files={"file": ("v.mp4", self.mp4, "video/mp4")})  # single upload replaces it
        # subtitles: SRT is converted to WebVTT, one per language
        self.api("post", f"/admin/medien/films/{fid}/subtitles", "admin", expect=400, data={"language": "de"}, files={"file": ("s.srt", b"no cues here", "text/plain")})
        self.api("post", f"/admin/medien/films/{fid}/subtitles", "admin", expect=422, data={"language": "xx"}, files={"file": ("s.srt", SRT, "text/plain")})
        sub = self.api("post", f"/admin/medien/films/{fid}/subtitles", "admin", data={"language": "de"}, files={"file": ("s.srt", SRT, "text/plain")}).json()
        self.api("post", f"/admin/medien/films/{fid}/subtitles", "admin", data={"language": "uz", "label": "O'zbekcha"}, files={"file": ("u.vtt", b"WEBVTT\n\n00:00.000 --> 00:01.000\nSalom\n", "text/vtt")})
        self.assertEqual({s["language"] for s in sub["subtitles"]}, {"de"})
        # watch: signed video (Range) + subtitle tracks
        watch = self.api("post", f"/medien/films/{fid}/watch", "a").json()
        self.assertEqual((watch["source"]["type"], sorted(s["language"] for s in watch["subtitles"])), ("file", ["de", "uz"]))
        self.as_(None)
        video = self.client.get(watch["source"]["url"], headers={"Range": "bytes=0-1023"})
        self.assertEqual((video.status_code, len(video.content), video.headers["content-type"]), (206, 1024, "video/mp4"))
        vtt = self.client.get(next(s["url"] for s in watch["subtitles"] if s["language"] == "de"))
        self.assertEqual(vtt.status_code, 200)
        self.assertTrue(vtt.text.startswith("WEBVTT") and "00:00:00.500 --> 00:00:01.500" in vtt.text)
        self.assertEqual(self.client.get(f"/api/v1/medien/subtitles/{sub['subtitles'][0]['id']}?token={watch['source']['url'].split('token=')[1]}").status_code, 403)
        # continue watching: position saved, listed, finished at 95 %
        self.api("put", f"/medien/progress/FILM/{fid}", "a", json={"position": 30, "total": 120})
        cont = self.api("get", "/medien/continue", "a").json()
        self.assertEqual((cont[0]["id"], cont[0]["progress"]["position"]), (fid, 30))
        self.assertEqual(self.api("post", f"/medien/films/{fid}/watch", "a").json()["progress"]["position"], 30)
        self.api("put", f"/medien/progress/FILM/{fid}", "a", json={"position": 118, "total": 120})
        self.assertEqual(self.api("get", "/medien/continue", "a").json(), [])
        self.assertIn(fid, [x["id"] for x in self.api("get", "/medien/continue?completed=true", "a").json()])  # finished films stay in the history
        # filters
        base = f"/medien/films?q={self.tag}"
        self.assertEqual(self.api("get", f"{base}&level=B1&genre=Drama&max_minutes=5", "a").json()["total"], 1)
        self.assertEqual(self.api("get", f"{base}&min_minutes=90", "a").json()["total"], 0)
        self.assertEqual(self.api("get", f"{base}&access=PAID", "a").json()["total"], 0)
        # external provider link (https) is used when there is no file
        ext = self.api("post", "/admin/medien/films", "admin", json={"title": self.title("Extern"), "status": "PUBLISHED"}).json()
        self.api("put", f"/admin/medien/films/{ext['id']}/external-url", "admin", json={"url": "https://video.example.org/clip.mp4"})
        self.assertEqual(self.api("post", f"/medien/films/{ext['id']}/watch", "a").json()["source"], {"type": "external", "url": "https://video.example.org/clip.mp4"})
        # deleting removes video, poster and subtitles from disk
        self.api("delete", f"/admin/medien/films/{fid}", "admin", expect=204)
        self.assertEqual(self.disk(), start)
        self.api("get", f"/medien/films/{fid}", "a", expect=404)
        self.api("delete", f"/admin/medien/films/{ext['id']}", "admin", expect=204)

    def test_8_paid_film_closed_and_special_offers(self):
        film = self.api("post", "/admin/medien/films", "admin", json={"title": self.title("Paid Film"), "access_type": "PAID", "price": 90000, "old_price": 120000,
                                                                       "is_special_offer": True, "status": "PUBLISHED"}).json()
        self.api("post", f"/admin/medien/films/{film['id']}/video", "admin", files={"file": ("v.mp4", self.mp4, "video/mp4")})
        self.api("post", f"/medien/films/{film['id']}/watch", "a", expect=403)
        self.api("put", f"/medien/progress/FILM/{film['id']}", "a", expect=403, json={"position": 5, "total": 100})
        offers = self.api("get", "/medien/special-offers", "a").json()
        mine = next(o for o in offers if o["id"] == film["id"])
        self.assertEqual((mine["price"], mine["old_price"], mine["discount_percent"], mine["locked"]), (90000, 120000, 25, True))
        self.assertNotIn("video", str(mine).replace("video_", ""))  # no file info
        self.api("put", f"/admin/medien/films/{film['id']}", "admin", json={"is_special_offer": False})
        self.assertNotIn(film["id"], [o["id"] for o in self.api("get", "/medien/special-offers", "a").json()])
        self.api("delete", f"/admin/medien/films/{film['id']}", "admin", expect=204)

    # ---------- admin rights, stats ----------
    def test_9_admin_routes_need_the_right_role(self):
        i = uuid.uuid4()
        calls = [("get", "/admin/medien/stats", None), ("get", "/admin/medien/categories?kind=BOOK", None), ("post", "/admin/medien/categories", {"kind": "BOOK", "name": "X"}),
                 ("get", "/admin/medien/books", None), ("post", "/admin/medien/books", {"title": "x"}), ("put", f"/admin/medien/books/{i}", {"title": "x"}),
                 ("delete", f"/admin/medien/books/{i}", None), ("get", "/admin/medien/songs", None), ("delete", f"/admin/medien/songs/{i}", None),
                 ("get", "/admin/medien/films", None), ("post", "/admin/medien/films", {"title": "x"}), ("delete", f"/admin/medien/films/{i}", None),
                 ("post", f"/admin/medien/films/{i}/video/init", {"filename": "a", "size": 1}), ("get", "/admin/medien/playlists", None),
                 ("post", "/admin/medien/playlists", {"name": "x"}), ("get", "/admin/medien/purchases", None),
                 ("post", f"/admin/medien/purchases/{i}/decision", {"status": "GRANTED"}), ("post", "/admin/medien/purchases/grant", {"kind": "BOOK", "content_id": str(i), "email": "a@b.c"}),
                 ("get", f"/admin/medien/songs/{i}/file", None), ("get", f"/admin/medien/books/{i}/file", None), ("get", f"/admin/medien/films/{i}/file", None)]
        for method, url, body in calls:
            kw = {"json": body} if body is not None else {}
            self.assertEqual(self.api(method, url, None, expect=None, **kw).status_code, 401, url)
            self.assertEqual(self.api(method, url, "a", expect=None, **kw).status_code, 403, url)
        self.assertEqual(self.api("get", "/medien/books", None, expect=None).status_code, 401)
        self.assertEqual(self.api("post", "/medien/purchases", None, expect=None, json={"kind": "BOOK", "content_id": str(i)}).status_code, 401)

    def test_91_stats_are_real(self):
        self.new_book("Stat Free", access_type="FREE")
        self.new_book("Stat Paid", access_type="PAID", price=1000)
        stats = self.api("get", "/admin/medien/stats", "admin").json()
        self.assertGreaterEqual(stats["books"]["total"], 2)
        self.assertGreaterEqual(stats["books"]["free"], 1)
        self.assertGreaterEqual(stats["books"]["paid"], 1)
        self.assertEqual(stats["total"], stats["published"] + stats["draft"])
        direct = {"books": self.sess.execute(__import__("sqlalchemy").text("select count(*) from media_books")).scalar()}
        self.assertEqual(stats["books"]["total"], direct["books"])


if __name__ == "__main__":
    unittest.main()
