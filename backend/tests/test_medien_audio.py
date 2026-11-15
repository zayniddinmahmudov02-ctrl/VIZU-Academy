"""Musik upload (Admin → Medien → Musik): MP3, WAV, M4A, AAC, OGG, FLAC are accepted by content, the metadata (duration, bitrate, format, tags) is read,
nothing is re-encoded, a missing / failing metadata tool never blocks an upload (the original is kept, the admin sees a warning), a broken file is
refused, and the tool lookup also works when the service's PATH lacks ffmpeg (the production bug: systemd PATH = virtualenv only).
Integration test: VIZU_WB_TEST_DB_URL (+ DATABASE_NAME) and ffmpeg (FFMPEG_BIN)."""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.medien_base import FFMPEG, MedienBase, ffmpeg

FORMATS = {  # extension -> (ffmpeg arguments after the input, content type, audio_format stored)
    "mp3": (["-c:a", "libmp3lame", "-b:a", "128k"], "audio/mpeg", "mp3"),
    "wav": (["-c:a", "pcm_s16le"], "audio/wav", "wav"),
    "m4a": (["-c:a", "aac", "-b:a", "128k", "-f", "ipod"], "audio/mp4", "m4a"),
    "aac": (["-c:a", "aac", "-b:a", "128k", "-f", "adts"], "audio/aac", "aac"),
    "ogg": (["-c:a", "libvorbis", "-b:a", "96k"], "audio/ogg", "ogg"),
    "flac": (["-c:a", "flac"], "audio/flac", "flac"),
}


