"""Musik bulk upload (up to 500 songs) — backend, against PostgreSQL (VIZU_WB_TEST_DB_URL) with ffmpeg (FFMPEG_BIN):
* permissions of the new routes (401 / 403);
* a song is only stored when the file arrived complete (browser SHA-256 = stored SHA-256, else 400 and nothing is left behind);
* duplicates: the same content → 409 SONG_DUPLICATE with the existing id (no second file on disk) unless allow_duplicate; the same NAME with other
  content is not a duplicate; two parallel uploads of one file → exactly one is stored; the pre-check endpoint;
* the metadata queue: a deferred upload is PENDING, the worker reads duration / format / tags one by one, a file that is not audio becomes INVALID
  and DRAFT, one bad file does not stop the queue;
* the hash script for older songs (plan / wrong id / apply);
* VIZU_STRESS_500=1: 500 different files through the API with 6 parallel uploads, then the queue — every file stored exactly once."""

import hashlib
import os
import shutil
import subprocess
import tempfile
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
FFMPEG = shutil.which(os.environ.get("FFMPEG_BIN", "ffmpeg"))


def make_mp3(directory: Path, seconds: float, artist: str | None = None, title: str | None = None) -> bytes:
    path = directory / f"{uuid.uuid4().hex}.mp3"
    meta = (["-metadata", f"artist={artist}"] if artist else []) + (["-metadata", f"title={title}"] if title else [])
    subprocess.run([FFMPEG, "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}", "-c:a", "libmp3lame",
                    "-b:a", "64k", *meta, str(path)], check=True)
    return path.read_bytes()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@unittest.skipUnless(DB_URL and FFMPEG, "integration test: set VIZU_WB_TEST_DB_URL (+ DATABASE_NAME) and have ffmpeg (FFMPEG_BIN)")
