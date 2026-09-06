from uuid import UUID

from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.student_progress import StudentProgress
from app.models.user import User
from app.repositories.teacher_assignment import TeacherAssignmentRepository
from app.schemas.teacher import TeacherOverview, TeacherStudent


def _display_name(user: User) -> str:
    parts = [p for p in (user.first_name, user.last_name) if p]
    return " ".join(parts) if parts else user.username


class TeacherService:
    """Read-only, scoped to the CURRENT teacher's assigned courses (see
    app/models/teacher_assignment.py) — a teacher with no assignment rows
    sees zero students, never every student in the system. A SUPER_ADMIN
    reaching these same /teacher/* endpoints via the panel switcher is
    scoped identically (whatever courses THEY happen to be assigned to,
    same as any other teacher) — Admin Panel already covers the
    "see everything" view, this one deliberately doesn't duplicate it.

    Course/lesson/user id columns are a long-standing mix of UUID-typed
    (Course.id, User.id, Lesson.id — see app/models/base.py) and
    str-typed FK columns (Enrollment.*, Module.course_id,
    StudentProgress.*) across this codebase (see the pre-existing
    "UUID/str schema" issue other services have already hit) — every
    value that crosses from a UUID-typed column into a filter against a
    str-typed one is explicitly str()-cast below so an `.in_()`/`==`
    never silently no-ops.
    """

    def __init__(self, db: Session):
        self.db = db
        self.assignments = TeacherAssignmentRepository(db)

    def _course_progress_percent(self, user_id: UUID, course_id: UUID) -> int:
        lesson_ids = [
            str(row[0])
            for row in (
                self.db.query(Lesson.id)
                .join(Module, Module.id == Lesson.module_id)
                .filter(Module.course_id == str(course_id))
                .all()
            )
        ]
        if not lesson_ids:
            return 0

        completed = (
            self.db.query(StudentProgress)
            .filter(
                StudentProgress.user_id == str(user_id),
                StudentProgress.lesson_id.in_(lesson_ids),
                StudentProgress.lesson_completed.is_(True),
            )
            .count()
        )
        return round((completed / len(lesson_ids)) * 100)

    def overview(self, teacher_id: UUID) -> TeacherOverview:
        course_ids = [str(c) for c in self.assignments.course_ids_for_teacher(teacher_id)]
        if not course_ids:
            return TeacherOverview(assigned_course_count=0, student_count=0)

        student_count = (
            self.db.query(Enrollment.user_id)
            .filter(Enrollment.course_id.in_(course_ids), Enrollment.is_active.is_(True))
            .distinct()
            .count()
        )
        return TeacherOverview(assigned_course_count=len(course_ids), student_count=student_count)

    def list_students(self, teacher_id: UUID) -> list[TeacherStudent]:
        course_ids = [str(c) for c in self.assignments.course_ids_for_teacher(teacher_id)]
        if not course_ids:
            return []

        rows = (
            self.db.query(Enrollment, User, Course)
            .join(User, User.id == Enrollment.user_id)
            .join(Course, Course.id == Enrollment.course_id)
            .filter(Enrollment.course_id.in_(course_ids), Enrollment.is_active.is_(True))
            .order_by(Course.level, User.email)
            .all()
        )

        return [
            TeacherStudent(
                id=user.id,
                name=_display_name(user),
                email=user.email,
                course_title=course.title,
                course_level=course.level,
                progress=self._course_progress_percent(user.id, course.id),
            )
            for _enrollment, user, course in rows
        ]
