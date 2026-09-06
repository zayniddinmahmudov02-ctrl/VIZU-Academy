"""Tests for the new legacy Schreiben/Sprechen real-submission system
(StudentWriting/StudentSpeaking extended with a genuine student-submit +
teacher-grade workflow — see app/models/student_writing.py and
app/models/student_speaking.py). Same style as
test_homework_grading_rbac_and_idor.py: services' repository/assignment
collaborators are swapped for MagicMocks, no real DB (matches this
repo's established test convention — see conftest.py).

Covers the spec's explicit test list (section 38): word-limit validation,
ownership, a teacher's assigned-course scope for both grading endpoints
and speaking audio access, and grade-request score validation.
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.student_speaking import SpeakingGradeRequest
from app.schemas.student_writing import WritingGradeRequest
from app.services.student_speaking.service import StudentSpeakingService
from app.services.student_writing.service import StudentWritingService


class TestGradeRequestValidation(unittest.TestCase):
    def test_writing_grade_score_out_of_range_rejected(self):
        with self.assertRaises(ValidationError):
            WritingGradeRequest(score=101, feedback="x", status="GRADED")

    def test_speaking_grade_score_out_of_range_rejected(self):
        with self.assertRaises(ValidationError):
            SpeakingGradeRequest(score=-1, feedback="x", status="GRADED")

    def test_writing_grade_status_must_be_graded_or_needs_revision(self):
        with self.assertRaises(ValidationError):
            WritingGradeRequest(score=50, feedback="x", status="SUBMITTED")


class TestStudentWritingServiceSubmit(unittest.TestCase):
    def _service(self):
        service = StudentWritingService(db=MagicMock())
        service.repository = MagicMock()
        service.assignments = MagicMock()
        return service

    def test_submit_final_below_min_words_rejected(self):
        service = self._service()
        writing = MagicMock(is_published=True, min_words=10, max_words=100)
        service.db.get.return_value = writing

        with self.assertRaises(HTTPException) as ctx:
            service.submit(uuid4(), uuid4(), "too short", submit_final=True)

        self.assertEqual(ctx.exception.status_code, 400)
        service.repository.get_by_user_and_writing.assert_not_called()

    def test_submit_final_above_max_words_rejected(self):
        service = self._service()
        writing = MagicMock(is_published=True, min_words=0, max_words=3)
        service.db.get.return_value = writing

        with self.assertRaises(HTTPException) as ctx:
            service.submit(uuid4(), uuid4(), "one two three four five", submit_final=True)

        self.assertEqual(ctx.exception.status_code, 400)

    def test_draft_save_skips_word_limit_validation(self):
        # "Entwurf speichern" must never block on word count — only the
        # final "Aufgabe abgeben" does.
        service = self._service()
        writing = MagicMock(is_published=True, min_words=50, max_words=100)
        service.db.get.return_value = writing
        service.repository.get_by_user_and_writing.return_value = None

        item = service.submit(uuid4(), uuid4(), "short draft", submit_final=False)

        # No HTTPException raised above is the actual assertion here — a
        # short draft must never trip the min-word check. Also confirm it
        # really persisted as a new row (service.db.add, not the
        # StudentWritingCreate-shaped repository.create()).
        service.db.add.assert_called_once()
        self.assertIsNotNone(item)

    def test_submit_to_unpublished_writing_404s(self):
        service = self._service()
        service.db.get.return_value = MagicMock(is_published=False)

        with self.assertRaises(HTTPException) as ctx:
            service.submit(uuid4(), uuid4(), "text", submit_final=False)

        self.assertEqual(ctx.exception.status_code, 404)

    def test_cannot_resubmit_an_already_graded_submission(self):
        service = self._service()
        writing = MagicMock(is_published=True, min_words=0, max_words=1000)
        service.db.get.return_value = writing
        service.repository.get_by_user_and_writing.return_value = MagicMock(status="GRADED")

        with self.assertRaises(HTTPException) as ctx:
            service.submit(uuid4(), uuid4(), "trying to overwrite", submit_final=True)

        self.assertEqual(ctx.exception.status_code, 409)


class TestStudentWritingServiceIdor(unittest.TestCase):
    def _service(self):
        service = StudentWritingService(db=MagicMock())
        service.repository = MagicMock()
        service.assignments = MagicMock()
        return service

    def test_get_for_teacher_404s_outside_assigned_courses(self):
        service = self._service()
        service.assignments.course_ids_for_teacher.return_value = [uuid4()]
        service.repository.get_for_teacher.return_value = None

        with self.assertRaises(HTTPException) as ctx:
            service.get_for_teacher(uuid4(), uuid4())

        self.assertEqual(ctx.exception.status_code, 404)

    def test_grade_rechecks_scope_before_writing(self):
        service = self._service()
        service.assignments.course_ids_for_teacher.return_value = []
        service.repository.get_for_teacher.return_value = None

        with self.assertRaises(HTTPException):
            service.grade(uuid4(), uuid4(), score=90, feedback="ok", new_status="GRADED")

        service.repository.get.assert_not_called()


class TestStudentSpeakingAudioAuthorization(unittest.TestCase):
    def _service(self):
        service = StudentSpeakingService(db=MagicMock())
        service.repository = MagicMock()
        service.assignments = MagicMock()
        return service

    def test_owner_student_can_access_own_audio(self):
        service = self._service()
        student_id = uuid4()
        item = MagicMock(user_id=student_id, storage_path="some/path.webm")
        service.repository.get.return_value = item

        result = service.authorize_audio_access(uuid4(), MagicMock(id=student_id, role="STUDENT"))

        self.assertIs(result, item)

    def test_other_student_gets_404_not_403(self):
        service = self._service()
        item = MagicMock(user_id=uuid4(), storage_path="some/path.webm")
        service.repository.get.return_value = item

        with self.assertRaises(HTTPException) as ctx:
            service.authorize_audio_access(uuid4(), MagicMock(id=uuid4(), role="STUDENT"))

        self.assertEqual(ctx.exception.status_code, 404)

    def test_unassigned_teacher_gets_404(self):
        # Course A teacher must not reach a Course B student's audio, even
        # with a real submission id (spec section 35's explicit scenario).
        service = self._service()
        item = MagicMock(user_id=uuid4(), storage_path="some/path.webm")
        service.repository.get.return_value = item
        service.assignments.course_ids_for_teacher.return_value = [uuid4()]
        service.repository.get_for_teacher.return_value = None  # not in scope

        with self.assertRaises(HTTPException) as ctx:
            service.authorize_audio_access(uuid4(), MagicMock(id=uuid4(), role="TEACHER"))

        self.assertEqual(ctx.exception.status_code, 404)

    def test_assigned_teacher_can_access(self):
        service = self._service()
        teacher = MagicMock(id=uuid4(), role="TEACHER")
        item = MagicMock(user_id=uuid4(), storage_path="some/path.webm")
        service.repository.get.return_value = item
        service.assignments.course_ids_for_teacher.return_value = [uuid4()]
        service.repository.get_for_teacher.return_value = (item, MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())

        result = service.authorize_audio_access(uuid4(), teacher)

        self.assertIs(result, item)

    def test_missing_recording_404s(self):
        service = self._service()
        service.repository.get.return_value = None

        with self.assertRaises(HTTPException) as ctx:
            service.authorize_audio_access(uuid4(), MagicMock(id=uuid4(), role="STUDENT"))

        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