@unittest.skipUnless(FFMPEG, "needs ffmpeg (FFMPEG_BIN)")
class TestMusikUpload(MedienBase):
    @classmethod
    def extra_setup(cls):
        cls.files = {}
        for ext, (args, _, _) in FORMATS.items():
            path = Path(cls.tmp.name) / f"tone.{ext}"
            ffmpeg("-f", "lavfi", "-i", "sine=frequency=440:duration=2", *args, str(path))
            cls.files[ext] = path.read_bytes()
        tagged = Path(cls.tmp.name) / "tagged.mp3"
        ffmpeg("-f", "lavfi", "-i", "sine=frequency=330:duration=2", "-c:a", "libmp3lame", "-metadata", "title=Guten Morgen", "-metadata", "artist=Die Lerner",
               "-metadata", "album=Deutsch A1", "-metadata", "genre=Pop", str(tagged))
        cls.files["tagged"] = tagged.read_bytes()

    def upload(self, name, data, expect=200, **form):
        return self.api("post", "/admin/medien/songs", "admin", expect=expect, files={"file": (name, data, "application/octet-stream")},
                        data={"status": "PUBLISHED", "language": "de", **form})

    def test_1_every_format_is_accepted_read_and_streamed_unchanged(self):
        for ext, (_, content_type, audio_format) in FORMATS.items():
            song = self.upload(f"{self.title(ext)}.{ext}", self.files[ext], title=self.title(f"Song {ext}")).json()
            self.assertEqual((song["audio_format"], song["metadata_status"], song["file_status"]), (audio_format, "OK", "ok"), ext)
            self.assertAlmostEqual(song["duration_ms"], 2000, delta=300, msg=ext)
            self.assertGreater(song["bitrate_kbps"] or 0, 20, ext)
            self.assertEqual(song["file_size"], len(self.files[ext]), f"{ext}: stored byte for byte, no conversion")
            played = self.api("post", f"/medien/songs/{song['id']}/play", "a").json()
            self.as_(None)
            r = self.client.get(played["url"], headers={"Range": "bytes=0-99"})
            self.assertEqual((r.status_code, len(r.content), r.headers["content-type"]), (206, 100, content_type), ext)
            self.assertEqual(r.headers["x-content-type-options"], "nosniff")
            full = self.client.get(played["url"])
            self.assertEqual(full.content, self.files[ext], f"{ext}: the student gets exactly the uploaded file")
            self.api("delete", f"/admin/medien/songs/{song['id']}", "admin", expect=204)
        self.assertFalse([p for p in self.disk() if p.startswith("songs/")])

    def test_2_tags_fill_what_is_empty_the_admin_wins(self):
        # the form's default title is the file name: the tag takes its place; artist / album / genre come from the tags when left empty
        auto = self.upload("Dateiname.mp3", self.files["tagged"], title="Dateiname").json()
        self.assertEqual((auto["title"], auto["artist"], auto["album"], auto["genre"]), ("Guten Morgen", "Die Lerner", "Deutsch A1", "Pop"))
        # a title / artist typed by the admin is never replaced
        own = self.upload("x.mp3", self.files["tagged"], title=self.title("Eigener Titel"), artist="Eigene Band").json()
        self.assertEqual((own["title"], own["artist"], own["album"]), (self.title("Eigener Titel"), "Eigene Band", "Deutsch A1"))
        # and everything stays editable afterwards
        edited = self.api("put", f"/admin/medien/songs/{auto['id']}", "admin", json={"title": self.title("Neu"), "artist": "Anders"}).json()
        self.assertEqual((edited["title"], edited["artist"]), (self.title("Neu"), "Anders"))
        for s in (auto, own):
            self.api("delete", f"/admin/medien/songs/{s['id']}", "admin", expect=204)

    def test_3_broken_and_foreign_files_are_refused_cleanly(self):
        before = self.disk()
        for name, data in (("kaputt.mp3", b"ID3\x03\x00\x00\x00\x00\x00\x00" + os.urandom(2048)), ("text.mp3", b"this is not audio at all"), ("pic.mp3", b"\x89PNG\r\n\x1a\n" + b"0" * 64),
                           ("leer.mp3", b"")):
            r = self.upload(name, data, expect=400, title=self.title("Bad"))
            self.assertRegex(r.json()["message"], r"^(UNSUPPORTED_FILE|FILE_TOO_LARGE)", name)
        self.assertEqual(self.disk(), before, "a refused upload leaves nothing on disk")

    def test_4_a_missing_or_failing_metadata_tool_keeps_the_original(self):
        from app.services.audio_files import service as audio
        from app.services.medien import audio_meta

        with patch.object(audio, "find_tool", return_value=None):  # no ffmpeg / ffprobe at all
            song = self.upload("keintool.mp3", self.files["mp3"], title=self.title("No Tool")).json()
        self.assertEqual((song["metadata_status"], song["duration_ms"], song["file_status"]), ("FAILED", None, "ok"))
        self.assertIn("AUDIO_TOOL_MISSING", song["metadata_note"])
        self.assertTrue(self.api("post", f"/medien/songs/{song['id']}/play", "a").json()["url"])  # still playable
        with patch.object(audio_meta, "read", side_effect=RuntimeError("boom")):  # the metadata step itself crashes
            crashed = self.upload("crash.wav", self.files["wav"], title=self.title("Crash")).json()
        self.assertEqual((crashed["metadata_status"], crashed["file_status"]), ("FAILED", "ok"))
        # replacing the file later reads the metadata again and clears the warning
        fixed = self.api("post", f"/admin/medien/songs/{song['id']}/file", "admin", files={"file": ("neu.flac", self.files["flac"], "audio/flac")}).json()
        self.assertEqual((fixed["metadata_status"], fixed["audio_format"]), ("OK", "flac"))
        self.assertAlmostEqual(fixed["duration_ms"], 2000, delta=300)
        for s in (song, crashed):
            self.api("delete", f"/admin/medien/songs/{s['id']}", "admin", expect=204)

    def test_5_bulk_upload_of_ten_one_bad_the_rest_unaffected(self):
        order = ["mp3", "wav", "m4a", "aac", "BAD", "ogg", "flac", "mp3", "wav", "m4a"]
        codes, made = [], []
        for i, ext in enumerate(order):
            data = b"not audio" if ext == "BAD" else self.files[ext]
            r = self.upload(f"b{i}.{ext.lower()}", data, expect=None, title=self.title(f"Bulk {i}"))
            codes.append(r.status_code)
            if r.status_code == 200:
                made.append(r.json()["id"])
        self.assertEqual(codes, [200, 200, 200, 200, 400, 200, 200, 200, 200, 200])
        listed = self.api("get", f"/medien/songs?q={self.tag}%20Bulk&page_size=60", "a").json()
        self.assertEqual(listed["total"], 9)
        for sid in made:
            self.api("delete", f"/admin/medien/songs/{sid}", "admin", expect=204)

    def test_6_only_content_editors_upload(self):
        self.api("post", "/admin/medien/songs", "a", expect=403, files={"file": ("a.mp3", self.files["mp3"], "audio/mpeg")})
        self.as_(None)
        self.assertEqual(self.client.post("/api/v1/admin/medien/songs", files={"file": ("a.mp3", self.files["mp3"], "audio/mpeg")}).status_code, 401)


