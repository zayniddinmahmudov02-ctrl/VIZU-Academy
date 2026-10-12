#!/usr/bin/env bash
# Verified backup before the A1–C1 course content reset. Changes nothing in
# the database or in storage — it only reads and writes into BACKUP_ROOT.
#
#   1. full PostgreSQL dump (pg_dump -Fc) of the app database,
#   2. archive of every file root (app/protected_storage + uploads),
#   3. verification: dump TOC readable, archive listable, sha256 sums,
#      optional test restore into a scratch database with row-count compare.
#
# Exit code != 0 means: the backup is NOT usable — do not start the cleanup.
#
# Run from backend/ as the user that owns the checkout:
#   bash scripts/backup-course-content.sh                  # dump + files + verify
#   RESTORE_CHECK=1 bash scripts/backup-course-content.sh  # + test restore (needs CREATEDB)
#
# Credentials come from the app settings (.env); they are passed to pg_dump
# through the environment only and are never printed.
set -euo pipefail

BACKEND_DIR="${BACKEND_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON="${PYTHON:-$BACKEND_DIR/.venv/bin/python}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/vizu}"
RESTORE_CHECK="${RESTORE_CHECK:-0}"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$BACKUP_ROOT/course-reset-$STAMP"

cd "$BACKEND_DIR"
[ -x "$PYTHON" ] || PYTHON="$(command -v python3)"

# DB connection from the app's own settings — read into variables, not echoed.
mapfile -t DB < <("$PYTHON" -c '
from app.core.config import settings as s
print(s.DATABASE_HOST); print(s.DATABASE_PORT); print(s.DATABASE_NAME); print(s.DATABASE_USER); print(s.DATABASE_PASSWORD)' | tr -d '\r')
export PGHOST="${DB[0]}" PGPORT="${DB[1]}" PGDATABASE="${DB[2]}" PGUSER="${DB[3]}" PGPASSWORD="${DB[4]}"

# psql: unaligned, tuples only; strip CR (Windows psql) so values compare cleanly.
q() { psql -XAtq "$@" | tr -d '\r'; }

FILE_ROOTS=()
for d in app/protected_storage uploads; do [ -d "$d" ] && FILE_ROOTS+=("$d"); done

umask 077
mkdir -p "$OUT"

# Enough disk space? (files + rough DB size, with 20 % headroom)
need_kb=$(( $(du -sk "${FILE_ROOTS[@]}" 2>/dev/null | awk '{s+=$1} END {print s+0}') ))
db_bytes=$(q -c "select pg_database_size(current_database())")
need_kb=$(( (need_kb + db_bytes / 1024) * 12 / 10 ))
free_kb=$(df -Pk "$OUT" | awk 'NR==2 {print $4}')
echo "backup dir: $OUT"
echo "database:   $PGDATABASE ($(( db_bytes / 1024 / 1024 )) MB on disk)"
echo "file roots: ${FILE_ROOTS[*]}"
echo "needed ~$(( need_kb / 1024 )) MB, free $(( free_kb / 1024 )) MB"
if [ "$free_kb" -lt "$need_kb" ]; then
  echo "ERROR: not enough free space in $BACKUP_ROOT" >&2
  exit 1
fi

# 1) database
pg_dump -Fc --no-owner --file "$OUT/db.dump"
pg_restore --list "$OUT/db.dump" > "$OUT/db.toc"
tables=$(grep -c " TABLE DATA " "$OUT/db.toc" || true)
[ "$tables" -gt 0 ] || { echo "ERROR: dump contains no table data" >&2; exit 1; }
echo "db dump: $(du -h "$OUT/db.dump" | cut -f1), $tables tables"

# row counts of the live database at dump time (for the restore check / later comparison)
q -c "select table_name from information_schema.tables where table_schema='public' and table_type='BASE TABLE' order by 1" |
  while read -r t; do printf '%s\t%s\n' "$t" "$(q -c "select count(*) from \"$t\"")"; done > "$OUT/row_counts.tsv"

# 2) files
if [ "${#FILE_ROOTS[@]}" -gt 0 ]; then
  tar -cf "$OUT/files.tar" "${FILE_ROOTS[@]}"
  tar -tf "$OUT/files.tar" > "$OUT/files.list"
  on_disk=$(find "${FILE_ROOTS[@]}" -type f | wc -l)
  in_tar=$(grep -vc '/$' "$OUT/files.list" || true)
  [ "$on_disk" -eq "$in_tar" ] || { echo "ERROR: archive has $in_tar files, disk has $on_disk" >&2; exit 1; }
  echo "files: $in_tar files, $(du -h "$OUT/files.tar" | cut -f1)"
fi

# 3) checksums
(cd "$OUT" && sha256sum db.dump files.tar 2>/dev/null > SHA256SUMS && sha256sum -c --quiet SHA256SUMS)
echo "checksums: ok"

# optional: restore into a scratch database and compare row counts
if [ "$RESTORE_CHECK" = 1 ]; then
  scratch="${PGDATABASE}_restore_check_$$"
  createdb "$scratch"
  trap 'dropdb --if-exists "$scratch"' EXIT
  pg_restore --no-owner --exit-on-error -d "$scratch" "$OUT/db.dump"
  # row_counts.tsv was read right after the dump, so tables users write to
  # (logins, progress) may legitimately differ a little — reported, not fatal.
  # A missing table, or an empty one that is not empty live, is fatal.
  bad=0
  diff=0
  while IFS=$'\t' read -r t n; do
    m=$(PGDATABASE="$scratch" q -c "select count(*) from \"$t\"" 2>/dev/null || echo MISSING)
    if [ "$m" = MISSING ] || { [ "$m" = 0 ] && [ "$n" != 0 ]; }; then
      echo "ERROR: $t live=$n restored=$m" >&2; bad=1
    elif [ "$m" != "$n" ]; then
      echo "note: $t live=$n restored=$m (changed after the dump?)"; diff=$((diff + 1))
    fi
  done < "$OUT/row_counts.tsv"
  [ "$bad" = 0 ] || { echo "ERROR: restore check failed" >&2; exit 1; }
  echo "restore check: $(wc -l < "$OUT/row_counts.tsv") tables restored, $diff with differing counts"
fi

echo "OK: backup complete and verified -> $OUT"
