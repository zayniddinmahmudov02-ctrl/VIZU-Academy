from dataclasses import dataclass
from typing import Any

from sqlalchemy import exists, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session, joinedload

from app.models import Base
from app.models.managed_page import ManagedPage, ManagedPageAudit
from app.models.user import User


@dataclass(frozen=True)
class PageDefinition:
    route: str
    name: str
    module: str
    page_type: str
    component: str
    domains: tuple[str, ...]
    in_navigation: bool = False
    protected: bool = False

    @property
    def page_id(self) -> str:
        return self.route.strip("/").replace("/", ".").replace("[", "").replace("]", "")


_ROUTES = (
    ("/admin", "Dashboard", "System", "SYSTEM_PAGE", "dashboard", True, True),
    ("/admin/werbung-banner", "Werbung-Banner", "Marketing", "ADMIN_PAGE", "advertisements", True, False),
    ("/admin/support", "Support / Hilfeanfragen", "Support", "ADMIN_PAGE", "support", True, False),
    ("/admin/languages", "Languages", "Languages", "ADMIN_PAGE", "languages", True, False),
    ("/admin/languages/new", "Create language", "Languages", "ADMIN_PAGE", "languages", False, False),
    ("/admin/languages/[id]/dashboard", "Language dashboard", "Languages", "ADMIN_PAGE", "languages", False, False),
    ("/admin/languages/[id]/edit", "Edit language", "Languages", "ADMIN_PAGE", "languages", False, False),
    ("/admin/languages/[id]/learners", "Language learners", "Languages", "ADMIN_PAGE", "languages", False, False),
    ("/admin/languages/[id]/settings", "Language settings", "Languages", "ADMIN_PAGE", "languages", False, False),
    ("/admin/kurse", "Kurse (LMS)", "Courses", "LMS_PAGE", "lms", True, False),
    ("/admin/kurse/[level]", "Course level", "Courses", "LMS_PAGE", "lms", False, False),
    ("/admin/kurse/lektion/[lessonId]", "Course lesson", "Courses", "LMS_PAGE", "lms", False, False),
    ("/admin/lms", "LMS A1–C1", "LMS content", "LMS_PAGE", "lms", True, False),
    ("/admin/lms/[courseId]", "LMS course editor", "LMS content", "LMS_PAGE", "lms", False, False),
    ("/admin/lms/import", "LMS import", "LMS content", "LMS_PAGE", "lms", False, False),
    ("/admin/lms/loesung", "Lösung", "LMS content", "LMS_PAGE", "lms", True, False),
    ("/admin/lms/loesung/[kind]/[id]", "Answer-key editor", "LMS content", "LMS_PAGE", "lms", False, False),
    ("/admin/lessons", "Lessons", "LMS content", "LMS_PAGE", "lms", False, False),
    ("/admin/lessons/[lessonId]", "Lesson editor", "LMS content", "LMS_PAGE", "lms", False, False),
    ("/admin/listening", "Listening", "LMS content", "LMS_PAGE", "lms", False, False),
    ("/admin/media-management", "Media Management", "Media", "ADMIN_PAGE", "media", True, False),
    ("/admin/media-management/hoeren-a1", "A1 Hören", "Media", "LMS_PAGE", "media", False, False),
    ("/admin/media-management/a2/lesson-4/hoeren", "A2 4. Unterricht Hören", "Media", "LMS_PAGE", "media", False, False),
    ("/admin/mock-exams", "Vorbereitung", "Mock exams", "ADMIN_PAGE", "mock_exams", True, False),
    ("/admin/mock-exams/[providerId]", "Mock exam provider", "Mock exams", "ADMIN_PAGE", "mock_exams", False, False),
    ("/admin/mock-exams/[providerId]/[levelId]", "Mock exam level", "Mock exams", "ADMIN_PAGE", "mock_exams", False, False),
    ("/admin/mock-exams/[providerId]/[levelId]/[modelTestId]", "Mock exam editor", "Mock exams", "ADMIN_PAGE", "mock_exams", False, False),
    ("/admin/mock-exams/analytics", "Mock exam analytics", "Mock exams", "ADMIN_PAGE", "mock_exams", False, False),
    ("/admin/vizu-multilevel", "VIZU-Multilevel", "Exams", "ADMIN_PAGE", "exams", True, False),
    ("/admin/users", "Users", "Users", "ADMIN_PAGE", "users", True, False),
    ("/admin/team", "Team", "Users", "ADMIN_PAGE", "users", True, False),
    ("/admin/teacher-assignments", "Lehrer-Zuweisungen", "Teachers", "ADMIN_PAGE", "users", True, False),
    ("/admin/premium-users", "Premium-Users", "Payments", "ADMIN_PAGE", "payments", True, False),
    ("/admin/certificates", "Zertifikate", "Certificates", "ADMIN_PAGE", "certificates", True, False),
    ("/admin/certificates/[userId]", "Certificate details", "Certificates", "ADMIN_PAGE", "certificates", False, False),
    ("/admin/achievements", "Achievements / Medals", "Achievements", "ADMIN_PAGE", "achievements", True, False),
    ("/admin/books", "Bücher", "Books", "ADMIN_PAGE", "books", True, False),
    ("/admin/payments", "Payments", "Payments", "ADMIN_PAGE", "payments", True, False),
    ("/admin/angebote", "Angebote & Preise", "Payments", "ADMIN_PAGE", "payments", True, False),
    ("/admin/analytics", "Analytics", "Analytics", "ADMIN_PAGE", "analytics", True, False),
    ("/admin/settings", "Settings", "System", "SYSTEM_PAGE", "settings", True, True),
    ("/admin/page-management", "Page Management", "System", "SYSTEM_PAGE", "settings", True, True),
    ("/admin/levels", "Levels", "LMS content", "LMS_PAGE", "lms", False, False),
    ("/admin/modules", "Modules", "LMS content", "LMS_PAGE", "lms", False, False),
    ("/admin/media", "Media library", "Media", "ADMIN_PAGE", "media", False, False),
    ("/admin/writing", "Writing", "LMS content", "LMS_PAGE", "lms", False, False),
    ("/admin/speaking", "Speaking", "LMS content", "LMS_PAGE", "lms", False, False),
    ("/admin/notifications", "Notifications", "Notifications", "ADMIN_PAGE", "notifications", True, False),
    ("/admin/global-chat", "Global Chat", "Community", "ADMIN_PAGE", "global_chat", True, False),
    ("/admin/groups", "Gruppen / Guruhlar", "Community", "ADMIN_PAGE", "groups", True, False),
)

