"""LocalStorage (all private file stores): a key may never leave the storage root ("../", absolute paths), the size limit raises its own
UploadTooLarge (a ValueError, so older callers keep working), and a parallel upload into a folder that is being created is not refused
(the containment check is retried — Windows resolved such a path differently for an instant in the 500-song stress test)."""

import asyncio
import tempfile
import threading
import unittest
from pathlib import Path

from app.core.storage.local import LocalStorage, UploadTooLarge


class _File:
    def __init__(self, data: bytes):
        self.data, self.pos = data, 0

    async def read(self, n: int) -> bytes:
        chunk = self.data[self.pos:self.pos + n]
        self.pos += len(chunk)
        return chunk


class TestStoragePaths(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = LocalStorage()
        self.store.ROOT = Path(self.tmp.name) / "root"
        self.store.ROOT.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_keys_stay_inside_the_root(self):
        self.assertEqual(self.store._inside_root("songs/a.mp3"), self.store.ROOT / "songs/a.mp3")
        for bad in ("../outside.mp3", "songs/../../outside.mp3", str(Path(self.tmp.name) / "elsewhere.mp3")):
            with self.assertRaises(ValueError):
                self.store._inside_root(bad)
        with self.assertRaises(ValueError):
            asyncio.run(self.store.upload(_File(b"x"), "../evil.mp3"))
        self.assertFalse((Path(self.tmp.name) / "evil.mp3").exists())

    def test_size_limit_has_its_own_error_and_leaves_nothing(self):
        with self.assertRaises(UploadTooLarge):
            asyncio.run(self.store.upload(_File(b"x" * 3000), "songs/big.mp3", max_bytes=1000))
        self.assertFalse((self.store.ROOT / "songs/big.mp3").exists())
        asyncio.run(self.store.upload(_File(b"x" * 900), "songs/ok.mp3", max_bytes=1000))
        self.assertEqual((self.store.ROOT / "songs/ok.mp3").stat().st_size, 900)

    def test_parallel_uploads_into_a_new_folder(self):
        errors = []

        def one(i):
            try:
                asyncio.run(self.store.upload(_File(b"data"), f"fresh/{i}.mp3", max_bytes=100))
            except Exception as exc:  # noqa: BLE001 — collected for the assertion
                errors.append(repr(exc))

        threads = [threading.Thread(target=one, args=(i,)) for i in range(24)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        self.assertEqual(len(list((self.store.ROOT / "fresh").iterdir())), 24)


if __name__ == "__main__":
    unittest.main()
