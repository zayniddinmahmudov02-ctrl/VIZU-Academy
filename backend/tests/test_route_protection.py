"""Every API endpoint needs an auth dependency unless it is on the explicit,
reviewed allowlist below — a new endpoint without authentication fails
this test instead of silently shipping as public."""

import unittest

from fastapi.routing import APIRoute

from app.api.dependencies import auth as auth_deps
from app.main import app

AUTH_FUNCS = {
    getattr(auth_deps, name)
    for name in dir(auth_deps)
    if callable(getattr(auth_deps, name)) and (name.startswith("get_current") or name.startswith("require_"))
}

# Public by design (reviewed 2026-10-08). Paths relative to the router mount.
PUBLIC_ALLOWLIST = {
    ("GET", "/"),
    ("GET", "/health"),
    # authentication itself
    ("POST", "/auth/login"),
    ("POST", "/auth/register"),
    ("POST", "/auth/refresh"),
    ("POST", "/auth/logout"),
    ("POST", "/auth/telegram"),
    # public certificate verification (QR / link on the certificate)
    ("GET", "/certificates/verify/{verification_code}"),
    # tracking redirect opened by the browser (no Authorization header possible)
    ("GET", "/advertisements/{advertisement_id}/click"),
    # authorised by its own short-lived signed stream token
    ("GET", "/videos/{video_id}/stream"),
    # catalogue metadata (titles / levels / covers) — content itself is gated
    ("GET", "/courses/"),
    ("GET", "/courses/{course_id}"),
    ("GET", "/modules"),
    ("GET", "/modules/{module_id}"),
    ("GET", "/books"),
    ("GET", "/languages/"),
    ("GET", "/languages/{language_id}"),
    ("GET", "/exam-providers"),
    ("GET", "/mock-exam/public/levels"),
    ("GET", "/mock-exam/public/providers"),
    ("GET", "/public/model-tests/{model_test_id}/assessment"),
    ("GET", "/vizu-pay/offers"),
    ("GET", "/vizu-pay/plans"),
    ("GET", "/vizu-pay/payment-cards"),
}


def _guarded(dependant) -> bool:
    return any(d.call in AUTH_FUNCS or _guarded(d) for d in dependant.dependencies)


def _router_guarded(router) -> bool:
    return any(getattr(d, "dependency", None) in AUTH_FUNCS for d in (getattr(router, "dependencies", None) or []))


def _walk(routes, inherited=False):
    for route in routes:
        if isinstance(route, APIRoute):
            yield route, inherited
        elif type(route).__name__ == "_IncludedRouter":  # FastAPI >= 0.120
            yield from _walk(route.original_router.routes, inherited or _router_guarded(route.original_router))
        else:
            sub = getattr(route, "routes", None)
            if sub:
                yield from _walk(sub, inherited)


class TestRouteProtection(unittest.TestCase):
    def test_only_allowlisted_endpoints_are_public(self):
        public = set()
        for route, inherited in _walk(app.routes):
            if inherited or _guarded(route.dependant):
                continue
            for method in route.methods:
                public.add((method, route.path))
        self.assertEqual(public - PUBLIC_ALLOWLIST, set(), "endpoints without authentication")

    def test_unscoped_homework_and_quiz_reads_are_admin_only(self):
        targets = {("GET", "/homeworks"), ("GET", "/homeworks/{item_id}"), ("GET", "/quizzes"), ("GET", "/quizzes/{quiz_id}")}
        found = {}
        for route, _ in _walk(app.routes):
            for method in route.methods:
                if (method, route.path) in targets:
                    found[(method, route.path)] = any(d.call is auth_deps.require_admin_panel_access for d in route.dependant.dependencies)
        self.assertEqual(set(found), targets)
        self.assertTrue(all(found.values()), found)


if __name__ == "__main__":
    unittest.main()
