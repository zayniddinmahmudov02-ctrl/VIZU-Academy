# Deployment map

Updated 2026-11-21 · verified on the server 2026-11-21. Procedure: skill `vizu-deploy`. No secrets here.

| | |
|---|---|
| Server | `217.76.62.208`, checkout `/opt/vizu/VIZU-Academy` (git, branch `main`, LF) |
| Checkout state | HEAD `0cb7b165` + overlays 1–19 (dirty working tree); `origin/main` `3f6db0f3` is 19 commits ahead and still contains the OLD video-chat code (migration `c1v7d3e9a5b2`): **do not `git pull`** until the owner has pushed the current local tree (else two Alembic heads). Overlays: drift check per file against the last known server copy |
| Access | SSH `root`, key `~/.ssh/claude_vizu_new` |
| Services | `vizu-backend` (uvicorn, `127.0.0.1:8000`, health `/api/v1/health`), `vizu-frontend` (Next.js `:3000`) |
| Do not touch | `nano_bot.service`, `telegram-cours2026.service` and their code/DBs |
| LiveKit (group video lessons) | `livekit.service` (user `livekit`, `/usr/local/bin/livekit-server` v1.13.11, config `/etc/livekit/livekit.yaml` 640 with the keys — never print), signaling `127.0.0.1:7880` behind nginx `location /livekit/` (= `wss://vizu-deutsch.com/livekit`, no access log), ICE TCP 7881, ICE UDP 7882, TURN UDP 3478 (relay 30000–40000). No TURN/TLS (needs a DNS-only host + cert, BLOCKED). Runbook + rollback: `docs/group-video-lessons.md` |
| Backend env | `backend/.env` (never print), venv `backend/.venv` (Python 3.12) |
| systemd PATH | `vizu-backend` has a drop-in `/etc/systemd/system/vizu-backend.service.d/10-path.conf` (2026-11-15) that adds `/usr/bin` to `PATH` (FFmpeg / ffprobe live there; the unit used to have the venv only = cause of "Audioverarbeitung nicht verfügbar"). Revert: delete the file + `systemctl daemon-reload` + restart. The code also searches the system folders itself (`audio_files.service.find_tool`) |
| Frontend slots | `frontend/.next-a` / `.next-b`; active in `frontend/.deploy/active.env` (`NEXT_DIST_DIR`, `NEXT_DEPLOYMENT_ID`), previous in `active.env.prev` |
| Frontend deploy | `cd frontend && bash scripts/deploy-frontend.sh` (build inactive slot → switch → restart → health) — `docs/deploy-frontend.md` |
| Private storage | `backend/app/protected_storage/lesson-listening` (Hören audio, 50 files on 2026-10-30) |
| Backups | `/var/backups/vizu/<name>-<stamp>/` (700): `db.dump`, `db.toc`, `lesson-listening.tar`, `lesson-listening.sha256`, CSV metadata, `SHA256SUMS`, script reports. Latest verified: `/var/backups/vizu/pre-team-kontroll-20261123-183235` (169-table restore check, 0 differing, SHA256SUMS OK; overlay 22 originals, migration preview, library categories plan / row copy); before: `pre-lesen-regrade-20261123-051421` (JSON row copy of the regraded Lesen attempts), `pre-lesen-keys-20261123-040549`, `pre-student-stats-20261121-154113` |
| DB | PostgreSQL 16, 172 tables; production Alembic `c8d3f5a1e7b2` (2026-11-23) |
| Book audio for scripts | `/root/a2-book-audio/` (A2 7. Unterricht Text 2) |
| Logs | `journalctl -u vizu-backend` / `-u vizu-frontend` / `-u livekit`; known line `SUPER_ADMIN_VERIFICATION_PASSWORD is not set` |
| Runbooks | `docs/lms-deploy-runbook.md`, `docs/deploy-frontend.md`, reports `docs/a2-production-deployment.md`, `docs/audit/production-deploy-2026-10-29.md` |

Not installed on the server: `httpx`/`httpx2` (no TestClient), `openpyxl`.

## Host facts (2026-11-21)

- Ubuntu 24.04.4 LTS, 2 vCPU, 3.8 GiB RAM, ~212 GiB free. UFW inactive, `iptables` INPUT ACCEPT (no host firewall); from outside TCP 7881 and
  UDP 3478 answer, TCP 7880 does not (loopback only). `vizu-deutsch.com` is Cloudflare-proxied (WebSockets pass); media goes to the origin IP.
- TLS certificate (Let's Encrypt, apex + `www`) expires 2027-02-18. No `meet.` / `turn.` DNS records exist (not needed for signaling).
- Backend venv got `livekit-api==2.0.1` (+ aiohttp, protobuf, PyJWT, livekit-protocol …; `pip check` clean); `pip-freeze-before.txt` is in the backup.
