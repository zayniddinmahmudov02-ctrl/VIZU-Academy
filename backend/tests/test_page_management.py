import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi import HTTPException

from app.api.admin.page_management_router import _page_or_404, router
from app.api.dependencies.auth import require_super_admin
from app.models.managed_page import ManagedPageAudit
from app.models.user import User
from app.services.page_management import PAGE_BY_ROUTE, PAGE_CATALOG, save_page_action, transition_page_state


class TestManagedPageCatalog(unittest.TestCase):
    def test_registered_routes_are_unique_and_resolve_to_app_router_files(self):
        routes = [page.route for page in PAGE_CATALOG]
        self.assertEqual(len(routes), len(set(routes)))
        repository = Path(__file__).resolve().parents[2]
        admin_root = repository / "frontend" / "src" / "app" / "admin"
        actual_routes = set()
        for page_file in admin_root.rglob("page.tsx"):
            relative = page_file.parent.relative_to(admin_root)
            suffix = "" if str(relative) == "." else "/" + str(relative).replace("\\", "/")
            actual_routes.add(f"/admin{suffix}")
        self.assertEqual(actual_routes, set(routes))
        for page in PAGE_CATALOG:
            self.assertTrue((repository / page.component).is_file(), page.route)

    def test_all_registered_code_routes_are_non_deletable(self):
        self.assertTrue(PAGE_CATALOG)
        self.assertTrue(all(not page.protected or page.page_type == "SYSTEM_PAGE" for page in PAGE_CATALOG))
        self.assertTrue(all(page.route in PAGE_BY_ROUTE for page in PAGE_CATALOG))
        self.assertFalse(any("DELETE" in route.methods for route in router.routes))

    def test_unknown_page_id_returns_not_found(self):
        with self.assertRaises(HTTPException) as error:
            _page_or_404("admin.not-a-real-page")
        self.assertEqual(error.exception.status_code, 404)


class TestManagedPageStateTransitions(unittest.TestCase):
    def test_remove_from_navigation_does_not_hide_or_archive_the_route(self):
        page = PAGE_BY_ROUTE["/admin/media-management"]
        result = transition_page_state(
            page,
            {"navigation_enabled": True, "is_hidden": False, "is_archived": False},
            "navigation",
            False,
        )
        self.assertEqual(result, {"navigation_enabled": False, "is_hidden": False, "is_archived": False})

    def test_hide_and_show_do_not_change_navigation_setting_or_route(self):
        page = PAGE_BY_ROUTE["/admin/media-management"]
        initial = {"navigation_enabled": True, "is_hidden": False, "is_archived": False}
        hidden = transition_page_state(page, initial, "visibility", True)
        restored = transition_page_state(page, hidden, "visibility", False)
        self.assertTrue(hidden["navigation_enabled"])
        self.assertTrue(hidden["is_hidden"])
        self.assertEqual(restored, initial)

    def test_archive_and_restore_preserve_previous_navigation_and_visibility(self):
        page = PAGE_BY_ROUTE["/admin/media-management"]
        initial = {"navigation_enabled": False, "is_hidden": True, "is_archived": False}
        archived = transition_page_state(page, initial, "archive")
        restored = transition_page_state(page, archived, "restore")
        self.assertTrue(archived["is_archived"])
        self.assertEqual(restored, initial)

    def test_protected_system_routes_cannot_be_hidden_archived_or_removed(self):
        for route in ("/admin", "/admin/settings", "/admin/page-management"):
            page = PAGE_BY_ROUTE[route]
            with self.subTest(route=route):
                with self.assertRaises(ValueError):
                    transition_page_state(
                        page,
                        {"navigation_enabled": True, "is_hidden": False, "is_archived": False},
                        "navigation",
                        False,
                    )
                with self.assertRaises(ValueError):
                    transition_page_state(
                        page,
                        {"navigation_enabled": True, "is_hidden": False, "is_archived": False},
                        "visibility",
                        True,
                    )
                with self.assertRaises(ValueError):
                    transition_page_state(
                        page,
                        {"navigation_enabled": True, "is_hidden": False, "is_archived": False},
                        "archive",
                    )

    def test_page_without_menu_entry_cannot_be_removed_from_navigation(self):
        page = PAGE_BY_ROUTE["/admin/languages/new"]
        with self.assertRaises(ValueError):
            transition_page_state(
                page,
                {"navigation_enabled": True, "is_hidden": False, "is_archived": False},
                "navigation",
                False,
            )


class TestPageManagementAudit(unittest.TestCase):
    def test_every_state_change_records_actor_and_before_after_state(self):
        page = PAGE_BY_ROUTE["/admin/media-management"]
        actor_id = uuid4()
        control = SimpleNamespace(
            id=uuid4(),
            route=page.route,
            navigation_enabled=True,
            is_hidden=False,
            is_archived=False,
            updated_by_id=None,
            updated_by=None,
            reason=None,
        )
        db = MagicMock()
        db.scalar.return_value = control
        actor = MagicMock(spec=User)
        actor.id = actor_id

        result = save_page_action(db, page, actor, "navigation", enabled=False, reason="Temporarily unused")

        self.assertIs(result, control)
        self.assertFalse(control.navigation_enabled)
        audit = next(call.args[0] for call in db.add.call_args_list if isinstance(call.args[0], ManagedPageAudit))
        self.assertEqual(audit.route, page.route)
        self.assertEqual(audit.actor_id, actor_id)
        self.assertEqual(audit.action, "navigation")
        self.assertEqual(audit.previous_state, {"navigation_enabled": True, "is_hidden": False, "is_archived": False})
        self.assertEqual(audit.new_state, {"navigation_enabled": False, "is_hidden": False, "is_archived": False})
        self.assertEqual(audit.reason, "Temporarily unused")
        db.commit.assert_called_once()


class TestPageManagementAuthorization(unittest.TestCase):
    def test_every_page_management_endpoint_requires_super_admin(self):
        for route in router.routes:
            self.assertTrue(route.dependant.dependencies, route.path)
            self.assertTrue(
                any(dependency.call is require_super_admin for dependency in route.dependant.dependencies),
                route.path,
            )

    def test_non_super_admin_cannot_access_page_management(self):
        user = MagicMock(spec=User)
        user.role = "ADMIN"
        with self.assertRaises(HTTPException) as error:
            asyncio.run(require_super_admin(current_user=user))
        self.assertEqual(error.exception.status_code, 403)

    def test_super_admin_can_access_page_management(self):
        user = MagicMock(spec=User)
        user.role = "SUPER_ADMIN"
        self.assertIs(asyncio.run(require_super_admin(current_user=user)), user)


if __name__ == "__main__":
    unittest.main()
