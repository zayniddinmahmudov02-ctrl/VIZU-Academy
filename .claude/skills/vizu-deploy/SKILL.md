---
name: vizu-deploy
description: VIZU production deploy to 217.76.62.208 — pre-checks, backup with restore check, git pull or staged overlay, Alembic migrations, backend restart, frontend slot deploy (.next-a/.next-b), smoke tests, logs, rollback. Use whenever something must go to production or the server must be inspected.
---
# VIZU Deploy

Facts: `docs/ai-context/deployment-map.md`. Hard rules: `.claude/rules/deployment.md`.

## How to run commands on the server
SSH as root with key `~/.ssh/claude_vizu_new` (BatchMode). From Windows PowerShell 5.1 send a script as
base64 *argument* (stdin gets a BOM): write the bash script locally, then
`ssh … "echo <b64> | base64 -d > /tmp/s.sh && bash /tmp/s.sh; rm -f /tmp/s.sh"`. Inside scripts read DB
settings with `.venv/bin/python -c 'from app.core.config import settings …'` into `PG*` env vars; never echo them.

## Procedure (routine deploys: no extra confirmation per step)
1. **Pre-check (read-only):** `git status --short`, `git fetch`, `git log HEAD..origin/main`, upstream files
   vs working tree, `alembic current`, `systemctl is-active vizu-backend vizu-frontend`, active slot
   (`frontend/.deploy/active.env`), free disk.
2. **Backup:** `/var/backups/vizu/pre-<topic>-<stamp>/`: `pg_dump -Fc` + `pg_restore --list`, restore into a
   scratch DB as `sudo -u postgres` and compare row counts of all tables, `lesson-listening.tar` + sha256
   list, audio metadata CSV, `SHA256SUMS` check. Failed → stop.
3. **Code:** `git pull --ff-only` (or LF-staged overlay checked against `HEAD`, see rules). Dependencies:
   only what `requirements.txt` needs (`pip install --dry-run` first), never bulk upgrades.
4. **Tests on server:** `.venv/bin/python -m unittest tests.<changed modules>`; `python -c "import app.main"`.
5. **Migrations:** expected current revision + one head, `alembic upgrade <cur>:head --sql` preview,
   `alembic upgrade head`.
6. **Backend:** `systemctl restart vizu-backend`, poll `http://127.0.0.1:8000/api/v1/health` until 200,
   `journalctl -u vizu-backend --since …` for errors.
7. **Data scripts** (if any): `plan` → read it → `apply --confirm <plan id>`; keep the JSON report in the backup dir.
8. **Frontend:** `cd frontend && bash scripts/deploy-frontend.sh` (builds the inactive slot, switches
   `active.env`, restarts, health-checks; a `curl (7)` line during restart is normal).
9. **Smoke:** pages 200 (`/`, `/login`, `/kurse`, changed admin page), anonymous 401 on changed APIs,
   new UI string present in `.next-<slot>`, student endpoints checked read-only, other levels' data
   unchanged vs backup, error count 0, `nano_bot` / `telegram-cours2026` still active.
10. **Report** with revision, backup path, SUCCESS only for steps that ran; update
    `docs/ai-context/current-state.md`, `recent-changes.md`.

## Rollback
Frontend: `cp frontend/.deploy/active.env.prev frontend/.deploy/active.env && systemctl restart vizu-frontend`.
Code: `git checkout` the previous files + restart. Data: from the backup (`pg_restore --clean --if-exists
--no-owner`) only on request. Migrations: never automatic.
