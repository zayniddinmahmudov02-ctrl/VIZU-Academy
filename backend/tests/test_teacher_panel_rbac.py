"""Tests for the new Teacher Panel / Panel Switcher RBAC gate
(require_teacher_panel_access, app/api/dependencies/auth.py).

Same style/shape as test_books_admin_schema_and_auth.py's
TestRequireAdminPanelAccess — a plain MagicMock(role=...) stands in for
the User the dependency receives (get_current_user has already resolved
it upstream by this point), no real DB needed for a dependency that only
branches on `.role`.

Covers the panel-switcher spec's access matrix: the special account
(SUPER_ADMIN) and a TEACHER-role account both reach /teacher/*; a plain
STUDENT (and every other admin-panel role that isn't SUPER_ADMIN/TEACHER)
gets 403, never a silent pass-through.
"""

import asyncio
import unittest
from unittest.mock import MagicMock

from fastapi import HTTPException

from app.api.dependencies.auth import require_teacher_panel_access


class TestRequireTeacherPanelAccess(unittest.TestCase):
    def _run(self, coro):
        return asyncio.run(coro)

    def test_teacher_role_passes(self):
        user = MagicMock(role="TEACHER")
        result = self._run(require_teacher_panel_access(current_user=user))
        self.assertIs(result, user)

    def test_super_admin_passes(self):
        # The special account (already SUPER_ADMIN) must reach the Teacher
        # Panel too — this is what makes that possible, role-based, not an
        # email check.
        user = MagicMock(role="SUPER_ADMIN")
        result = self._run(require_teacher_panel_access(current_user=user))
        self.assertIs(result, user)

    def test_student_role_is_403_not_401(self):
        user = MagicMock(role="STUDENT")
        with self.assertRaises(HTTPException) as ctx:
            self._run(require_teacher_panel_access(current_user=user))
        self.assertEqual(ctx.exception.status_code, 403)

    def test_plain_admin_roles_are_403(self):
        # ADMIN/CONTENT_MANAGER/PAYMENT_MANAGER/SUPPORT can reach the Admin
        # Panel's read endpoints (require_admin_panel_access), but none of
        # them is a teacher — the Teacher Panel is not part of what those
        # roles are for.
        for role in ("ADMIN", "CONTENT_MANAGER", "PAYMENT_MANAGER", "SUPPORT"):
            with self.subTest(role=role):
                user = MagicMock(role=role)
                with self.assertRaises(HTTPException) as ctx:
                    self._run(require_teacher_panel_access(current_user=user))
                self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
