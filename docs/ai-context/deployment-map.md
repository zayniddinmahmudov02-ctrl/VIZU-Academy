# Deployment map

Updated 2026-11-21 · verified on the server 2026-11-21. Procedure: skill `vizu-deploy`. No secrets here.

| | |
|---|---|
| Server | `217.76.62.208`, checkout `/opt/vizu/VIZU-Academy` (git, branch `main`, LF) |
| Checkout state | HEAD `0cb7b165`; `origin/main` is 18 commits ahead; 251 dirty paths after fetch (2026-11-21). Do not pull/overlay until reconciled |
| Access | SSH `root`, key `~/.ssh/claude_vizu_new` |
| Services | `vizu-backend` (uvicorn, `127.0.0.1:8000`, health `/api/v1/health`), `vizu-frontend` (Next.js `:3000`) |
| Do not touch | `nano_bot.service`, `telegram-cours2026.service` and their code/DBs |
| LiveKit | `livekit-server`, `coturn`, and Docker packages are absent; no LiveKit/coturn service is active. `meet.vizu-deutsch.com` has no public A/AAAA/CNAME record; the existing certificate covers only `vizu-deutsch.com` and `www` |
| Backend env | `backend/.env` (never print), venv `backend/.venv` (Python 3.12) |
| systemd PATH | `vizu-backend` has a drop-in `/etc/systemd/system/vizu-backend.service.d/10-path.conf` (2026-11-15) that adds `/usr/bin` to `PATH` (FFmpeg / ffprobe live there; the unit used to have the venv only = cause of "Audioverarbeitung nicht verfügbar"). Revert: delete the file + `systemctl daemon-reload` + restart. The code also searches the system folders itself (`audio_files.service.find_tool`) |
| Frontend slots | `frontend/.next-a` / `.next-b`; active in `frontend/.deploy/active.env` (`NEXT_DIST_DIR`, `NEXT_DEPLOYMENT_ID`), previous in `active.env.prev` |
| Frontend deploy | `cd frontend && bash scripts/deploy-frontend.sh` (build inactive slot → switch → restart → health) — `docs/deploy-frontend.md` |
| Private storage | `backend/app/protected_storage/lesson-listening` (Hören audio, 50 files on 2026-10-30) |
| Backups | `/var/backups/vizu/<name>-<stamp>/` (700): `db.dump`, `db.toc`, `lesson-listening.tar`, `lesson-listening.sha256`, CSV metadata, `SHA256SUMS`, script reports. Latest verified: `/var/backups/vizu/pre-group-video-chat-20261121-001608` (166-table restore check, 51 audio files, checksums OK) |
| DB | PostgreSQL 16, 166 tables; production Alembic `a6c2e8f4b9d1` (2026-11-21) |
| Book audio for scripts | `/root/a2-book-audio/` (A2 7. Unterricht Text 2) |
| Logs | `journalctl -u vizu-backend` / `-u vizu-frontend`; known line `SUPER_ADMIN_VERIFICATION_PASSWORD is not set` |
| Runbooks | `docs/lms-deploy-runbook.md`, `docs/deploy-frontend.md`, reports `docs/a2-production-deployment.md`, `docs/audit/production-deploy-2026-10-29.md` |

Not installed on the server: `httpx`/`httpx2` (no TestClient), `openpyxl`.

## 2026-11-21 Group Video Chat production preflight

- DNS queries to the local resolver and `1.1.1.1` returned no A/AAAA/CNAME for `meet.vizu-deutsch.com`. Owner action: add `A meet.vizu-deutsch.com → 217.76.62.208`; do not add AAAA unless the VPS IPv6 is confirmed.
- Ubuntu 24.04.4 LTS, 2 vCPU, 3.8 GiB RAM, 212 GiB free disk. Nginx 1.24 and the existing VIZU + Telegram services are active. UFW is inactive; only TCP 80/443 listeners were found among the inspected signaling/TURN/media ports. No LiveKit UDP test was possible.
- Existing TLS certificate expires 2027-02-18 but contains only the apex and `www`, not `meet`. LiveKit and coturn services are inactive; Docker is absent.
- LiveKit URL/key/secret are not configured in production `.env`; the backend settings do not yet define the TTL/participant settings, `livekit-api` is absent, and the server checkout lacks the video-chat service and migration.
- Fresh DB + private audio backup and scratch restore passed: 166 table row counts matched the exported snapshot; all 51 audio files were inventoried; checksums passed; scratch DB and temporary restore copy were removed.
- No production application code, database migration, `.env`, Nginx, firewall, Docker, or service changes were made. Current deploy is blocked by DNS/TLS and the 251-path dirty checkout; see `current-state.md`.