class TestSongBulkUpload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
        from app.core.config import settings
        from app.core.storage.protected_local import ProtectedMedienStorage
        from app.main import app
        from app.models.user import User

        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name) / "storage"
        cls.patches = [patch.object(ProtectedMedienStorage, "ROOT", cls.root), patch.object(settings, "SONG_PROCESSING_WORKER_ENABLED", False)]
        for p in cls.patches:
            p.start()
        cls.work = Path(cls.tmp.name)
        cls.base = make_mp3(cls.work, 2, artist="Tag Band", title="Tag Titel")
        cls.created: list[str] = []
        cls.app, cls.client = app, TestClient(app)
        cls.tag = uuid.uuid4().hex[:6]
        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine, expire_on_commit=False)
        cls.sess = cls.Session()
        cls.users = {}
        for name, role in (("stud", "STUDENT"), ("support", "SUPPORT"), ("admin", "ADMIN")):
            u = User(email=f"bulk-{name}-{cls.tag}@test.local", username=f"bulk_{name}_{cls.tag}", password_hash="x", is_active=True, is_verified=True,
                     is_superuser=False, role=role, is_banned=False, preferred_language="uz")
            cls.sess.add(u)
            cls.users[name] = u
        cls.sess.commit()

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete

        from app.api.dependencies.auth import get_current_user
        from app.models.audit_log import AuditLog
        from app.models.medien import Song
        from app.models.user import User

        cls.app.dependency_overrides.pop(get_current_user, None)
        ids = [u.id for u in cls.users.values()]
        s = cls.sess
        s.rollback()
        s.execute(delete(Song).where(Song.title.like(f"T{cls.tag}%")))
        if cls.created:
            s.execute(delete(Song).where(Song.id.in_([uuid.UUID(i) for i in cls.created])))
        s.execute(delete(AuditLog).where(AuditLog.actor_id.in_([str(i) for i in ids])))
        s.execute(delete(User).where(User.id.in_(ids)))
        s.commit()
        s.close()
        for p in reversed(cls.patches):
            p.stop()
        cls.tmp.cleanup()
        cls.engine.dispose()

    # ---------- helpers ----------
    def api(self, method, url, who, expect=200, **kw):
        from app.api.dependencies.auth import get_current_user

        if who is None:
            self.app.dependency_overrides.pop(get_current_user, None)
        else:
            self.app.dependency_overrides[get_current_user] = lambda: self.users[who]
        r = getattr(self.client, method)(f"/api/v1{url}", **kw)
        if expect is not None:
            self.assertEqual(r.status_code, expect, f"{method.upper()} {url} -> {r.status_code} {r.text[:300]}")
        return r

    def upload(self, data: bytes, name: str, title: str | None = None, expect=200, **fields):
        form = {"title": title or f"T{self.tag} {name}", "status": "PUBLISHED", **{k: str(v).lower() if isinstance(v, bool) else v for k, v in fields.items()}}
        r = self.api("post", "/admin/medien/songs", "admin", expect=expect, data=form, files={"file": (name, data, "audio/mpeg")})
        if r.status_code == 200:
            self.created.append(r.json()["id"])
        return r

    def stored_files(self) -> int:
        folder = self.root / "songs"
        return len(list(folder.iterdir())) if folder.is_dir() else 0

    def run_queue(self, limit=1000):
        from app.services.medien import song_processing

        n = 0
        with self.Session() as db:
            while n < limit and song_processing.run_one(db):
                n += 1
        return n

    # ---------- tests ----------
    def test_1_permissions(self):
        for method, url, body in (("post", "/admin/medien/songs/duplicates", {"sha256": []}), ("post", "/admin/medien/songs/states", {"ids": []}),
                                  ("get", "/admin/medien/songs/processing", None)):
            kw = {"json": body} if body is not None else {}
            self.api(method, url, None, expect=401, **kw)
            self.api(method, url, "stud", expect=403, **kw)
        self.api("post", "/admin/medien/songs/duplicates", "support", expect=403, json={"sha256": []})  # only a content editor uploads
        self.api("post", "/admin/medien/songs/states", "support", json={"ids": []})
        self.api("post", "/admin/medien/songs/duplicates", "admin", expect=422, json={"sha256": ["a" * 64] * 501})
        self.api("post", "/admin/medien/songs", "stud", expect=403, data={"title": "x"}, files={"file": ("x.mp3", self.base, "audio/mpeg")})

    def test_2_complete_files_only_and_duplicates(self):
        data = self.base + self.tag.encode() + b"\x00unique-2"
        before = self.stored_files()
        # a hash that does not match the stored bytes: the file did not arrive complete → nothing stays
        r = self.upload(data, "kaputt.mp3", expect=400, sha256=sha(data + b"x"))
        self.assertIn("CHECKSUM_MISMATCH", r.json()["message"])
        self.assertEqual(self.stored_files(), before)
        first = self.upload(data, "lied.mp3", sha256=sha(data)).json()
        self.assertEqual(self.stored_files(), before + 1)
        # the same file again (another name): refused with the existing song, no second file
        r = self.upload(data, "lied-kopie.mp3", expect=409, sha256=sha(data))
        self.assertIn(f"SONG_DUPLICATE: {first['id']}", r.json()["message"])
        self.assertEqual(self.stored_files(), before + 1)
        # … unless the admin wants a copy
        self.upload(data, "lied-kopie.mp3", sha256=sha(data), allow_duplicate=True)
        self.assertEqual(self.stored_files(), before + 2)
        # the same NAME with other content is not a duplicate
        other = self.base + self.tag.encode() + b"\x00unique-2b"
        self.upload(other, "lied.mp3", sha256=sha(other))
        # the pre-check
        found = self.api("post", "/admin/medien/songs/duplicates", "admin", json={"sha256": [sha(data), sha(other), "f" * 64, "not-a-hash"]}).json()["existing"]
        self.assertEqual(set(found), {sha(data), sha(other)})
        self.assertEqual(found[sha(data)]["id"], first["id"])  # the oldest one

    def test_3_two_parallel_uploads_of_one_file_store_it_once(self):
        data = self.base + self.tag.encode() + b"\x00unique-3"

        def send(i):
            return self.client.post("/api/v1/admin/medien/songs", data={"title": f"T{self.tag} parallel {i}", "sha256": sha(data)},
                                    files={"file": (f"p{i}.mp3", data, "audio/mpeg")}).status_code

        from app.api.dependencies.auth import get_current_user

        self.app.dependency_overrides[get_current_user] = lambda: self.users["admin"]
        with ThreadPoolExecutor(max_workers=4) as pool:
            codes = sorted(pool.map(send, range(4)))
        self.assertEqual(codes, [200, 409, 409, 409])
        found = self.api("post", "/admin/medien/songs/duplicates", "admin", json={"sha256": [sha(data)]}).json()["existing"]
        self.assertEqual(len(found), 1)

    def test_4_metadata_queue(self):
        data = self.base + self.tag.encode() + b"\x00unique-4"
        song = self.upload(data, "Tag Titel.mp3", title="Tag Titel", sha256=sha(data), defer_metadata=True).json()
        self.assertEqual((song["metadata_status"], song["duration_ms"], song["audio_format"]), ("PENDING", None, "mp3"))
        # not audio but starts like an MP3: accepted by the content check, refused by the reader in the queue
        fake = b"ID3" + os.urandom(4000)
        broken = self.upload(fake, "broken.mp3", sha256=sha(fake), defer_metadata=True).json()
        # not even the first bytes of audio: refused at once, as before
        self.upload(b"das ist keine audiodatei", "text.mp3", expect=400, defer_metadata=True)
        self.assertEqual(self.api("get", "/admin/medien/songs/processing", "admin").json()["pending"], 2)
        self.assertEqual(self.run_queue(), 2)  # the broken one does not stop the other
        states = {s["id"]: s for s in self.api("post", "/admin/medien/songs/states", "admin", json={"ids": [song["id"], broken["id"]]}).json()}
        ok, bad = states[song["id"]], states[broken["id"]]
        self.assertEqual(ok["metadata_status"], "OK")
        self.assertGreater(ok["duration_ms"], 1500)
        self.assertEqual(ok["artist"], "Tag Band")  # the tag filled what the admin left empty
        self.assertEqual((bad["metadata_status"], bad["status"]), ("INVALID", "DRAFT"))  # never shown to students
        self.assertEqual(self.api("get", "/admin/medien/songs/processing", "admin").json(), {"pending": 0, "processing": 0})

    def test_5_hash_script_for_older_songs(self):
        from sqlalchemy import update

        from app.models.medien import Song
        from app.scripts import medien_song_hashes as script

        data = self.base + self.tag.encode() + b"\x00unique-5"
        song = self.upload(data, "alt.mp3", sha256=sha(data)).json()
        with self.Session() as db:
            db.execute(update(Song).where(Song.id == song["id"]).values(sha256=None))
            db.commit()
            plan = script.build_plan(db)
            self.assertIn(song["id"], [i["id"] for i in plan["items"]])
            with self.assertRaises(SystemExit):
                script.apply_plan(db, "000000000000")
            out = script.apply_plan(db, plan["plan_id"])
            self.assertGreaterEqual(out["hashed"], 1)
            self.assertEqual(db.get(Song, uuid.UUID(song["id"])).sha256, sha(data))
            self.assertNotIn(song["id"], [i["id"] for i in script.build_plan(db)["items"]])

    @unittest.skipUnless(os.environ.get("VIZU_STRESS_500") == "1", "stress test: set VIZU_STRESS_500=1")
    def test_6_stress_500_files(self):
        from app.api.dependencies.auth import get_current_user

        self.app.dependency_overrides[get_current_user] = lambda: self.users["admin"]
        files = [self.base + self.tag.encode() + b"\x00stress-" + str(i).encode() for i in range(500)]
        before = self.stored_files()

        def send(i):
            r = self.client.post("/api/v1/admin/medien/songs", data={"title": f"T{self.tag} stress {i:03d}", "sha256": sha(files[i]), "defer_metadata": "true"},
                                 files={"file": (f"stress-{i:03d}.mp3", files[i], "audio/mpeg")})
            return r.status_code, r.text[:200]

        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(send, range(500)))
        upload_s = time.perf_counter() - started
        codes = [code for code, _ in results]
        self.assertEqual(codes.count(200), 500, f"not all stored: {[r for r in results if r[0] != 200][:5]}")
        self.assertEqual(self.stored_files(), before + 500)
        started = time.perf_counter()
        processed = self.run_queue(limit=600)
        queue_s = time.perf_counter() - started
        self.assertGreaterEqual(processed, 500)
        found = self.api("post", "/admin/medien/songs/duplicates", "admin", json={"sha256": [sha(f) for f in files]}).json()["existing"]
        self.assertEqual(len(found), 500)  # each file exactly once
        print(f"\nSTRESS 500: uploads {upload_s:.1f} s (6 parallel), metadata queue {queue_s:.1f} s, {self.stored_files() - before} files stored")


if __name__ == "__main__":
    unittest.main()
