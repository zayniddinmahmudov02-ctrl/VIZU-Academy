"""Uploaded file names come from the client's multipart header. The generic
uploader (/upload/{folder}, /media-library/upload, avatars) wrote them to
uploads/<folder>/<filename> unchanged, so filename="../../app/main.py" wrote
outside the uploads directory (the service runs as root)."""

import asyncio
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from starlette.datastructures import Headers, UploadFile

from app.core.storage.local import LocalStorage
from app.services.upload.service import UploadService, safe_filename


def _file(name, data=b"x", content_type="image/png"):
    return UploadFile(io.BytesIO(data), filename=name, headers=Headers({"content-type": content_type}))


class TestUploadPathSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "uploads"
        self.patch = mock.patch.object(LocalStorage, "ROOT", self.root)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _upload(self, name):
        service = UploadService()
        service.storage = LocalStorage()
        return asyncio.run(service.upload(_file(name), "images"))

    def test_traversal_in_filename_stays_inside_the_folder(self):
        for name in ("../../evil.png", "..\\..\\evil.png", "/etc/evil.png", "a/../../evil.png"):
            with self.subTest(name=name):
                result = self._upload(name)
                written = [p for p in self.tmp.rglob("*") if p.is_file()]
                self.assertTrue(all(self.root / "images" in p.parents for p in written), written)
                self.assertNotIn("..", result["path"])
                for p in written:
                    p.unlink()

    def test_storage_refuses_a_path_outside_its_root(self):
        with self.assertRaises(ValueError):
            asyncio.run(LocalStorage().upload(_file("x.png"), "../outside.png"))
        self.assertFalse((self.tmp / "outside.png").exists())
        with self.assertRaises(ValueError):
            asyncio.run(LocalStorage().delete("../../outside.png"))

    def test_safe_filename(self):
        self.assertEqual(safe_filename("../../a b.png"), "a_b.png")
        self.assertEqual(safe_filename("C:\\x\\photo.JPG"), "photo.JPG")
        self.assertEqual(safe_filename(".."), "file")
        self.assertEqual(safe_filename(""), "file")
        self.assertEqual(safe_filename(".htaccess"), "htaccess")
        self.assertLessEqual(len(safe_filename("a" * 400 + ".png")), 150)
        self.assertTrue(safe_filename("a" * 400 + ".png").endswith(".png"))

    def test_active_content_is_refused(self):
        from fastapi import HTTPException

        for name in ("x.html", "X.HTM", "logo.svg", "a.js", "../../shell.php"):
            with self.subTest(name=name):
                with self.assertRaises(HTTPException) as ctx:
                    self._upload(name)
                self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual([p for p in self.tmp.rglob("*") if p.is_file()], [])

    def test_media_types_are_accepted(self):
        for name in ("a.mp3", "b.m4a", "c.png", "d.pdf", "e.mp4", "f.docx", "noext"):
            with self.subTest(name=name):
                self._upload(name)

    def test_ordinary_names_are_kept(self):
        result = self._upload("Lektion-1_Hören.mp3")
        self.assertEqual(result["path"], "images/Lektion-1_Hören.mp3")
        self.assertTrue((self.root / "images" / "Lektion-1_Hören.mp3").is_file())


if __name__ == "__main__":
    unittest.main()
