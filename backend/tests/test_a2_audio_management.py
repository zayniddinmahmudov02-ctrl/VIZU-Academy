from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

from app.models.listening_audio_archive import ListeningAudioArchive
from app.services.lesson_skills import admin as skill_admin


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
        self.assertIsNone(store_mock.await_args.args[1])

    def _delete_fixture(self, counts):
        task = SimpleNamespace(
            id=uuid4(), a2_material_key="a2-l01-audio-01", audio_storage_path="old.m4a", audio_content_type="audio/mp4",
            audio_size_bytes=5, audio_original_name="A2 1.Unterricht Hören.m4a", audio_duration_seconds=3,
            audio_url=None, is_published=True, questions=[object()],
        )
        db = MagicMock()
        db.get.return_value = task
        db.scalar.side_effect = counts  # listening refs, track refs, archive ref
        return task, db

    async def test_delete_removes_file_then_clears_record_and_keeps_questions(self):
        task, db = self._delete_fixture([1, 0, None])
        with patch.object(skill_admin.listening_storage, "delete", new=AsyncMock()) as delete:
            await skill_admin.delete_listening_audio(db, task.id)
        delete.assert_awaited_once_with("old.m4a")
        self.assertIsNone(task.audio_storage_path)
        self.assertFalse(task.is_published)
        self.assertEqual(len(task.questions), 1)
        db.commit.assert_called_once()

    async def test_failed_file_deletion_changes_nothing_and_reports_error(self):
        task, db = self._delete_fixture([1, 0, None])
        with patch.object(skill_admin.listening_storage, "delete", new=AsyncMock(side_effect=OSError("busy"))):
            with self.assertRaises(HTTPException) as error:
                await skill_admin.delete_listening_audio(db, task.id)
        self.assertEqual(error.exception.status_code, 500)
        self.assertEqual(task.audio_storage_path, "old.m4a")
        db.commit.assert_not_called()

    async def test_file_shared_with_another_record_is_kept(self):
        task, db = self._delete_fixture([2, 0, None])
        with patch.object(skill_admin.listening_storage, "delete", new=AsyncMock()) as delete:
            await skill_admin.delete_listening_audio(db, task.id)
        delete.assert_not_awaited()
        self.assertIsNone(task.audio_storage_path)

    def test_student_gets_no_player_for_a_record_whose_file_is_gone(self):
        from app.services.lesson_skills import skill_tests

        gone = SimpleNamespace(audio_storage_path="missing.m4a", audio_url=None)
        external = SimpleNamespace(audio_storage_path=None, audio_url="https://example.test/a.mp3")
        with patch.object(skill_admin, "listening_audio_path", return_value=None):
            self.assertFalse(skill_tests.has_audio(gone))
        with patch.object(skill_admin, "listening_audio_path", return_value=Path("x.m4a")):
            self.assertTrue(skill_tests.has_audio(gone))
        self.assertTrue(skill_tests.has_audio(external))
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
