"""Medienwelt film player — backend: subtitle upload / check / preview / re-assign / delete (de, uz, en), sanitising, cue lists with
signed tokens and purchase checks, player settings + per-film state, previous / next film, additional video qualities
(chunked upload, Range, access), dictionary look-up of clicked subtitle words.

Integration test on a throwaway database: VIZU_WB_TEST_DB_URL (+ DATABASE_NAME) and ffmpeg (FFMPEG_BIN), like test_medien.py."""

import os
import random
import shutil
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
FFMPEG = shutil.which(os.environ.get("FFMPEG_BIN", "ffmpeg"))
CS = 1_500
SRT_DE = "1\n00:00:00,500 --> 00:00:01,500\nIch lerne jeden Tag Grüße, Köln\n\n2\n00:00:01,600 --> 00:00:02,000\nTschüss\n".encode("cp1252")
SRT_EN = b"1\n00:00:00,500 --> 00:00:01,500\nI learn German every day\n\n2\n00:00:01,600 --> 00:00:02,000\nBye\n"
VTT_UZ = "WEBVTT\n\n00:00.500 --> 00:01.500\nMen har kuni nemis tilini o'rganaman\n\n00:01.600 --> 00:02.000\nXayr\n".encode("utf-8")
SRT_EVIL = b"1\n00:00:00,500 --> 00:00:01,500\n<script>alert(1)</script><i>Hallo</i> &lt;b&gt;Welt\n"
SRT_LONG = b"1\n00:04:50,000 --> 00:05:00,000\nViel zu spaet\n"


