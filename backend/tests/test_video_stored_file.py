"""Video files are read only through stored_file_path(): inside protected
video storage, existing, never outside the storage root."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.storage.protected_local import ProtectedVideoStorage
from app.services.video import service as video_service


class StoredFilePathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "protected_storage"
        (self.root / "videos" / "lesson").mkdir(parents=True)
        (self.root / "videos" / "lesson" / "a.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42")
        (Path(self.tmp.name) / "secret.txt").write_text("outside")
        patcher = patch.object(ProtectedVideoStorage, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_existing_file_resolves_inside_the_root(self):
        path = video_service.stored_file_path("videos/lesson/a.mp4")
        self.assertIsNotNone(path)
        self.assertTrue(path.is_file())
        self.assertIn(self.root.resolve(), path.parents)

    def test_missing_file_is_none(self):
        self.assertIsNone(video_service.stored_file_path("videos/lesson/missing.mp4"))

    def test_empty_key_is_none(self):
        self.assertIsNone(video_service.stored_file_path(None))
        self.assertIsNone(video_service.stored_file_path(""))

    def test_parent_traversal_is_rejected(self):
        self.assertIsNone(video_service.stored_file_path("../secret.txt"))
        self.assertIsNone(video_service.stored_file_path("videos/../../secret.txt"))

    def test_absolute_key_is_rejected(self):
        self.assertIsNone(video_service.stored_file_path(str(Path(self.tmp.name) / "secret.txt")))

    def test_directory_is_not_a_file(self):
        self.assertIsNone(video_service.stored_file_path("videos/lesson"))

    def test_resolve_video_path_uses_the_same_rules(self):
        svc = video_service.VideoService.__new__(video_service.VideoService)
        ok = type("V", (), {"storage_key": "videos/lesson/a.mp4"})()
        bad = type("V", (), {"storage_key": "../secret.txt"})()
        self.assertIsNotNone(svc.resolve_video_path(ok))
        self.assertIsNone(svc.resolve_video_path(bad))


class MediaTypeTests(unittest.TestCase):
    def test_media_type_follows_the_file_extension(self):
        self.assertEqual(video_service.video_media_type(Path("x.mp4")), "video/mp4")
        self.assertEqual(video_service.video_media_type(Path("x.WEBM")), "video/webm")
        self.assertEqual(video_service.video_media_type(Path("x.mov")), "video/quicktime")
        self.assertEqual(video_service.video_media_type(Path("x.bin")), "video/mp4")


if __name__ == "__main__":
    unittest.main()