class TestToolLookup(unittest.TestCase):
    """The tool lookup does not depend on the service's PATH (pure unit tests)."""

    def test_finds_ffmpeg_in_system_folders_when_path_does_not_have_it(self):
        from app.services.audio_files import service as audio

        real_isfile = os.path.isfile
        with patch.dict(os.environ, {"FFMPEG_BIN": ""}, clear=False), patch("shutil.which", return_value=None), \
                patch("os.path.isfile", side_effect=lambda p: p == os.path.join("/usr/bin", "ffmpeg") or real_isfile(p)), patch("os.access", return_value=True):
            self.assertEqual(audio.find_tool("ffmpeg"), os.path.join("/usr/bin", "ffmpeg"))
            self.assertEqual(audio._bin("ffmpeg"), os.path.join("/usr/bin", "ffmpeg"))

    def test_nothing_found_is_a_503_with_the_known_code_only_when_a_tool_is_required(self):
        from fastapi import HTTPException

        from app.services.audio_files import service as audio

        with patch.dict(os.environ, {"FFMPEG_BIN": "", "FFPROBE_BIN": ""}, clear=False), patch("shutil.which", return_value=None), patch("os.path.isfile", return_value=False):
            self.assertIsNone(audio.find_tool("ffprobe"))
            with self.assertRaises(HTTPException) as ctx:
                audio._bin("ffmpeg")
            self.assertEqual((ctx.exception.status_code, ctx.exception.detail.split(":")[0]), (503, "AUDIO_TOOL_MISSING"))

    def test_environment_override_wins(self):
        from app.services.audio_files import service as audio

        with patch.dict(os.environ, {"FFMPEG_BIN": "/opt/custom/ffmpeg"}), patch("shutil.which", side_effect=lambda p: p if p == "/opt/custom/ffmpeg" else None):
            self.assertEqual(audio.find_tool("ffmpeg"), "/opt/custom/ffmpeg")

    def test_format_sniffing(self):
        from app.services.medien import common as c

        self.assertEqual([c.sniff_audio(h) for h in (b"ID3\x03" + b"0" * 12, b"\xff\xfb\x90\x00" + b"0" * 12, b"\xff\xf1\x50\x80" + b"0" * 12, b"fLaC" + b"0" * 12,
                                                      b"RIFF\x00\x00\x00\x00WAVE" + b"0" * 4, b"\x00\x00\x00\x20ftypM4A " + b"0" * 4, b"OggS" + b"0" * 12, b"MZ" + b"0" * 14)],
                         ["mp3", "mp3", "aac", "flac", "wav", "m4a", "ogg", None])


class TestMetadataParsers(unittest.TestCase):
    """The ffmpeg-only parser (no ffprobe) and the ffprobe JSON parser read the same facts."""

    REPORT = """Input #0, mp3, from 'x.mp3':
  Metadata:
    title           : Hallo Welt
    artist          : Max Beispiel
    encoder         : Lavf60
  Duration: 00:03:05.50, start: 0.025057, bitrate: 192 kb/s
  Stream #0:0: Audio: mp3 (mp3float), 44100 Hz, stereo, fltp, 192 kb/s
At least one output file must be specified
"""

    def test_ffmpeg_report(self):
        import subprocess
        from types import SimpleNamespace
        from pathlib import Path

        from app.services.medien import audio_meta

        with patch.object(subprocess, "run", return_value=SimpleNamespace(returncode=1, stderr=self.REPORT, stdout="")):
            info = audio_meta._from_ffmpeg("ffmpeg", Path("x.mp3"))
        self.assertEqual((info.duration_ms, info.bitrate_kbps, info.codec, info.title, info.artist, info.album), (185_500, 192, "mp3", "Hallo Welt", "Max Beispiel", None))

    def test_ffprobe_json_and_unreadable_file(self):
        import json
        import subprocess
        from types import SimpleNamespace
        from pathlib import Path

        from app.services.medien import audio_meta

        data = {"format": {"duration": "12.5", "bit_rate": "256000", "tags": {"TITLE": "Lied\x00 Eins", "Artist": "Band"}}, "streams": [{"codec_type": "audio", "codec_name": "flac"}]}
        with patch.object(subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=json.dumps(data), stderr="")):
            info = audio_meta._from_ffprobe("ffprobe", Path("x.flac"))
        self.assertEqual((info.duration_ms, info.bitrate_kbps, info.codec, info.title, info.artist), (12_500, 256, "flac", "Lied Eins", "Band"))
        with patch.object(subprocess, "run", return_value=SimpleNamespace(returncode=1, stdout="", stderr="x.mp3: Invalid data found when processing input")):
            with self.assertRaises(audio_meta.AudioUnreadable):
                audio_meta._from_ffprobe("ffprobe", Path("x.mp3"))


if __name__ == "__main__":
    unittest.main()
