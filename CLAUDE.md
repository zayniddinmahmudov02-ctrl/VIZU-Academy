# VIZU-DEUTSCH (VIZU Academy)

German-learning platform for Uzbek learners: A1–C1 course LMS, VIZU-Multilevel level test,
Vorbereitung mock exams, VIZU Pay, groups/classroom, Global Chat. Site <https://vizu-deutsch.com>.
Users and docs are mostly Uzbek; the admin UI is German.

## Stack

- **Backend** `backend/`: FastAPI, SQLAlchemy 2, Alembic, PostgreSQL (psycopg 3), Pydantic v2.
- **Frontend** `frontend/`: Next.js 16.2 (App Router, Turbopack), React 19.2, TanStack Query, zustand,
  Tailwind 4, axios. Read `frontend/AGENTS.md` first: this Next.js has breaking changes.
- **E2E** `e2e/`: Playwright (Chrome, desktop + Pixel 7), against a local stack only.
- **Production**: `217.76.62.208:/opt/vizu/VIZU-Academy`, systemd `vizu-backend` / `vizu-frontend`.

## Layout (where to look first)

| Path | What |
| --- | --- |
| `backend/app/api/<module>/router.py` | HTTP endpoints. Every router is mounted bare and under `/api/v1` (`app/main.py`) |
| `backend/app/services/<module>/` | business logic |
| `backend/app/models/` | SQLAlchemy models (one file per table group) |
| `backend/alembic/versions/` | migrations (linear, one head) |
| `backend/app/scripts/` | one-off/data scripts: `python -m app.scripts.<name>`, dry-run by default |
| `backend/tests/` | unittest/pytest tests |
| `frontend/src/app/` | routes: `(auth)`, `(dashboard)` = student, `admin/`, `teacher/` |
| `frontend/src/features/<module>/` | services (API calls), hooks, components per feature |
| `frontend/src/components/` | shared UI, `lesson-player/`, `lms/`, `admin/` |
| `docs/` | audits and runbooks (Uzbek); `docs/ai-context/` = maps for Claude |

## How to load context (do this, not a repo scan)

1. Read this file. 2. Find the module in `docs/ai-context/module-registry.md`.
2. Read only that module entry plus the map you need (table below). 4. Open the source files it lists.
3. Look at other modules only on a direct dependency. Source code wins over any doc: if a doc is stale,
   fix the doc in the same task.

| Task | Read |
| --- | --- |
| Any feature / bug | `docs/ai-context/module-registry.md` (that module only) |
| Endpoint, URL, permission | `docs/ai-context/api-registry.md` |
| Table, migration, model | `docs/ai-context/database-map.md` + `.claude/rules/database.md` |
| Where is a backend / frontend file | `docs/ai-context/backend-map.md` / `frontend-map.md` |
| How the pieces fit | `docs/ai-context/architecture-map.md` |
| Deploy, server, rollback | skill `vizu-deploy` + `docs/ai-context/deployment-map.md` |
| What is open / broken | `docs/ai-context/known-issues.md`, `current-state.md` |
| What changed lately | `docs/ai-context/recent-changes.md` |

Skills (load only when the task matches): `vizu-lms` (courses, lessons, scoring, progress),
`vizu-admin` (admin panel, CMS, permissions), `vizu-media` (audio/video, uploads, transcripts),
`vizu-chat` (Global Chat), `vizu-deploy` (production).

## Token rules

1. No full-repo scans. Start from the module entry; search inside named folders only.
2. Never search `node_modules`, `.next*`, `.venv`, `venv`, `__pycache__`, `protected_storage`, `uploads`, logs.
3. Read large files in ranges (`offset`/`limit`) or grep first; don't re-read a file without a reason.
4. Show only failures and the final summary of test runs and long commands.
5. Small task, small context; split big tasks by module.
6. Keep docs short: paths and decisions, no code copies, no fact in two places.
7. Never skip security checks, migration review or the tests a change needs to save tokens.

## Commands

Test commands, the local test database and the env vars it needs are in `.claude/rules/testing.md`.
Frontend: `npx tsc --noEmit`, `npx eslint <files>`, `npm run test:unit`. Never run `npm run build` into
`.next-a`/`.next-b` locally: use `NEXT_DIST_DIR=.next-e2e` and restore `tsconfig.json` afterwards.

## Production (summary — details in skill `vizu-deploy`)

Routine deploys are done without asking at each step. Always: backup with a restore check first,
review the migration SQL offline, backend restart + health check, frontend only through
`frontend/scripts/deploy-frontend.sh` (slots `.next-a`/`.next-b`), smoke tests, logs.
Never: automatic DB downgrade, deleting data or files without a verified backup, touching the Telegram
bots (`nano_bot`, `telegram-cours2026`), their code, DBs or services.

## Security (always)

- Never print or store secrets: `.env` values, DB password, `SECRET_KEY`, bot tokens, API keys, SSH keys.
  Docs name settings, never values. No personal data of users in docs or logs.
- Every lesson-content endpoint goes through `require_lesson_access`; admin endpoints through
  `require_admin_panel_access` (read) / `require_content_editor` (write) / `require_super_admin`.
- Answer keys are never sent to students before grading; audio/video are private (no public URL).
- No fake payments, no invented prices (price source: `backend/app/services/vizu_pay/offers.py`).
- Do not create test users, tokens or audio on production.

## Git

`git` is not on PATH; use GitHub Desktop's bundled one (`app-*\resources\app\git\cmd\git.exe`; the folder changes
on updates). 2026-11-05 (later): `app-3.6.10` has no `git.exe` any more; use
`C:\Users\user\AppData\Local\GitHubDesktop\app-3.6.7\resources\app\git\cmd\git.exe` (also the one whose `push` works
non-interactively). If no `app-*` has git, the owner pushes from GitHub Desktop.
Temp / caches live on D: (user env `CLAUDE_CODE_TMPDIR`, `TEMP`, `TMP`, `PIP_CACHE_DIR`, `PLAYWRIGHT_BROWSERS_PATH`,
npm `cache` → `D:\vz_tmp\…`); write large outputs to `D:\vz_tmp\work\`.
Repo files use CRLF; some files have a UTF-8 BOM: keep each file's style. The server checkout uses LF.

## After every task

Update only the knowledge that changed: the module entry, the API/DB map if endpoints/tables changed,
`docs/ai-context/recent-changes.md` (newest first, keep about 15 entries) and `current-state.md`.
