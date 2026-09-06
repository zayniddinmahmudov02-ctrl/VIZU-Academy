"""Tests for the new Homework grading feature (Teacher Panel 2.0):
HomeworkGradeRequest's backend score validation, and the IDOR scoping
that keeps a teacher from ever reaching a submission outside their
TeacherAssignment courses — even by guessing a submission id directly
(section 20 of the spec: "Course A ga assigned. Course B studentining
submission ID'sini bilib qolsa ham -> access denied").

Same style as test_teacher_panel_rbac.py: the service's collaborators
(HomeworkSubmissionRepository, TeacherAssignmentRepository) are swapped
for MagicMocks after construction rather than hitting a real DB — no
fixture DB infra exists in this repo (see conftest.py), matching every
other service-level test here.
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.homework_submission import HomeworkGradeRequest
from app.services.homework_submission.service import HomeworkSubmissionService


class TestHomeworkGradeRequestValidation(unittest.TestCase):
    """Backend validation, not frontend-only — a score outside 0-100 or a
    status outside the two real teacher-settable values must 422, no
    matter what the UI sends."""

    def test_valid_score_and_status_accepted(self):
        payload = HomeworkGradeRequest(score=85, feedback="Gut gemacht!", status="GRADED")
        self.assertEqual(payload.score, 85)

    def test_score_above_100_rejected(self):
        with self.assertRaises(ValidationError):
            HomeworkGradeRequest(score=101, feedback="x", status="GRADED")

    def test_negative_score_rejected(self):
        with self.assertRaises(ValidationError):
            HomeworkGradeRequest(score=-1, feedback="x", status="GRADED")

    def test_score_boundaries_0_and_100_accepted(self):
        HomeworkGradeRequest(score=0, feedback="x", status="GRADED")
        HomeworkGradeRequest(score=100, feedback="x", status="GRADED")

    def test_empty_feedback_rejected(self):
        with self.assertRaises(ValidationError):
            HomeworkGradeRequest(score=50, feedback="", status="GRADED")

    def test_arbitrary_status_rejected(self):
        # Only GRADED/NEEDS_REVISION are teacher-settable — SUBMITTED is a
        # student-only transition (created by submit()), never something a
        # grade request should be able to set directly.
        with self.assertRaises(ValidationError):
            HomeworkGradeRequest(score=50, feedback="x", status="SUBMITTED")


class TestHomeworkSubmissionServiceIdor(unittest.TestCase):
    def _service_with_mocks(self):
        service = HomeworkSubmissionService(db=MagicMock())
        service.repository = MagicMock()
        service.assignments = MagicMock()
        return service

    def test_get_for_teacher_404s_when_submission_outside_assigned_courses(self):
        service = self._service_with_mocks()
        teacher_id = uuid4()
        submission_id = uuid4()

        # Teacher IS assigned to some course, but the repository (scoped
        # to exactly those course_ids in its SQL join/filter) finds no
        # matching row for this submission_id — i.e. it belongs to a
        # different, unassigned course.
        service.assignments.course_ids_for_teacher.return_value = [uuid4()]
        service.repository.get_for_teacher.return_value = None

        with self.assertRaises(HTTPException) as ctx:
            service.get_for_teacher(teacher_id, submission_id)

        self.assertEqual(ctx.exception.status_code, 404)

    def test_get_for_teacher_404s_when_teacher_has_no_assignments_at_all(self):
        service = self._service_with_mocks()
        service.assignments.course_ids_for_teacher.return_value = []
        service.repository.get_for_teacher.return_value = None

        with self.assertRaises(HTTPException) as ctx:
            service.get_for_teacher(uuid4(), uuid4())

        self.assertEqual(ctx.exception.status_code, 404)
        # Zero assigned courses must never even reach the repository query
        # with an empty/unbounded filter.
        service.repository.get_for_teacher.assert_called_once()
        called_course_ids = service.repository.get_for_teacher.call_args[0][0]
        self.assertEqual(called_course_ids, [])

    def test_grade_re_checks_scope_before_writing(self):
        service = self._service_with_mocks()
        teacher_id = uuid4()
        submission_id = uuid4()

        service.assignments.course_ids_for_teacher.return_value = []
        service.repository.get_for_teacher.return_value = None

        with self.assertRaises(HTTPException) as ctx:
            service.grade(teacher_id, submission_id, score=90, feedback="ok", new_status="GRADED")

        self.assertEqual(ctx.exception.status_code, 404)
        # The IDOR check must fail closed BEFORE any write is attempted.
        service.repository.grade.assert_not_called()

    def test_grade_writes_with_reviewer_id_when_authorized(self):
        service = self._service_with_mocks()
        teacher_id = uuid4()
        submission_id = uuid4()

        # Authorized: the teacher IS assigned to this submission's course.
        course_id = uuid4()
        service.assignments.course_ids_for_teacher.return_value = [course_id]

        student = MagicMock(id=uuid4(), email="student@example.com", first_name="Anna", last_name="Muster")
        homework = MagicMock(title="Hausaufgabe 1")
        lesson = MagicMock(title="Lektion 1", number=1)
        module = MagicMock()
        course = MagicMock(title="Deutsch A1", level="A1")
        homework.lesson = lesson
        lesson.module = module
        module.course = course

        # The pre-grade submission, as read for grade()'s own IDOR
        # re-check (see service.grade -> self.get_for_teacher) — concrete
        # field values, same as a real ORM row would have, not a bare
        # MagicMock (which would fail TeacherHomeworkSubmission's own
        # pydantic validation on .id/.text_content/etc).
        pre_grade_submission = MagicMock(
            id=submission_id,
            text_content="Meine Antwort",
            status="SUBMITTED",
            submitted_at=datetime.now(timezone.utc),
            score=None,
            feedback=None,
            reviewed_at=None,
        )
        raw_row = (pre_grade_submission, homework, lesson, module, course, student)
        service.repository.get_for_teacher.return_value = raw_row

        graded = MagicMock(
            id=submission_id,
            homework=homework,
            student=student,
            text_content="Meine Antwort",
            status="GRADED",
            submitted_at=datetime.now(timezone.utc),
            score=90,
            feedback="Sehr gut",
            reviewed_at=datetime.now(timezone.utc),
        )
        service.repository.get.return_value = MagicMock()
        service.repository.grade.return_value = graded

        result = service.grade(teacher_id, submission_id, score=90, feedback="Sehr gut", new_status="GRADED")

        # reviewer_id passed through is the CURRENT teacher, never anyone
        # else's id (e.g. never the student's, never unset).
        service.repository.grade.assert_called_once()
        args, _kwargs = service.repository.grade.call_args
        self.assertEqual(args[1], teacher_id)
        self.assertEqual(result.score, 90)
        self.assertEqual(result.status, "GRADED")


if __name__ == "__main__":
    unittest.main()