def make_video(directory: Path) -> bytes:
    path = directory / "v.mp4"
    subprocess.run([FFMPEG, "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=duration=2:size=160x120:rate=10", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", str(path)], check=True)
    return path.read_bytes()


@unittest.skipUnless(DB_URL and FFMPEG, "integration test: set VIZU_WB_TEST_DB_URL (+ DATABASE_NAME) and have ffmpeg (FFMPEG_BIN)")
class TestMedienPlayer(unittest.TestCase):
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
        cls.mp4 = make_video(Path(cls.tmp.name))
        cls.app, cls.client = app, TestClient(app)
        cls.tag = uuid.uuid4().hex[:6]
        cls.engine = create_engine(DB_URL)
        cls.sess = sessionmaker(bind=cls.engine, expire_on_commit=False)()
        cls.users, cls.entries = {}, []
        for name, role in (("a", "STUDENT"), ("b", "STUDENT"), ("admin", "ADMIN"), ("super", "SUPER_ADMIN")):
            u = User(email=f"plr-{name}-{cls.tag}@test.local", username=f"plr_{name}_{cls.tag}", password_hash="x", is_active=True, is_verified=True,
                     is_superuser=role == "SUPER_ADMIN", role=role, is_banned=False, preferred_language="uz")
            cls.sess.add(u)
            cls.users[name] = u
        cls.sess.commit()

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete

        from app.api.dependencies.auth import get_current_user
        from app.models.audit_log import AuditLog
        from app.models.dictionary import DictionaryEntry
        from app.models.medien import Film, MediaCategory, MediaPlayerPrefs, MediaProgress, MediaPurchase
        from app.models.user import User

        cls.app.dependency_overrides.pop(get_current_user, None)
        ids = [u.id for u in cls.users.values()]
        s = cls.sess
        s.rollback()
        s.execute(delete(MediaPurchase).where(MediaPurchase.user_id.in_(ids)))
        s.execute(delete(MediaProgress).where(MediaProgress.user_id.in_(ids)))
        s.execute(delete(MediaPlayerPrefs).where(MediaPlayerPrefs.user_id.in_(ids)))
        s.execute(delete(Film).where(Film.title.like(f"T{cls.tag}%")))
        s.execute(delete(MediaCategory).where(MediaCategory.name.like(f"T{cls.tag}%")))
        if cls.entries:
            s.execute(delete(DictionaryEntry).where(DictionaryEntry.id.in_(cls.entries)))
        s.execute(delete(AuditLog).where(AuditLog.actor_id.in_([str(i) for i in ids])))
        s.execute(delete(User).where(User.id.in_(ids)))
        s.commit()
        s.close()
        cls.patch.stop()
        cls.tmp.cleanup()
        cls.engine.dispose()

    # ---------- helpers ----------
    def as_(self, who):
        from app.api.dependencies.auth import get_current_user

        if who is None:
            self.app.dependency_overrides.pop(get_current_user, None)
        else:
            self.app.dependency_overrides[get_current_user] = lambda: self.users[who]

    def api(self, method, url, who, expect=200, **kw):
        self.as_(who)
        r = getattr(self.client, method)(f"/api/v1{url}", **kw)
        if expect is not None:
            self.assertEqual(r.status_code, expect, f"{method.upper()} {url} -> {r.status_code} {r.text[:300]}")
        return r

    def title(self, name):
        return f"T{self.tag} {name}"

    def film(self, name, video=True, **extra):
        body = {"title": self.title(name), "level": "B1", "status": "PUBLISHED", "duration_minutes": 1, **extra}
        film = self.api("post", "/admin/medien/films", "admin", json=body).json()
        if video:
            film = self.api("post", f"/admin/medien/films/{film['id']}/video", "admin", files={"file": ("v.mp4", self.mp4, "video/mp4")}).json()
        return film

    def sub(self, fid, language, raw, name="s.srt", expect=200, **data):
        return self.api("post", f"/admin/medien/films/{fid}/subtitles", "admin", expect=expect, data={"language": language, **data},
                        files={"file": (name, raw, "text/plain")})

    def disk(self):
        root = Path(self.tmp.name) / "storage"
        return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} if root.exists() else set()

    def watch(self, fid, who="a"):
        return self.api("post", f"/medien/films/{fid}/watch", who).json()

    # ---------- subtitles: admin ----------
    def test_1_subtitles_de_uz_en_upload_checks_and_tools(self):
        film = self.film("Subs")
        fid = film["id"]
        self.assertTrue(1500 < film["video_duration_ms"] < 2600)  # the probed length of the 2 s test video
        de = self.sub(fid, "de", SRT_DE).json()["subtitles"][0]
        self.assertEqual((de["language"], de["label"], de["cue_count"], de["format"], de["last_ms"]), ("de", "Deutsch", 2, "srt", 2000))
        self.assertEqual([w["code"] for w in de["warnings"]], ["ENCODING_CONVERTED"])  # Windows-1252 file -> stored as UTF-8
        self.sub(fid, "uz", VTT_UZ, "uz.vtt", label="O'zbekcha")
        card = self.sub(fid, "en", SRT_EN).json()
        self.assertEqual([s["language"] for s in card["subtitles"]], ["de", "en", "uz"])
        self.assertEqual({s["language"]: s["cue_count"] for s in card["subtitles"]}, {"de": 2, "en": 2, "uz": 2})
        # refused: wrong extension, binary, empty, no cues, too large, unknown language, backwards times only
        for name, raw, code in (("s.ass", SRT_EN, 400), ("s.srt", b"\x00\x01\x02\x03binary", 400), ("s.srt", b"", 400), ("s.srt", b"no cues here", 400),
                                ("s.srt", b"1\n00:00:09,000 --> 00:00:01,000\nx\n", 400), ("s.srt", b"1\n00:00:00,000 --> 00:00:01,000\n" + b"x" * (2 * 1024 * 1024 + 5), 400)):
            r = self.sub(fid, "de", raw, name, expect=code)
            self.assertRegex(r.json()["message"], r"^[A-Z_]+")
        self.sub(fid, "xx", SRT_EN, expect=422)
        # the stored track is sanitised plain WebVTT, the student gets plain text
        self.sub(fid, "ru", SRT_EVIL)
        stored = next(p for p in self.disk() if p.startswith("subtitles/"))
        for p in self.disk():
            if p.startswith("subtitles/"):
                text = (Path(self.tmp.name) / "storage" / p).read_text("utf-8")
                self.assertTrue(text.startswith("WEBVTT\n\n"))
                self.assertNotIn("<script", text)
                self.assertNotIn("<i>", text)
        self.assertTrue(stored)
        ru = next(s for s in self.watch(fid)["subtitles"] if s["language"] == "ru")
        self.as_(None)
        self.assertEqual(self.client.get(ru["cues_url"]).json()["cues"], [[500, 1500, "alert(1)Hallo <b>Welt"]])
        # dry-run check stores nothing
        before = (self.disk(), len(self.api("get", "/admin/medien/films", "admin").json()["items"][0]["subtitles"]))
        rep = self.api("post", f"/admin/medien/films/{fid}/subtitles/check", "admin", files={"file": ("x.srt", SRT_LONG, "text/plain")}).json()
        self.assertEqual(rep["report"]["cue_count"], 1)
        self.assertIn("BEYOND_VIDEO", [w["code"] for w in rep["report"]["warnings"]])
        self.assertEqual(rep["preview"], [[290000, 300000, "Viel zu spaet"]])
        self.assertEqual((self.disk(), len(self.api("get", "/admin/medien/films", "admin").json()["items"][0]["subtitles"])), before)
        self.api("post", f"/admin/medien/films/{fid}/subtitles/check", "admin", expect=400, files={"file": ("x.srt", b"nonsense", "text/plain")})
        # a subtitle that does not fit the video is still saved, with the warning kept
        warned = self.sub(fid, "en", SRT_LONG).json()
        en = next(s for s in warned["subtitles"] if s["language"] == "en")
        self.assertIn("BEYOND_VIDEO", [w["code"] for w in en["warnings"]])
        self.assertEqual(len(warned["subtitles"]), 4)  # replaced, not added
        files_before = {p for p in self.disk() if p.startswith("subtitles/")}
        self.sub(fid, "en", SRT_EN)
        self.assertEqual(len({p for p in self.disk() if p.startswith("subtitles/")}), len(files_before))  # the replaced file is gone
        # preview, re-check, re-assign, rename
        sid = next(s["id"] for s in self.api("get", "/admin/medien/films", "admin").json()["items"][0]["subtitles"] if s["language"] == "uz")
        prev = self.api("get", f"/admin/medien/films/{fid}/subtitles/{sid}", "admin").json()
        self.assertEqual((prev["language"], prev["cues"][0], prev["report"]["cue_count"]), ("uz", [500, 1500, "Men har kuni nemis tilini o'rganaman"], 2))
        from app.models.medien import FilmSubtitle

        row = self.sess.get(FilmSubtitle, uuid.UUID(sid))
        row.cue_count, row.warnings = 0, []  # an "old" row from before the checks existed
        self.sess.commit()
        again = self.api("post", f"/admin/medien/films/{fid}/subtitles/{sid}/check", "admin").json()
        self.assertEqual(next(s["cue_count"] for s in again["subtitles"] if s["id"] == sid), 2)
        self.api("put", f"/admin/medien/films/{fid}/subtitles/{sid}", "admin", expect=409, json={"language": "de"})  # taken
        moved = self.api("put", f"/admin/medien/films/{fid}/subtitles/{sid}", "admin", json={"label": "O'zbek (tarjima)"}).json()
        self.assertEqual(next(s["label"] for s in moved["subtitles"] if s["id"] == sid), "O'zbek (tarjima)")
        self.api("put", f"/admin/medien/films/{fid}/subtitles/{sid}", "admin", expect=422, json={"language": "klingon"})
        ru_id = next(s["id"] for s in moved["subtitles"] if s["language"] == "ru")
        self.api("put", f"/admin/medien/films/{fid}/subtitles/{ru_id}", "admin", json={"label": "RU"})
        self.api("delete", f"/admin/medien/films/{fid}/subtitles/{ru_id}", "admin")
        self.api("delete", f"/admin/medien/films/{fid}/subtitles/{uuid.uuid4()}", "admin", expect=404)
        # rights: students and anonymous users cannot use the tools
        for method, url in (("post", f"/admin/medien/films/{fid}/subtitles/check"), ("get", f"/admin/medien/films/{fid}/subtitles/{sid}"),
                            ("post", f"/admin/medien/films/{fid}/subtitles/{sid}/check"), ("put", f"/admin/medien/films/{fid}/subtitles/{sid}"),
                            ("delete", f"/admin/medien/films/{fid}/subtitles/{sid}"), ("delete", f"/admin/medien/films/{fid}/renditions/{uuid.uuid4()}")):
            self.as_(None)
            self.assertEqual(getattr(self.client, method)(f"/api/v1{url}").status_code, 401, url)
            self.assertEqual(self.api(method, url, "a", expect=None, **({"json": {}} if method == "put" else {})).status_code, 403, url)
        self.api("delete", f"/admin/medien/films/{fid}", "admin", expect=204)
        self.assertFalse([p for p in self.disk() if p.startswith(("subtitles/", "films/"))])

    # ---------- subtitles + video: student side and access ----------
    def test_2_student_cues_tokens_and_paid_access(self):
        film = self.film("Paid Subs", access_type="PAID", price=90000)
        fid = film["id"]
        self.sub(fid, "de", SRT_DE)
        self.api("post", f"/medien/films/{fid}/watch", "a", expect=403)
        req = self.api("post", "/medien/purchases", "a", json={"kind": "FILM", "content_id": fid}).json()
        self.api("post", f"/medien/films/{fid}/watch", "a", expect=403)  # a request gives no access
        self.api("post", f"/admin/medien/purchases/{req['id']}/decision", "super", json={"status": "GRANTED"})
        w = self.watch(fid)
        self.assertEqual([s["language"] for s in w["subtitles"]], ["de"])
        self.assertEqual(w["sources"], [{"id": "main", "label": "Original", "height": None, "url": w["source"]["url"]}])
        self.assertEqual((set(w["neighbors"]), w["prefs"]["size"], w["progress"]), ({"prev", "next"}, "medium", None))
        track = w["subtitles"][0]
        self.as_(None)
        cues = self.client.get(track["cues_url"])
        self.assertEqual((cues.status_code, cues.headers["cache-control"]), (200, "private, no-store"))
        self.assertEqual(cues.json(), {"language": "de", "label": "Deutsch", "cues": [[500, 1500, "Ich lerne jeden Tag Grüße, Köln"], [1600, 2000, "Tschüss"]]})
        self.assertNotIn("file_key", cues.text)
        self.assertEqual(self.client.get(track["url"]).status_code, 200)  # the WebVTT file keeps working
        # tokens: none / garbage / the video's token / another film's token
        base = track["cues_url"].split("?")[0]
        self.assertEqual(self.client.get(base).status_code, 422)
        self.assertEqual(self.client.get(f"{base}?token=garbage").status_code, 401)
        self.assertEqual(self.client.get(f"{base}?token={w['source']['url'].split('token=')[1]}").status_code, 403)
        other = self.film("Other Subs")
        self.sub(other["id"], "de", SRT_EN)
        other_track = self.watch(other["id"])["subtitles"][0]
        self.assertEqual(self.client.get(f"{base}?token={other_track['cues_url'].split('token=')[1]}").status_code, 403)
        # another student has no access; revoking closes the OLD signed urls (checked per request)
        self.api("post", f"/medien/films/{fid}/watch", "b", expect=403)
        self.api("post", f"/admin/medien/purchases/{req['id']}/decision", "super", json={"status": "REVOKED"})
        self.as_(None)
        for url in (track["cues_url"], track["url"], w["source"]["url"]):
            self.assertEqual(self.client.get(url).status_code, 403, url)
        # a hidden film is closed for students even with a token that was issued earlier
        self.api("put", f"/admin/medien/films/{other['id']}", "admin", json={"status": "HIDDEN"})
        self.as_(None)
        self.assertEqual(self.client.get(other_track["cues_url"]).status_code, 404)
        for f in (fid, other["id"]):
            self.api("delete", f"/admin/medien/films/{f}", "admin", expect=204)

    # ---------- settings and per-film state ----------
    def test_3_player_prefs_and_state(self):
        self.api("get", "/medien/player-prefs", None, expect=401)
        default = self.api("get", "/medien/player-prefs", "a").json()
        self.assertEqual(default, {"enabled": True, "size": "medium", "color": "#ffffff", "bg_opacity": 75, "position": "bottom", "font": "sans",
                                   "dual": False, "secondary": "uz"})
        full = {"enabled": False, "size": "large", "color": "#ffe066", "bg_opacity": 40, "position": "higher", "font": "serif", "dual": True, "secondary": "en"}
        self.assertEqual(self.api("put", "/medien/player-prefs", "a", json=full).json(), full)
        self.assertEqual(self.api("put", "/medien/player-prefs", "a", json={"size": "small"}).json(), {**full, "size": "small"})  # partial update merges
        self.assertEqual(self.api("get", "/medien/player-prefs", "a").json()["size"], "small")
        self.assertEqual(self.api("get", "/medien/player-prefs", "b").json(), default)  # per user
        for bad in ({"size": "huge"}, {"color": "#123456"}, {"bg_opacity": 101}, {"bg_opacity": -1}, {"position": "top"}, {"font": "comic"},
                    {"secondary": "xx"}, {"enabled": "yes"}, {"unknown": 1}, {"color": "red; background:url(x)"}):
            self.api("put", "/medien/player-prefs", "a", expect=422, json=bad)
        self.assertEqual(self.api("get", "/medien/player-prefs", "a").json()["size"], "small")
        # state of one film comes back with the watch info
        film = self.film("State")
        fid = film["id"]
        state = {"subtitle": "de", "dual": True, "secondary": "uz", "speed": 1.5, "quality": "720p"}
        saved = self.api("put", f"/medien/progress/FILM/{fid}", "a", json={"position": 1, "total": 2, "state": state}).json()
        self.assertEqual(saved["state"], {**state, "speed": 1.5})
        self.assertEqual(self.watch(fid)["progress"]["state"], saved["state"])
        merged = self.api("put", f"/medien/progress/FILM/{fid}", "a", json={"position": 1, "total": 2, "state": {"speed": 0.75}}).json()
        self.assertEqual(merged["state"], {**state, "speed": 0.75})  # only the sent keys change
        # values that are not menu values are dropped, not stored
        cleaned = self.api("put", f"/medien/progress/FILM/{fid}", "a", json={"position": 1, "total": 2, "state": {"speed": 3.3, "quality": "<b>x</b>", "audio": "de"}}).json()
        self.assertEqual(cleaned["state"], {**state, "speed": 0.75, "audio": "de"})
        for bad in ({"subtitle": "xx"}, {"secondary": "off"}, {"speed": 9}, {"quality": "x" * 30}, {"dual": "yes"}, {"other": 1}):
            self.api("put", f"/medien/progress/FILM/{fid}", "a", expect=422, json={"position": 1, "total": 2, "state": bad})
        self.assertIsNone(self.watch(fid, "b")["progress"])  # per user
        self.api("delete", f"/admin/medien/films/{fid}", "admin", expect=204)

    # ---------- previous / next ----------
    def test_4_previous_and_next_film(self):
        cat = self.api("post", "/admin/medien/categories", "admin", json={"kind": "FILM", "name": self.title("Serie")}).json()
        ids = []
        for n in (1, 2, 3):
            f = self.film(f"Folge {n}", video=False, category_id=cat["id"])
            self.api("put", f"/admin/medien/films/{f['id']}/external-url", "admin", json={"url": f"https://video.example.org/{n}.mp4"})
            ids.append(f["id"])
        hidden = self.film("Folge hidden", video=False, category_id=cat["id"], status="HIDDEN")
        other = self.film("Folge ohne Serie", video=False)
        self.api("put", f"/admin/medien/films/{other['id']}/external-url", "admin", json={"url": "https://video.example.org/o.mp4"})
        order = [x["id"] for x in self.api("get", f"/medien/films?category={cat['slug']}", "a").json()["items"]]  # newest first
        self.assertEqual(order, ids[::-1])
        nb = lambda fid: self.watch(fid)["neighbors"]  # noqa: E731
        self.assertEqual((nb(order[0])["prev"], nb(order[0])["next"]["id"]), (None, order[1]))
        mid = nb(order[1])
        self.assertEqual((mid["prev"]["id"], mid["next"]["id"], mid["next"]["title"]), (order[0], order[2], self.title("Folge 1")))
        self.assertEqual((nb(order[2])["prev"]["id"], nb(order[2])["next"]), (order[1], None))
        self.assertIsNone(nb(other["id"])["prev"])  # a film without a category is compared with all published films: this one is the newest
        self.assertNotIn(hidden["id"], str(mid))
        for f in (*ids, hidden["id"], other["id"]):
            self.api("delete", f"/admin/medien/films/{f}", "admin", expect=204)
        self.api("delete", f"/admin/medien/categories/{cat['id']}", "admin", expect=204)

    # ---------- additional video qualities ----------
    def test_5_renditions_upload_stream_replace_delete(self):
        from app.services.medien import admin as svc

        empty = self.film("Ohne Video", video=False)
        self.api("post", f"/admin/medien/films/{empty['id']}/video/init", "admin", expect=409, json={"filename": "v.mp4", "size": 100, "quality": "720p"})
        film = self.film("Qualitaeten", access_type="PAID", price=50000)
        fid = film["id"]
        start = self.disk()
        for bad in ("big", "50p", "99999p", "720", "720p;rm"):
            self.api("post", f"/admin/medien/films/{fid}/video/init", "admin", expect=422, json={"filename": "v.mp4", "size": 100, "quality": bad})

        def upload(label):
            with patch.object(svc, "CHUNK_SIZE", CS):
                init = self.api("post", f"/admin/medien/films/{fid}/video/init", "admin", json={"filename": f"{label}.mp4", "size": len(self.mp4), "quality": label}).json()
                state = next(f for f in self.api("get", "/admin/medien/films", "admin").json()["items"] if f["id"] == fid)["processing_status"]
                self.assertEqual(state, "READY")  # the film keeps playing while a quality is uploaded
                for i in range(init["chunks"]):
                    self.api("put", f"/admin/medien/films/{fid}/video/{init['upload_id']}/{i}", "admin", content=self.mp4[i * CS:(i + 1) * CS])
                return self.api("post", f"/admin/medien/films/{fid}/video/{init['upload_id']}/complete", "admin").json()

        card = upload("720p")
        self.assertEqual((card["processing_status"], [(r["label"], r["height"], r["file_status"]) for r in card["renditions"]]), ("READY", [("720p", 720, "ok")]))
        card = upload("360p")
        self.assertEqual([r["label"] for r in card["renditions"]], ["720p", "360p"])  # high to low
        with_two = self.disk()
        replaced = upload("720p")  # the same label replaces the file
        self.assertEqual(len(replaced["renditions"]), 2)
        self.assertEqual(len(self.disk()), len(with_two))
        # PAID: closed without a purchase, open with one; Range works for every quality; tokens are not interchangeable
        self.api("post", f"/medien/films/{fid}/watch", "a", expect=403)
        self.api("post", "/admin/medien/purchases/grant", "super", json={"kind": "FILM", "content_id": fid, "email": self.users["a"].email})
        w = self.watch(fid)
        self.assertEqual([(s["id"] == "main", s["label"]) for s in w["sources"]], [(True, "Original"), (False, "720p"), (False, "360p")])
        self.as_(None)
        for s in w["sources"]:
            r = self.client.get(s["url"], headers={"Range": "bytes=0-511"})
            self.assertEqual((r.status_code, len(r.content), r.headers["content-type"]), (206, 512, "video/mp4"), s["label"])
        rendition_base = w["sources"][1]["url"].split("?")[0]
        self.assertEqual(self.client.get(rendition_base).status_code, 422)
        self.assertEqual(self.client.get(f"{rendition_base}?token={w['source']['url'].split('token=')[1]}").status_code, 403)  # the main video's token
        self.assertEqual(self.client.get(f"{rendition_base}?token={w['sources'][2]['url'].split('token=')[1]}").status_code, 403)  # another rendition's token
        # revoking closes the old rendition URL too
        from app.models.medien import MediaPurchase
        from sqlalchemy import update

        self.sess.execute(update(MediaPurchase).where(MediaPurchase.content_id == uuid.UUID(fid)).values(status="REVOKED"))
        self.sess.commit()
        self.as_(None)
        self.assertEqual(self.client.get(w["sources"][1]["url"]).status_code, 403)
        # delete one quality (file goes), the film (everything goes)
        rid = next(r["id"] for r in card["renditions"] if r["label"] == "360p")
        left = self.api("delete", f"/admin/medien/films/{fid}/renditions/{rid}", "admin").json()
        self.assertEqual([r["label"] for r in left["renditions"]], ["720p"])
        self.api("delete", f"/admin/medien/films/{fid}/renditions/{rid}", "admin", expect=404)
        self.api("delete", f"/admin/medien/films/{fid}", "admin", expect=204)
        self.api("delete", f"/admin/medien/films/{empty['id']}", "admin", expect=204)
        self.assertEqual(self.disk(), start - {p for p in start if p.startswith("films/")})

    # ---------- dictionary look-up ----------
    def test_6_lookup_of_clicked_words(self):
        from app.models.dictionary import DictionaryEntry
        from app.scripts.woerterbuch.source import canonical_uz, search_key

        sid = random.randint(800_000, 899_000)
        entries = {}
        for i, (lemma, article, kind, uz, forms, example) in enumerate((("Zqxhund", "der", "Nomen", "zqxit", ["zqxhunde", "zqxhundes"], "Der Zqxhund schläft."),
                                                                        ("zqxlernen", None, "Verb", "zqxo'rganmoq", ["zqxlerne", "zqxlernst", "zqxlernt"], "Ich zqxlerne Deutsch."))):
            e = DictionaryEntry(level="C1", source_id=sid + i, lemma=lemma, word_type=kind, article=article, translation=uz, status="verified",
                                group_key=f"t{self.tag}-{lemma}", search_de=search_key(lemma), search_uz="|" + search_key(canonical_uz(uz)) + "|",
                                search_forms="|" + "|".join(search_key(f) for f in forms) + "|", content_hash="x", example_de=example, example_uz="Misol.")
            self.sess.add(e)
            entries[lemma] = e
        self.sess.commit()
        self.entries += [e.id for e in entries.values()]
        look = lambda w: self.api("get", f"/medien/lookup?word={w}", "a").json()  # noqa: E731
        hund = look("Zqxhund")
        self.assertEqual((hund["status"], hund["word"]), ("exact", "Zqxhund"))
        card = hund["entries"][0]
        self.assertEqual((card["lemma"], card["article"], card["word_type"], card["translation"], card["example_de"], card["saved"]),
                         ("Zqxhund", "der", "Nomen", "zqxit", "Der Zqxhund schläft.", False))
        self.assertEqual(look("zqxhund,")["status"], "exact")          # punctuation / case do not matter
        self.assertEqual(look("%22Zqxhund!%22")["entries"][0]["lemma"], "Zqxhund")
        form = look("zqxlerne")
        self.assertEqual((form["status"], form["entries"][0]["lemma"]), ("form", "zqxlernen"))  # an inflected form -> its headword, flagged as a form
        similar = look("Zqxhu")
        self.assertEqual((similar["status"], similar["entries"]), ("similar", []))  # only suggestions, never a translation
        self.assertIn("Zqxhund", [s["lemma"] for s in similar["suggestions"]])
        none = look("Zxqvw")
        self.assertEqual((none["status"], none["entries"], none["suggestions"]), ("none", [], []))
        self.assertEqual(look("%25")["status"], "none")             # LIKE wildcards are escaped
        self.assertEqual(look("....")["word"], "")                  # nothing left after cleaning
        self.api("get", "/medien/lookup", "a", expect=422)
        self.api("get", f"/medien/lookup?word={'x' * 81}", "a", expect=422)
        self.api("get", "/medien/lookup?word=Hund", None, expect=401)
        # saving uses the Wörterbuch's own star: the answer shows it afterwards
        self.api("put", f"/dictionary/entries/{card['id']}/saved", "a", json={"saved": True})
        self.assertTrue(look("Zqxhund")["entries"][0]["saved"])
        self.assertFalse(self.api("get", "/medien/lookup?word=Zqxhund", "b").json()["entries"][0]["saved"])  # per student
        from sqlalchemy import delete

        from app.models.dictionary import DictionaryUserWord

        self.sess.execute(delete(DictionaryUserWord).where(DictionaryUserWord.entry_id.in_(self.entries)))
        self.sess.commit()

    def test_7_new_routes_need_a_login(self):
        self.as_(None)
        for method, url in (("get", "/medien/player-prefs"), ("put", "/medien/player-prefs"), ("get", "/medien/lookup?word=a")):
            self.assertEqual(getattr(self.client, method)(f"/api/v1{url}").status_code, 401, url)


if __name__ == "__main__":
    unittest.main()
