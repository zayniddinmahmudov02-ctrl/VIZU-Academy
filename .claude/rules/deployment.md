---
paths:
  - "frontend/scripts/**"
  - "backend/scripts/**"
  - "docs/*deploy*"
  - "docs/ai-context/deployment-map.md"
---
# Deployment rules

Procedure: skill `vizu-deploy`. Facts (server, services, backups): `docs/ai-context/deployment-map.md`.

- No step without a verified backup (`pg_dump` + restore check into a scratch DB as `postgres`, Hören
  storage tar + SHA256SUMS). If the backup fails, stop.
- Code reaches the server by `git pull --ff-only`. If local changes are not pushed yet, stage files as LF,
  check every target file is unchanged vs `HEAD` on the server, then copy. Unknown upstream commits: compare
  before pulling; stop on real conflicts.
- Migrations: offline SQL preview, expected current revision, one head. Never auto-downgrade.
- Frontend only via `frontend/scripts/deploy-frontend.sh` (never plain `npm run build` on the server).
- After deploy: health 200, anonymous 401 on protected APIs, logs without new errors, Telegram bot
  services untouched and active.
- Report only what really ran as SUCCESS; say what was not checked and why.
