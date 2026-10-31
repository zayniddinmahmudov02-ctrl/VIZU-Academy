---
name: vizu-admin
description: VIZU admin panel and CMS — admin pages under frontend/src/app/admin, admin APIs (/admin/*), roles and permissions, page management, users, notifications, support, Angebote/VIZU Pay admin, teacher assignments. Use when adding or changing an admin page, an admin endpoint or a permission.
---
# VIZU Admin

## Context to load
1. `docs/ai-context/module-registry.md` → "Admin CMS" and the business module of the page.
2. `docs/ai-context/api-registry.md` → the `/admin/...` prefix and its dependency.
3. Source: `frontend/src/app/admin/<page>/page.tsx` → its client component in
   `frontend/src/features/admin/components/<area>/` → service in `frontend/src/features/admin/services/`
   → backend router `backend/app/api/admin/*_router.py` or `backend/app/api/<module>/admin_router.py`.

## Rules
- Permissions: read = `require_admin_panel_access` (all staff incl. TEACHER/SUPPORT), write =
  `require_content_editor`, money/irreversible = `require_super_admin`; teacher area =
  `require_teacher_panel_access`. Roles in `backend/app/core/security/roles.py`.
- Admin login needs the second factor `SUPER_ADMIN_VERIFICATION_PASSWORD` (name only; see
  `docs/super-admin-verification-secret.md`).
- Every new `page.tsx` must be listed in `backend/app/services/page_management.py`
  (`tests/test_page_management.py`).
- Admin UI: German labels, `@/components/admin/admin-ui`, `ConfirmDialog` for destructive actions,
  `data-testid` for E2E, works on mobile.
- Write an audit entry (`app.core.audit.write_audit`) for every admin write that changes content or money.

## Tests
Backend: the module's tests + a 401/403 case. Frontend: `tsc`, `eslint <files>`; E2E `e2e/tests/admin.spec.ts`
or the feature spec. Then update the module entry + `recent-changes.md`.
