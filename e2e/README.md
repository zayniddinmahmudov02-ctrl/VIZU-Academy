# VIZU e2e (Playwright)

Browser tests for the welcome/login/register/help pages, remember me,
logout, Settings (former Profile) and the admin sidebar. This is a separate
package, so the production install of `frontend/` stays unchanged. It uses
the installed Google Chrome (`channel: "chrome"`), so there is no browser
download.

**Never point it at production.** It registers users.

```powershell
# 1. throwaway database (local test cluster on :54329)
psql -h localhost -p 54329 -U postgres -c "create database vizu_auth_e2e"
cd backend
$env:DATABASE_PORT="54329"; $env:DATABASE_NAME="vizu_auth_e2e"
python -m alembic upgrade head
# a SUPER_ADMIN e2e-admin@example.com / AdminE2E123 must exist in that DB
$env:SUPER_ADMIN_VERIFICATION_PASSWORD="e2e-admin-check"
python -m uvicorn app.main:app --port 8000

# 2. frontend built with NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
cd frontend; npx next build; npx next start -p 3000

# 3. tests
cd e2e; npm install; npx playwright test
# optional review screenshots into e2e/shots/
$env:E2E_SHOTS="1"; npx playwright test tests/screenshots.spec.ts
```

The backend HTTP flow test with the same database:
`VIZU_AUTH_FLOW_URL=http://127.0.0.1:8000 python -m unittest tests.test_auth_session_flow`
