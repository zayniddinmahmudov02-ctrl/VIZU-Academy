# Deployment map

Updated 2026-10-31 · verified on the server 2026-10-30 02:50 CET. Procedure: skill `vizu-deploy`. No secrets here.

| | |
|---|---|
| Server | `217.76.62.208`, checkout `/opt/vizu/VIZU-Academy` (git, branch `main`, LF) |
| Access | SSH `root`, key `~/.ssh/claude_vizu_new` |
| Services | `vizu-backend` (uvicorn, `127.0.0.1:8000`, health `/api/v1/health`), `vizu-frontend` (Next.js `:3000`) |
| Do not touch | `nano_bot.service`, `telegram-cours2026.service` and their code/DBs |
| Backend env | `backend/.env` (never print), venv `backend/.venv` (Python 3.12) |
| Frontend slots | `frontend/.next-a` / `.next-b`; active in `frontend/.deploy/active.env` (`NEXT_DIST_DIR`, `NEXT_DEPLOYMENT_ID`), previous in `active.env.prev` |
| Frontend deploy | `cd frontend && bash scripts/deploy-frontend.sh` (build inactive slot → switch → restart → health) — `docs/deploy-frontend.md` |
| Private storage | `backend/app/protected_storage/lesson-listening` (Hören audio, 50 files on 2026-10-30) |
| Backups | `/var/backups/vizu/<name>-<stamp>/` (700): `db.dump`, `db.toc`, `lesson-listening.tar`, `lesson-listening.sha256`, CSV metadata, `SHA256SUMS`, script reports. Restore check needs `sudo -u postgres` (app DB user cannot create databases) |
| DB | PostgreSQL, ~34 MB, 134 tables; Alembic head `c4f7a9e2d6b3` |
| Book audio for scripts | `/root/a2-book-audio/` (A2 7. Unterricht Text 2) |
| Logs | `journalctl -u vizu-backend` / `-u vizu-frontend`; known line `SUPER_ADMIN_VERIFICATION_PASSWORD is not set` |
| Runbooks | `docs/lms-deploy-runbook.md`, `docs/deploy-frontend.md`, reports `docs/a2-production-deployment.md`, `docs/audit/production-deploy-2026-10-29.md` |

Not installed on the server: `httpx`/`httpx2` (no TestClient), `openpyxl`.
