---
paths:
  - "backend/tests/**"
  - "frontend/tests/**"
  - "e2e/**"
---
# Testing rules

Show only failures and the final summary line. Old failures are not new failures: compare with the
previous run before reporting.

## Backend (local, Windows PowerShell)
- Python: `D:\vz_tmp\venv\Scripts\python.exe`. Env helper (DB vars, `SECRET_KEY`, `APP_ENV=test`,
  `VIZU_WB_TEST_DB_URL`): `scratchpad\env.ps1` of the session or set them by hand — never real secrets.
- Test PostgreSQL 18 cluster `D:\vz_tmp\pgtest2` on port 54329 (trust auth), normally stopped; `pg_ctl` is not
  on PATH: `& "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" -D D:\vz_tmp\pgtest2 -o "-p 54329 -c listen_addresses=127.0.0.1" -l D:\vz_tmp\pgtest2.log start`
  (start it in its own command: pg_ctl keeps the pipe open). Stop it afterwards.
- DBs: `vizu_gcr_test` (integration, `VIZU_WB_TEST_DB_URL`), `vizu_gcr_mig` (migration tests,
  `VIZU_MIGRATION_TEST_DB_URL`), `vizu_gcr_e2e` (E2E stack). Migrate with `python -m alembic upgrade head`.
- Run: `cd backend; New-Item -ItemType Directory uploads -Force; python -m pytest -q -p no:cacheprovider tests`
  then remove the empty `uploads/`. Integration tests skip without the DB URL; HTTP tests skip without httpx.
- Last full run 2026-10-30: 917 passed, 17 skipped.

## Frontend
`npx tsc --noEmit -p tsconfig.json`, `npx eslint <changed files>`, `npm run test:unit`.
Full `npx eslint .` has 9 errors / 10 warnings in untouched files (known, not yours).

## E2E (local stack only, never production)
Backend: uvicorn on :8000 with `DATABASE_NAME=vizu_gcr_e2e`, `SUPER_ADMIN_VERIFICATION_PASSWORD` = the local test value `ADMIN.verify` from `e2e/tests/helpers.ts`.
Frontend: `NEXT_DIST_DIR=.next-e2e NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npx next build` (back up and
restore `tsconfig.json`), `npx next start -p 3000`. Seeds live outside the repo in `D:\vz_tmp\work\`
(`gcr_e2e_seed.py`, `a2l4_e2e_seed.py`, `a2p_local_setup.py`). Run `cd e2e; npx playwright test tests/<spec>`.
Clean up: stop :8000/:3000, delete `.next-e2e`.

## Server
`cd /opt/vizu/VIZU-Academy/backend; .venv/bin/python -m unittest tests.<module> …` — DB tests skip there,
httpx/httpx2 is not installed (do not install it for tests).
