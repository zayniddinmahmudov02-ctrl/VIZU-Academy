"""Concurrent competency visits against PostgreSQL (set VIZU_WB_TEST_DB_URL to a
migrated test database).

Production logged ~50 HTTP 500s in two days on
POST /lms/lessons/{id}/competencies/{kind}/visit: two requests for the same
student + lesson both found no snapshot row and both inserted one
(uq_student_competency_progress). Visits and snapshot syncs are now
serialised per (student, lesson)."""

import os
import threading
import unittest
import uuid

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
THREADS = 8


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestConcurrentVisits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.models.course import Course
        from app.models.language import Language
        from app.models.lesson import Lesson
        from app.models.module import Module
        from app.models.user import User

        cls.engine = create_engine(DB_URL, pool_size=THREADS + 2)
        cls.Session = sessionmaker(bind=cls.engine, expire_on_commit=False)
        db = cls.Session()
        tag = uuid.uuid4().hex[:6]
        user = User(email=f"race-{tag}@test.local", username=f"race_{tag}", password_hash="x", is_active=True, is_verified=True,
                    is_superuser=False, role="STUDENT", is_banned=False, preferred_language="uz", first_name="race")
        lang = Language(code=f"r{tag}", locale=f"r-{tag}", name=f"Race {tag}")
        db.add_all([user, lang])
        db.flush()
        course = Course(language_id=lang.id, level="A1", title=f"A1 race {tag}", order_index=1, is_active=True)
        db.add(course)
        db.flush()
        module = Module(course_id=course.id, number=1, title="Modul 1", order_index=1, is_active=True)
        db.add(module)
        db.flush()
        lesson = Lesson(module_id=module.id, number=1, title="Lektion 1", duration=10, is_published=True)
        db.add(lesson)
        db.commit()
        cls.user_id, cls.lesson_id = user.id, lesson.id
        db.close()

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def _race(self, target):
        barrier = threading.Barrier(THREADS)
        errors = []

        def run(i):
            db = self.Session()
            try:
                barrier.wait()
                target(db, i)
            except Exception as exc:  # noqa: BLE001 - every failure is the finding
                errors.append(f"{type(exc).__name__}: {str(exc).splitlines()[0]}")
                db.rollback()
            finally:
                db.close()

        threads = [threading.Thread(target=run, args=(i,)) for i in range(THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(30)
        return errors

    def _rows(self, kind=None):
        from sqlalchemy import func, select

        from app.models.lms import StudentCompetencyProgress

        db = self.Session()
        try:
            q = select(func.count()).select_from(StudentCompetencyProgress).where(
                StudentCompetencyProgress.user_id == self.user_id, StudentCompetencyProgress.lesson_id == self.lesson_id)
            if kind:
                q = q.where(StudentCompetencyProgress.competency == kind)
            return db.scalar(q)
        finally:
            db.close()

    def _visit(self, kind_for):
        from app.models.lesson import Lesson
        from app.models.user import User
        from app.services.lms import progress

        def target(db, i):
            progress.record_visit(db, db.get(User, self.user_id), db.get(Lesson, self.lesson_id), kind_for(i))
        return target

    def test_same_competency_opened_twice_at_once(self):
        errors = self._race(self._visit(lambda i: "EINFUEHRUNG"))
        self.assertEqual(errors, [])
        self.assertEqual(self._rows("EINFUEHRUNG"), 1)

    def test_different_competencies_of_one_lesson_at_once(self):
        kinds = ["LESEN", "HOEREN", "GRAMMATIK", "WORTSCHATZ"]
        errors = self._race(self._visit(lambda i: kinds[i % len(kinds)]))
        self.assertEqual(errors, [])
        for kind in kinds:
            self.assertEqual(self._rows(kind), 1, kind)


if __name__ == "__main__":
    unittest.main()
