#!/usr/bin/env bash
# VIZU Academy — READ-ONLY production diagnostics. Sent by
# `bash scripts/server_connect.sh diagnose` and run as the deploy user.
#
# Writes nothing: no git fetch/pull, no index refresh (--no-optional-locks),
# no .pyc files (PYTHONDONTWRITEBYTECODE), no service restarts, no database
# writes (only `alembic current` and the read-only A1 report run SELECTs).
# Secrets are never printed: .env files are listed, never read out.

PROJECT="${VIZU_PROJECT:-/opt/vizu/VIZU-Academy}"
export PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 PYTHONIOENCODING=utf-8
sec() { printf '\n==================== %s\n' "$*"; }
mask() { sed -E 's#(https?://)[^/@ ]+@#\1***@#g'; }

sec "system"
echo "host: $(hostname)  user: $(whoami)  $(. /etc/os-release && echo "$PRETTY_NAME")  uptime: $(uptime -p)"
echo "load: $(cut -d' ' -f1-3 /proc/loadavg)  cpus: $(nproc)"
free -h
df -h / /opt "$PROJECT" 2>/dev/null | awk 'NR==1 || !seen[$0]++'
du -sh "$PROJECT"/backend/uploads "$PROJECT"/backend/app/protected_storage 2>/dev/null

sec "git ($PROJECT)"
cd "$PROJECT" 2>/dev/null || { echo "cannot enter $PROJECT"; exit 1; }
git --no-optional-locks rev-parse --abbrev-ref HEAD
git --no-optional-locks log --oneline -5
git --no-optional-locks remote -v | mask | head -2
echo "local changes:"; git --no-optional-locks status --short | head -30
echo "ahead/behind origin (last fetched state, no fetch done): $(git --no-optional-locks rev-list --left-right --count HEAD...@{u} 2>/dev/null || echo n/a)"

sec "services"
for s in vizu-backend vizu-frontend nginx postgresql; do
  printf '%-15s %-9s since %s\n' "$s" "$(systemctl is-active "$s" 2>/dev/null)" "$(systemctl show -p ActiveEnterTimestamp --value "$s" 2>/dev/null)"
done
for s in vizu-backend vizu-frontend; do
  echo "-- $s"; systemctl show -p User -p WorkingDirectory -p ExecStart -p EnvironmentFiles "$s" 2>/dev/null | sed -E 's/ ; (argv|ignore_errors|start_time|stop_time|pid|code|status)=[^;]*//g' | mask
done
echo "-- recent backend errors (journal, if readable)"
if journal="$(journalctl -u vizu-backend -p err -n 15 --no-pager 2>/dev/null)"; then echo "$journal" | mask; else echo "journal not readable for $(whoami)"; fi

sec "deploy configuration"
echo "env files (presence only, contents NOT shown):"
ls -la "$PROJECT"/backend/.env* "$PROJECT"/frontend/.env* 2>/dev/null | awk '{print "  "$1, $3, $9}'
echo "nginx sites:"; ls /etc/nginx/sites-enabled 2>/dev/null | sed 's/^/  /'
grep -rhE '^\s*(server_name|client_max_body_size|proxy_pass|listen)\b' /etc/nginx/sites-enabled /etc/nginx/nginx.conf 2>/dev/null | sed 's/^\s*/  /' | sort | uniq -c
grep -rqE 'client_max_body_size' /etc/nginx 2>/dev/null || echo "  client_max_body_size not set -> nginx default 1m (too small for the 27 MB A1 audio)"
ls -d "$PROJECT"/frontend/.next* 2>/dev/null | sed 's/^/frontend build dirs: /'
[ -f "$PROJECT/frontend/.next/BUILD_ID" ] && echo "frontend BUILD_ID: $(cat "$PROJECT/frontend/.next/BUILD_ID") ($(stat -c %y "$PROJECT/frontend/.next/BUILD_ID" | cut -d. -f1))"
echo "node: $(node -v 2>/dev/null)"

sec "backend environment"
PY=""
for p in "$PROJECT/backend/.venv/bin/python" "$PROJECT/backend/venv/bin/python" "$PROJECT/.venv/bin/python" "$PROJECT/venv/bin/python"; do
  [ -x "$p" ] && PY="$p" && break
done
[ -z "$PY" ] && PY="$(systemctl show -p ExecStart --value vizu-backend 2>/dev/null | grep -oE 'path=[^ ;]+' | cut -d= -f2 | xargs -r dirname | sed 's#$#/python#')"
echo "python: ${PY:-not found} $([ -x "$PY" ] && "$PY" -V 2>&1)"
cd "$PROJECT/backend" 2>/dev/null || exit 0
if [ -x "$PY" ]; then
  echo "alembic (read only):"; "$PY" -m alembic current 2>&1 | grep -vE 'INFO|SUPER_ADMIN' | tail -3 | sed 's/^/  /'
  echo "alembic heads:"; "$PY" -m alembic heads 2>&1 | grep -v INFO | sed 's/^/  /'
fi

sec "A1 content import mechanism"
for f in app/scripts/import_vizu_deutsch_a1.py app/scripts/a1_lesson_report.py app/services/lms/grammar_text_only.py; do
  [ -f "$f" ] && echo "present: $f" || echo "MISSING: $f (code older than main)"
done
echo "book data: $(ls app/data/vizu_deutsch_a1/modul_*.json 2>/dev/null | wc -l) module file(s)"
if [ -x "$PY" ] && [ -f app/scripts/a1_lesson_report.py ]; then
  for n in $(seq 1 14); do
    "$PY" -m app.scripts.a1_lesson_report --lesson "$n" 2>&1 | grep -vE 'SUPER_ADMIN|^\s*$' | sed 's/^/  /'
  done
fi

sec "done — nothing was changed on the server"