_DOMAIN_TABLES: dict[str, tuple[tuple[str, str], ...]] = {
    "dashboard": (
        ("Users", "users"), ("Courses", "courses"), ("Lessons", "lessons"),
        ("Learning progress", "student_progress"), ("Orders", "subscription_orders"),
    ),
    "advertisements": (("Advertisements", "advertisements"), ("Advertisement events", "advertisement_events")),
    "notifications": (("Broadcast notifications", "broadcast_notifications"), ("Notifications", "notifications")),
    "support": (("Support tickets", "support_tickets"), ("Support messages", "support_messages")),
    "global_chat": (
        ("Global chat messages", "global_chat_messages"), ("Mutes / bans", "global_chat_restrictions"),
        ("Moderation log", "global_chat_moderation_actions"),
    ),
    "groups": (
        ("Study groups", "study_groups"), ("Group members", "study_group_members"),
        ("Group messages", "study_group_messages"), ("Group audit log", "study_group_audit_logs"),
    ),
    "languages": (("Languages", "languages"), ("User language enrollments", "user_languages"), ("Language settings", "language_settings")),
    "lms": (
        ("Courses", "courses"), ("Modules", "modules"), ("Lessons", "lessons"),
        ("Enrollments", "enrollments"), ("Learning resources", "learning_resources"),
        ("Competency progress", "student_competency_progress"), ("Listening tasks", "listenings"),
    ),
    "media": (
        ("Videos", "videos"), ("Listening tasks", "listenings"),
        ("Audio archives", "listening_audio_archives"), ("Media library assets", "media_assets"),
    ),
    "mock_exams": (
        ("Model tests", "model_tests"), ("Questions", "mock_questions"),
        ("Attempts", "mock_test_attempts"), ("Providers", "certification_providers"),
    ),
    "exams": (
        ("Exam providers", "exam_providers"), ("Exams", "exams"),
        ("Exam sessions", "exam_sessions"), ("Assessment attempts", "assessment_attempts"),
    ),
    "users": (("Users", "users"), ("Login history", "login_history"), ("Teacher assignments", "teacher_assignments")),
    "payments": (
        ("Orders", "subscription_orders"), ("Promo codes", "promo_codes"),
        ("Promo redemptions", "promo_code_redemptions"), ("Payments", "payments"),
    ),
    "certificates": (("Certificates", "certificates"),),
    "achievements": (("Achievements", "achievements"), ("User achievements", "user_achievements")),
    "books": (("Books", "books"),),
    "analytics": (
        ("Users", "users"), ("Courses", "courses"), ("Learning progress", "student_progress"),
        ("Orders", "subscription_orders"), ("Exam attempts", "assessment_attempts"),
    ),
    "settings": (("Application settings", "app_settings"),),
}

PAGE_CATALOG = tuple(
    PageDefinition(
        route=route,
        name=name,
        module=module,
        page_type=page_type,
        component=f"frontend/src/app{route}/page.tsx".replace("[", "[").replace("]", "]"),
        domains=_DOMAIN_TABLES[domain],
        in_navigation=in_navigation,
        protected=protected,
    )
    for route, name, module, page_type, domain, in_navigation, protected in _ROUTES
)
PAGE_BY_ROUTE = {page.route: page for page in PAGE_CATALOG}
PAGE_BY_ID = {page.page_id: page for page in PAGE_CATALOG}


