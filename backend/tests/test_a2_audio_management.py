from collections import Counter
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

from app.models.listening_audio_archive import ListeningAudioArchive
from app.services.lesson_skills import admin as skill_admin
from app.services.lesson_skills.a2_audio_manifest import A2_AUDIO_MATERIALS, audit_audio_files


class TestA2AudioManifest(unittest.TestCase):
    def test_legacy_hint_list_is_unchanged_and_unverified(self):
        counts = Counter(item.lesson_number for item in A2_AUDIO_MATERIALS)
        self.assertEqual(len(counts), 13)
        self.assertEqual(len(A2_AUDIO_MATERIALS), 28)
        self.assertEqual(
            counts,
            Counter({**{lesson: 1 for lesson in (1, 2, 3, 5, 6, 8, 9)}, 4: 3, 7: 2, 10: 4, 11: 4, 12: 4, 13: 4}),
        )

    def test_inventory_accepts_exact_expected_files(self):
        files = [Path(f"{item.source_name}.{item.extension}") for item in A2_AUDIO_MATERIALS]
        result = audit_audio_files(files)
        self.assertTrue(result["ok"])
        self.assertEqual((result["discovered_count"], result["matched_count"]), (28, 28))

    def test_inventory_reports_missing_wrong_format_extra_and_ambiguous(self):
        files = [Path(f"{item.source_name}.{item.extension}") for item in A2_AUDIO_MATERIALS]
        files.remove(files[0])
        files.remove(Path(f"{A2_AUDIO_MATERIALS[2].source_name}.{A2_AUDIO_MATERIALS[2].extension}"))
        files.append(Path(f"{A2_AUDIO_MATERIALS[0].source_name}.mp3"))
        files.append(Path(f"{A2_AUDIO_MATERIALS[1].source_name}.mp3"))
        files.append(Path(f"{A2_AUDIO_MATERIALS[1].source_name}.MP3"))
        files.append(Path("unlisted audio.mp3"))
        result = audit_audio_files(files)
        self.assertFalse(result["ok"])
        self.assertTrue(result["missing"])
        self.assertTrue(result["wrong_format"])
        self.assertTrue(result["ambiguous"])
        self.assertEqual([path.name for path in result["unexpected"]], ["unlisted audio.mp3"])


class TestA2AudioReplacement(unittest.IsolatedAsyncioTestCase):
    async def test_replacement_archives_old_file_without_removing_questions_or_old_audio(self):
        listening_id = uuid4()
        old_questions = [object(), object()]
        task = type(
            "ListeningStub",
            (),
            {
                "id": listening_id,
                "a2_material_key": "a2-l01-audio-01",
                "is_published": True,
                "audio_storage_path": "old-audio.m4a",
                "audio_original_name": "original.m4a",
                "audio_content_type": "audio/mp4",
                "audio_size_bytes": 123,
                "audio_duration_seconds": 11,
                "questions": old_questions,
            },
        )()
        db = type(
            "DatabaseStub",
            (),
            {
                "get": lambda self, model, item_id: task,
                "add": lambda self, item: setattr(self, "added", item),
                "commit": lambda self: None,
                "refresh": lambda self, item: None,
            },
        )()
        actor_id = uuid4()

        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "new-audio.m4a").write_bytes(b"audio")

            async def store_audio(_file, _expected_format=None):
                return "new-audio.m4a", "m4a"

            with (
                patch.object(skill_admin, "_store_audio", new=AsyncMock(side_effect=store_audio)) as store_mock,
                patch.object(skill_admin.listening_storage, "ROOT", root),
                patch.object(skill_admin, "_delete_if_unused", new=AsyncMock()) as delete_old,
            ):
                result = await skill_admin.upload_listening_audio(
                    db,
                    listening_id,
                    UploadFile(file=BytesIO(b""), filename="replacement.m4a", headers=Headers({"content-type": "audio/mp4"})),
                    None,
                    replaced_by_id=actor_id,
                )

        self.assertIs(result, task)
        self.assertEqual(task.audio_storage_path, "new-audio.m4a")
        self.assertFalse(task.is_published)
        self.assertEqual(task.questions, old_questions)
        self.assertIsInstance(db.added, ListeningAudioArchive)
        self.assertEqual(db.added.storage_path, "old-audio.m4a")
        self.assertEqual(db.added.replaced_by_id, actor_id)
        delete_old.assert_not_awaited()
        store_mock.assert_awaited_once()
        self.assertEqual(store_mock.await_args.args[1], "m4a")

    async def test_mapped_a2_audio_cannot_be_physically_deleted(self):
        task = type(
            "ListeningStub",
            (),
            {"id": uuid4(), "a2_material_key": "a2-l01-audio-01", "audio_storage_path": "old-audio.mp3"},
        )()
        db = type("DatabaseStub", (), {"get": lambda self, model, item_id: task})()
        with self.assertRaises(HTTPException) as error:
            await skill_admin.delete_listening_audio(db, task.id)
        self.assertEqual(error.exception.status_code, 409)

    async def test_a2_material_rejects_extra_track_upload(self):
        task = type(
            "ListeningStub",
            (),
            {"id": uuid4(), "a2_material_key": "a2-l01-audio-01", "audio_tracks": []},
        )()
        db = type("DatabaseStub", (), {"get": lambda self, model, item_id: task})()
        with self.assertRaises(HTTPException) as error:
            await skill_admin.upload_audio_track(
                db,
                task.id,
                "Extra audio",
                UploadFile(file=BytesIO(b""), filename="extra.mp3"),
                None,
            )
        self.assertEqual(error.exception.status_code, 409)

    async def test_upload_rejects_audio_with_wrong_detected_format_before_storage(self):
        upload = UploadFile(
            file=BytesIO(b"ID3\x04" + b"\x00" * 12),
            filename="audio.mp3",
            headers=Headers({"content-type": "audio/mpeg"}),
        )
        with self.assertRaises(HTTPException) as error:
            await skill_admin._store_audio(upload, expected_format="m4a")
        self.assertEqual(error.exception.status_code, 400)
        self.assertIn("M4A", error.exception.detail)


if __name__ == "__main__":
    unittest.main()
