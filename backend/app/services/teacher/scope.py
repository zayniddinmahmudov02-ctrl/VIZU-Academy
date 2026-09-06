from app.core.security.roles import UserRole
from app.models.user import User
from app.repositories.teacher_assignment import TeacherAssignmentRepository


def teacher_course_ids_or_none(db, user: User) -> list[str] | None:
    """The scoping rule shared by every "staff can review this" check that
    now also has to account for TEACHER being a real, narrower role
    (ADMIN_PANEL_ROLES has always included TEACHER — see
    app/core/security/roles.py — but until the Teacher Panel existed,
    nobody with that role ever actually called these endpoints).

    Returns None for every OTHER admin-panel role (SUPER_ADMIN, ADMIN,
    CONTENT_MANAGER, PAYMENT_MANAGER, SUPPORT) — "no restriction," their
    existing unscoped behavior is completely unchanged. Returns a course-id
    list (possibly empty) ONLY for TEACHER — callers must treat that as
    "restrict to exactly these courses," never as "no restriction."
    """
    if user.role != UserRole.TEACHER:
        return None
    return [str(c) for c in TeacherAssignmentRepository(db).course_ids_for_teacher(user.id)]
