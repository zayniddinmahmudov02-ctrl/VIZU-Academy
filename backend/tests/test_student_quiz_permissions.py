"""StudentQuiz rows are grades: section gating and the lesson's 100-point score
read them. They are written by the server-graded quiz submit
(app.services.quiz.grading_service); the generic CRUD let any student POST
{"user_id": <self>, "score": 100, "passed": true} or PUT a better score."""

import asyncio
import importlib
import unittest
import uuid
from types import SimpleNamespace
from unittest import mock

from fastapi import HTTPException

from app.api.dependencies.auth import get_current_user
from app.schemas.student_quiz import StudentQuizCreate, StudentQuizUpdate

sq = importlib.import_module("app.api.student_quiz.router")


def _deps(route_name):
    route = next(r for r in sq.router.routes if r.name == route_name)
    return [d.call for d in route.dependant.dependencies]


class TestStudentQuizWrites(unittest.TestCase):
    def test_writes_are_admin_only(self):
        for name in ("create", "update", "delete"):
            with self.subTest(route=name):
                calls = _deps(name)
                self.assertNotIn(get_current_user, calls)
                self.assertTrue(any(getattr(c, "__name__", "") == "require_admin_panel_access" for c in calls), calls)

    def test_student_is_refused_by_the_dependency(self):
        from app.api.dependencies.auth import require_admin_panel_access

        student = SimpleNamespace(id=uuid.uuid4(), role="STUDENT")
        with self.assertRaises(HTTPException) as ctx:
            result = require_admin_panel_access(current_user=student)
            if asyncio.iscoroutine(result):
                asyncio.run(result)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_reads_stay_owner_or_admin(self):
        self.assertIn(get_current_user, _deps("get_one"))
        self.assertIn(get_current_user, _deps("get_all"))

    def test_owner_check_matches_uuid_ids(self):
        me = SimpleNamespace(id=uuid.uuid4(), role="STUDENT")
        sq._ensure_owner_or_admin(me.id, me)  # the column holds a UUID, not a str
        with self.assertRaises(HTTPException):
            sq._ensure_owner_or_admin(uuid.uuid4(), me)

    def test_list_returns_only_own_rows_for_students(self):
        me = SimpleNamespace(id=uuid.uuid4(), role="STUDENT")
        rows = [SimpleNamespace(user_id=me.id), SimpleNamespace(user_id=uuid.uuid4())]
        with mock.patch.object(sq, "StudentQuizService") as svc:
            svc.return_value.get_all.return_value = rows
            self.assertEqual(sq.get_all(db=None, current_user=me), rows[:1])


if __name__ == "__main__":
    unittest.main()
