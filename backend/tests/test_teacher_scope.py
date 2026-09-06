"""Tests for app.services.teacher.scope.teacher_course_ids_or_none — the
shared scoping rule now applied to writing_service/speaking_service's
pending-review list, teacher-review submit, and audio access functions
(Teacher Panel 2.0's Schreiben/Sprechen sections). See section 19/20 of
the spec: a TEACHER must never reach another course's submissions, even
by guessing an id, while every OTHER admin-panel role's existing
(unscoped) behavior must stay exactly as it was.
"""

import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.teacher.scope import teacher_course_ids_or_none


class TestTeacherCourseIdsOrNone(unittest.TestCase):
    def test_non_teacher_roles_get_none_unrestricted(self):
        # None is the "existing behavior, don't touch it" signal — every
        # role that already had full visibility keeps it.
        for role in ("SUPER_ADMIN", "ADMIN", "CONTENT_MANAGER", "PAYMENT_MANAGER", "SUPPORT", "STUDENT"):
            with self.subTest(role=role):
                user = MagicMock(role=role)
                self.assertIsNone(teacher_course_ids_or_none(MagicMock(), user))

    @patch("app.services.teacher.scope.TeacherAssignmentRepository")
    def test_teacher_role_gets_their_assigned_course_ids_as_strings(self, mock_repo_cls):
        course_id = uuid4()
        mock_repo_cls.return_value.course_ids_for_teacher.return_value = [course_id]

        user = MagicMock(role="TEACHER", id=uuid4())
        result = teacher_course_ids_or_none(MagicMock(), user)

        self.assertEqual(result, [str(course_id)])

    @patch("app.services.teacher.scope.TeacherAssignmentRepository")
    def test_teacher_with_zero_assignments_gets_empty_list_not_none(self, mock_repo_cls):
        # Empty list must NOT be confused with None — None means
        # unrestricted, [] means "restricted to nothing," i.e. sees zero
        # submissions. Conflating the two would silently give an
        # unassigned teacher full visibility.
        mock_repo_cls.return_value.course_ids_for_teacher.return_value = []

        user = MagicMock(role="TEACHER", id=uuid4())
        result = teacher_course_ids_or_none(MagicMock(), user)

        self.assertEqual(result, [])
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
