"""AI subtitle jobs of Medienwelt films — integration (VIZU_WB_TEST_DB_URL + ffmpeg, the test provider of subtitle_ai):
start checks (service not set up, no video, existing track, second running job), permissions (401 / 403 for every new route), the real ffmpeg
part (pauses, pieces, audio pieces), TRANSCRIBE → DRAFT track → follow-up TRANSLATE jobs, drafts invisible to students (list, cue list, an old
token), approve / withdraw, the admin's cue edits, SRT / VTT download, retry continues with the missing pieces, cancel, auto-detected language
that is not supported or already has a track (stops after the first piece), an upload replacing an AI draft is approved at once."""

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
SRT_DE = b"1\n00:00:00,500 --> 00:00:01,500\nHallo\n"


def make_video(directory: Path) -> bytes:
    """20 s: a tone of 2.5 s every 4 s (= "speech" with pauses in between) under a test picture."""
    path = directory / "talk.mp4"
    subprocess.run([FFMPEG, "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=duration=20:size=160x120:rate=5",
                    "-f", "lavfi", "-i", "aevalsrc='if(lt(mod(t,4),2.5),0.4*sin(2*PI*440*t),0)':s=16000:d=20",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path)], check=True)
    return path.read_bytes()


@unittest.skipUnless(DB_URL and FFMPEG, "integration test: set VIZU_WB_TEST_DB_URL (+ DATABASE_NAME) and have ffmpeg (FFMPEG_BIN)")
class TestSubtitleJobs(unittest.TestCase):
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
        cls.patches = [patch.object(ProtectedMedienStorage, "ROOT", Path(cls.tmp.name) / "storage"),
                       patch.object(settings, "SUBTITLE_WORKER_ENABLED", False), patch.object(settings, "APP_ENV", "test"),
                       patch.object(settings, "SUBTITLE_STT_PROVIDER", "fake"), patch.object(settings, "SUBTITLE_TRANSLATE_PROVIDER", "fake"),
                       patch.object(settings, "SUBTITLE_CHUNK_SECONDS", 8)]
        for p in cls.patches:
            p.start()
        cls.mp4 = make_video(Path(cls.tmp.name))
        cls.app, cls.client = app, TestClient(app)
        cls.tag = uuid.uuid4().hex[:6]
        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine, expire_on_commit=False)
        cls.sess = cls.Session()
        cls.users = {}
        for name, role in (("stud", "STUDENT"), ("support", "SUPPORT"), ("admin", "ADMIN")):
            u = User(email=f"sai-{name}-{cls.tag}@test.local", username=f"sai_{name}_{cls.tag}", password_hash="x", is_active=True, is_verified=True,
                     is_superuser=False, role=role, is_banned=False, preferred_language="uz")
            cls.sess.add(u)
            cls.users[name] = u
        cls.sess.commit()

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete

        from app.api.dependencies.auth import get_current_user
        from app.models.audit_log import AuditLog
        from app.models.medien import Film, MediaProgress
        from app.models.user import User

        cls.app.dependency_overrides.pop(get_current_user, None)
        ids = [u.id for u in cls.users.values()]
        s = cls.sess
        s.rollback()
        films = [f.id for f in s.query(Film).filter(Film.title.like(f"T{cls.tag}%"))]
        s.execute(delete(MediaProgress).where(MediaProgress.user_id.in_(ids)))
        s.execute(delete(Film).where(Film.title.like(f"T{cls.tag}%")))  # subtitles + jobs cascade
        s.execute(delete(AuditLog).where(AuditLog.actor_id.in_([str(i) for i in ids])))
        for fid in films:
            s.execute(delete(AuditLog).where(AuditLog.actor_id.is_(None), AuditLog.details.like(f"{fid}%")))
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

    def film(self, name, video=True):
        body = {"title": f"T{self.tag} {name}", "level": "B1", "status": "PUBLISHED", "duration_minutes": 1}
        film = self.api("post", "/admin/medien/films", "admin", json=body).json()
        if video:
            film = self.api("post", f"/admin/medien/films/{film['id']}/video", "admin", files={"file": ("v.mp4", self.mp4, "video/mp4")}).json()
        return film

    def run_jobs(self, limit=20):
        from app.services.medien import subtitle_jobs

        n = 0
        with self.Session() as db:
            while n < limit and subtitle_jobs.run_one(db):
                n += 1
        return n

    def jobs(self, fid):
        return self.api("get", f"/admin/medien/films/{fid}/subtitle-jobs", "admin").json()

    def tracks(self, fid):
        from app.models.medien import KIND_FILM, Film
        from app.services.medien import admin as svc

        with self.Session() as db:
            return {s["language"]: {**s, "id": str(s["id"])} for s in svc.admin_card(KIND_FILM, db.get(Film, uuid.UUID(fid)), db)["subtitles"]}

    def watch(self, fid):
        return self.api("post", f"/medien/films/{fid}/watch", "stud").json()

    # ---------- tests ----------
    def test_1_permissions(self):
        fid = self.film("perm", video=False)["id"]
        z = uuid.uuid4()
        routes = [("get", "/admin/medien/subtitle-ai/status", None), ("get", f"/admin/medien/films/{fid}", None),
                  ("post", f"/admin/medien/films/{fid}/subtitles/ai", {"language": "auto"}),
                  ("get", f"/admin/medien/films/{fid}/subtitle-jobs", None), ("post", f"/admin/medien/films/{fid}/subtitle-jobs/{z}/retry", None),
                  ("post", f"/admin/medien/films/{fid}/subtitle-jobs/{z}/cancel", None), ("post", f"/admin/medien/films/{fid}/subtitles/{z}/approve", {"approved": True}),
                  ("put", f"/admin/medien/films/{fid}/subtitles/{z}/cues", {"cues": []}), ("get", f"/admin/medien/films/{fid}/subtitles/{z}/download", None),
                  ("post", f"/admin/medien/films/{fid}/subtitles/{z}/translate", {"target": "uz"})]
        for method, url, body in routes:
            kw = {"json": body} if body is not None else {}
            self.api(method, url, None, expect=401, **kw)
            self.api(method, url, "stud", expect=403, **kw)
            if method != "get":  # SUPPORT may look, never change
                self.api(method, url, "support", expect=403, **kw)
        self.api("get", "/admin/medien/subtitle-ai/status", "support")
        self.assertEqual(self.api("get", f"/admin/medien/films/{fid}", "support").json()["id"], fid)
        self.api("post", f"/admin/medien/films/{fid}/subtitles/ai", "admin", expect=422, json={"language": "fr"})
        self.api("post", f"/admin/medien/films/{fid}/subtitles/ai", "admin", expect=422, json={"language": "de", "extra": 1})

    def test_2_start_checks(self):
        from app.core.config import settings

        no_video = self.film("novideo", video=False)["id"]
        r = self.api("post", f"/admin/medien/films/{no_video}/subtitles/ai", "admin", expect=409, json={"language": "auto"})
        self.assertIn("VIDEO_MISSING", r.json()["message"])
        fid = self.film("notconfigured")["id"]
        with patch.object(settings, "SUBTITLE_STT_PROVIDER", "gemini"), patch.object(settings, "GEMINI_API_KEY", ""):
            r = self.api("post", f"/admin/medien/films/{fid}/subtitles/ai", "admin", expect=409, json={"language": "auto"})
            self.assertIn("AI_NOT_CONFIGURED", r.json()["message"])
            status = self.api("get", "/admin/medien/subtitle-ai/status", "admin").json()
            self.assertFalse(status["speech_to_text"]["configured"])
            self.assertTrue(status["ffmpeg"])
        self.assertEqual(self.jobs(fid), [])  # nothing was queued
        self.api("post", f"/admin/medien/films/{fid}/subtitles/ai", "admin", expect=202, json={"language": "de"})
        r = self.api("post", f"/admin/medien/films/{fid}/subtitles/ai", "admin", expect=409, json={"language": "en"})
        self.assertIn("JOB_RUNNING", r.json()["message"])
        self.run_jobs()

    def test_3_transcribe_translate_review_flow(self):
        fid = self.film("flow")["id"]
        job = self.api("post", f"/admin/medien/films/{fid}/subtitles/ai", "admin", expect=202, json={"language": "auto", "translate_to": ["uz", "en"]}).json()
        self.assertEqual((job["status"], job["kind"], job["translate_to"]), ("PENDING", "TRANSCRIBE", ["uz", "en"]))
        self.assertEqual(self.run_jobs(), 3)  # transcription + two translations
        jobs = {j["kind"] + j["language"]: j for j in self.jobs(fid)}
        t = jobs["TRANSCRIBEauto"]
        self.assertEqual((t["status"], t["detected_language"], t["progress_done"], t["progress_total"]), ("COMPLETED", "de", 3, 3))
        self.assertEqual(t["stats"]["speakers_max_per_piece"], 2)
        self.assertEqual({jobs["TRANSLATEuz"]["status"], jobs["TRANSLATEen"]["status"]}, {"COMPLETED"})

        tracks = self.tracks(fid)
        self.assertEqual(set(tracks), {"de", "uz", "en"})
        de, uz = tracks["de"], tracks["uz"]
        self.assertEqual((de["status"], de["source"], uz["status"], uz["source"], uz["source_language"]), ("DRAFT", "AI", "DRAFT", "TRANSLATION", "de"))
        de_cues = self.api("get", f"/admin/medien/films/{fid}/subtitles/{de['id']}", "admin").json()["cues"]
        uz_cues = self.api("get", f"/admin/medien/films/{fid}/subtitles/{uz['id']}", "admin").json()["cues"]
        self.assertGreaterEqual(len(de_cues), 5)
        self.assertTrue(all(0 <= c[0] < c[1] <= 20_500 for c in de_cues))
        self.assertTrue(all(b[0] >= a[1] for a, b in zip(de_cues, de_cues[1:])))  # no overlap
        self.assertTrue(de_cues[0][2].startswith("Testsatz"))
        self.assertEqual([c[:2] for c in uz_cues], [c[:2] for c in de_cues])  # same times
        self.assertEqual(uz_cues[0][2], f"[uz] {de_cues[0][2]}")

        # drafts never reach a student: not listed, not readable even with a token
        from app.services.medien import common as c

        watch = self.watch(fid)
        self.assertEqual(watch["subtitles"], [])
        token_url = c.signed_url(f"/api/v1/medien/subtitles/{de['id']}/cues", de["id"], self.users["stud"], "subtitle")
        self.assertEqual(self.client.get(token_url).status_code, 404)

        # approve → visible, the transcript is the original language; withdraw → gone again
        for track in (de, uz):
            self.api("post", f"/admin/medien/films/{fid}/subtitles/{track['id']}/approve", "admin", json={"approved": True})
        watch = self.watch(fid)
        self.assertEqual({s["language"] for s in watch["subtitles"]}, {"de", "uz"})
        self.assertEqual(watch["original_language"], "de")
        self.assertEqual(self.client.get(token_url).status_code, 200)
        self.api("post", f"/admin/medien/films/{fid}/subtitles/{uz['id']}/approve", "admin", json={"approved": False})
        self.assertEqual({s["language"] for s in self.watch(fid)["subtitles"]}, {"de"})

        # the admin corrects lines: bad times refused, empty lines dropped, status kept
        url = f"/admin/medien/films/{fid}/subtitles/{de['id']}/cues"
        self.api("put", url, "admin", expect=422, json={"cues": [[2000, 1000, "rückwärts"]]})
        self.api("put", url, "admin", expect=422, json={"cues": [["0", 100, "x"]]})
        edited = [[c0, c1, text] for c0, c1, text in de_cues]
        edited[0][2] = "Ich möchte heute ins <b>Kino</b> gehen."
        edited.append([19_000, 19_500, "   "])
        out = self.api("put", url, "admin", json={"cues": edited}).json()
        self.assertEqual(out["cues"][0][2], "Ich möchte heute ins Kino gehen.")
        self.assertEqual(len(out["cues"]), len(de_cues))
        self.assertEqual((out["status"], out["source"]), ("APPROVED", "AI"))
        self.assertIsNotNone(out["edited_at"])

        srt = self.api("get", f"/admin/medien/films/{fid}/subtitles/{de['id']}/download?format=srt", "admin")
        self.assertIn("attachment", srt.headers["content-disposition"])
        self.assertTrue(srt.text.startswith("1\n00:00:"))
        self.assertIn("Ich möchte heute ins Kino gehen.", srt.text)
        vtt = self.api("get", f"/admin/medien/films/{fid}/subtitles/{de['id']}/download?format=vtt", "admin")
        self.assertTrue(vtt.text.startswith("WEBVTT"))

        # translate an approved track again: refused without replace, a new DRAFT with it
        self.api("post", f"/admin/medien/films/{fid}/subtitles/{de['id']}/translate", "admin", expect=409, json={"target": "uz"})
        self.api("post", f"/admin/medien/films/{fid}/subtitles/{de['id']}/translate", "admin", expect=422, json={"target": "de"})
        self.api("post", f"/admin/medien/films/{fid}/subtitles/{de['id']}/translate", "admin", expect=202, json={"target": "ru"})
        self.run_jobs()
        self.assertEqual(self.tracks(fid)["ru"]["status"], "DRAFT")

    def test_4_retry_continues_and_cancel(self):
        from app.services.medien import subtitle_ai as ai

        fid = self.film("retry")["id"]
        self.api("post", f"/admin/medien/films/{fid}/subtitles/ai", "admin", expect=202, json={"language": "de"})
        real = ai.FakeSTT.transcribe
        calls = []

        def flaky(self_, data, mime, language, seconds):
            calls.append(seconds)
            if len(calls) == 2:
                raise ai.SubtitleAIError("AI_HTTP_503", "The AI service answered HTTP 503.", retryable=True)
            return real(self_, data, mime, language, seconds)

        with patch.object(ai.FakeSTT, "transcribe", flaky):
            self.run_jobs()
            job = self.jobs(fid)[0]
            self.assertEqual((job["status"], job["error_code"], job["progress_done"]), ("FAILED", "AI_HTTP_503", 1))
            self.api("post", f"/admin/medien/films/{fid}/subtitle-jobs/{job['id']}/retry", "admin")
            self.api("post", f"/admin/medien/films/{fid}/subtitle-jobs/{job['id']}/retry", "admin", expect=409)  # already waiting
            self.run_jobs()
        job = self.jobs(fid)[0]
        self.assertEqual((job["status"], job["progress_done"], job["attempts"]), ("COMPLETED", 3, 2))
        self.assertEqual(len(calls), 4)  # piece 1, piece 2 failed, then only pieces 2 and 3
        self.assertEqual(self.tracks(fid)["de"]["source"], "AI")

        fid2 = self.film("cancel")["id"]
        job = self.api("post", f"/admin/medien/films/{fid2}/subtitles/ai", "admin", expect=202, json={"language": "en"}).json()
        out = self.api("post", f"/admin/medien/films/{fid2}/subtitle-jobs/{job['id']}/cancel", "admin").json()
        self.assertEqual((out["status"], out["error_code"]), ("FAILED", "CANCELLED"))
        self.assertEqual(self.run_jobs(), 0)
        self.assertNotIn("en", self.tracks(fid2))

    def test_5_detected_language_conflicts(self):
        from app.services.medien import subtitle_ai as ai

        fid = self.film("conflict")["id"]
        self.api("post", f"/admin/medien/films/{fid}/subtitles", "admin", data={"language": "de"}, files={"file": ("de.srt", SRT_DE, "text/plain")})
        r = self.api("post", f"/admin/medien/films/{fid}/subtitles/ai", "admin", expect=409, json={"language": "de"})
        self.assertIn("SUBTITLE_EXISTS", r.json()["message"])
        self.api("post", f"/admin/medien/films/{fid}/subtitles/ai", "admin", expect=202, json={"language": "auto"})
        self.run_jobs()
        job = self.jobs(fid)[0]
        self.assertEqual((job["status"], job["error_code"], job["progress_done"]), ("FAILED", "SUBTITLE_EXISTS", 0))  # stopped at the first piece
        self.assertEqual(self.tracks(fid)["de"]["source"], "UPLOAD")
        self.assertEqual(len(self.watch(fid)["subtitles"]), 1)
        # with "replace": the upload is replaced by an AI draft (students lose it until it is approved)
        self.api("post", f"/admin/medien/films/{fid}/subtitles/ai", "admin", expect=202, json={"language": "auto", "replace": True})
        self.run_jobs()
        self.assertEqual((self.tracks(fid)["de"]["source"], self.tracks(fid)["de"]["status"]), ("AI", "DRAFT"))
        self.assertEqual(self.watch(fid)["subtitles"], [])
        # a new upload replaces the draft and is visible at once
        self.api("post", f"/admin/medien/films/{fid}/subtitles", "admin", data={"language": "de"}, files={"file": ("de.srt", SRT_DE, "text/plain")})
        self.assertEqual((self.tracks(fid)["de"]["source"], self.tracks(fid)["de"]["status"]), ("UPLOAD", "APPROVED"))

        fid2 = self.film("french")["id"]
        real = ai.FakeSTT.transcribe
        self.api("post", f"/admin/medien/films/{fid2}/subtitles/ai", "admin", expect=202, json={"language": "auto"})
        with patch.object(ai.FakeSTT, "transcribe", lambda s, d, m, l, sec: ai.Transcript("fr", real(s, d, m, l, sec).segments, "test-fake")):
            self.run_jobs()
        job = self.jobs(fid2)[0]
        self.assertEqual((job["status"], job["error_code"]), ("FAILED", "LANGUAGE_NOT_SUPPORTED"))


if __name__ == "__main__":
    unittest.main()