def page_state(page: PageDefinition, control: ManagedPage | None) -> dict[str, Any]:
    navigation_enabled = control.navigation_enabled if control else page.in_navigation
    hidden = control.is_hidden if control else False
    archived = control.is_archived if control else False
    status = "archived" if archived else "hidden" if hidden else "active" if navigation_enabled else "removed"
    return {
        "navigation_enabled": navigation_enabled,
        "is_hidden": hidden,
        "is_archived": archived,
        "navigation_visible": navigation_enabled and not hidden and not archived,
        "status": status,
        "reason": control.reason if control else None,
        "updated_at": control.updated_at if control else None,
        "updated_by": (
            {"id": str(control.updated_by.id), "name": control.updated_by.username}
            if control and control.updated_by else None
        ),
    }


def list_pages(db: Session) -> list[dict[str, Any]]:
    controls = {
        row.route: row
        for row in db.scalars(select(ManagedPage).options(joinedload(ManagedPage.updated_by))).all()
    }
    table_names = {
        table_name
        for page in PAGE_CATALOG
        for _, table_name in page.domains
        if table_name in Base.metadata.tables
    }
    presence = {
        table_name: bool(db.scalar(select(exists().select_from(Base.metadata.tables[table_name]))))
        for table_name in table_names
    }
    result = []
    for page in PAGE_CATALOG:
        related = [
            {"name": label, "exists": presence.get(table_name, False)}
            for label, table_name in page.domains
        ]
        control = controls.get(page.route)
        result.append({
            "page_id": page.page_id,
            "name": page.name,
            "route": page.route,
            "module": page.module,
            "page_type": page.page_type,
            **page_state(page, control),
            "allowed_roles": ["SUPER_ADMIN"],
            "in_navigation": page.in_navigation,
            "component": page.component,
            "related_data": related,
            "related_data_exists": any(row["exists"] for row in related),
            "can_delete": False,
            "delete_block_reason": "This is a code-managed Next.js route; remove it through reviewed repository changes and deployment.",
            "protected": page.protected,
        })
    return result


def navigation_state(db: Session) -> dict[str, bool]:
    controls = {
        row.route: row
        for row in db.scalars(select(ManagedPage)).all()
    }
    return {
        page.route: page_state(page, controls.get(page.route))["navigation_visible"]
        for page in PAGE_CATALOG
        if page.in_navigation
    }


def ensure_locked_control(db: Session, route: str) -> ManagedPage:
    db.execute(
        pg_insert(ManagedPage)
        .values(route=route)
        .on_conflict_do_nothing(index_elements=["route"])
    )
    control = db.scalar(select(ManagedPage).where(ManagedPage.route == route).with_for_update())
    if control is None:
        raise RuntimeError(f"Failed to initialize page control for {route}")
    return control


def audit_state(control: ManagedPage, page: PageDefinition) -> dict[str, Any]:
    return {
        "navigation_enabled": control.navigation_enabled if control.id else page.in_navigation,
        "is_hidden": control.is_hidden if control.id else False,
        "is_archived": control.is_archived if control.id else False,
    }


def transition_page_state(
    page: PageDefinition,
    current: dict[str, bool],
    action: str,
    enabled: bool | None = None,
) -> dict[str, bool]:
    next_state = dict(current)
    if action == "navigation":
        if not page.in_navigation:
            raise ValueError("This page does not have a sidebar navigation item.")
        if page.protected and enabled is False:
            raise ValueError("This system page cannot be removed from navigation.")
        next_state["navigation_enabled"] = bool(enabled)
    elif action == "visibility":
        if page.protected and enabled is True:
            raise ValueError("This protected system page cannot be hidden.")
        next_state["is_hidden"] = bool(enabled)
    elif action == "archive":
        if page.protected:
            raise ValueError("This protected system page cannot be archived.")
        next_state["is_archived"] = True
    elif action == "restore":
        next_state["is_archived"] = False
    else:
        raise ValueError("Unsupported page management action.")
    return next_state


def save_page_action(
    db: Session,
    page: PageDefinition,
    actor: User,
    action: str,
    *,
    enabled: bool | None = None,
    reason: str | None = None,
) -> ManagedPage:
    control = ensure_locked_control(db, page.route)
    previous = audit_state(control, page)
    current = transition_page_state(page, previous, action, enabled)
    control.navigation_enabled = current["navigation_enabled"]
    control.is_hidden = current["is_hidden"]
    control.is_archived = current["is_archived"]
    cleaned_reason = reason.strip()[:500] if reason and reason.strip() else None
    if current != previous or cleaned_reason:
        control.updated_by_id = actor.id
        control.reason = cleaned_reason
        db.add(ManagedPageAudit(
            route=page.route,
            actor_id=actor.id,
            action=action,
            previous_state=previous,
            new_state=current,
            reason=cleaned_reason,
        ))
        db.commit()
        db.refresh(control)
    return control
