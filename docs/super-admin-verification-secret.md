# Setting `SUPER_ADMIN_VERIFICATION_PASSWORD` on production

The backend reads this value from `backend/.env` through pydantic settings
(`app/core/config.py`, `env_file=".env"`). The `vizu-backend` systemd unit
only sets `PATH` and does not override it. While the value is empty,
`POST /auth/verify-admin-password` answers `503
ADMIN_VERIFICATION_NOT_CONFIGURED` and never falls back to a default.
At every start the backend logs
`SUPER_ADMIN_VERIFICATION_PASSWORD is not set`.

Status on 2026-10-26: **not set** in production (0 matching lines). The
warning appears in every start since at least 2026-10-22. `backend/.env`
has mode `600 root:root` and is git-ignored.

## Rules

- The owner chooses the value. Nobody generates it in chat, and it is never
  committed, pasted into a ticket or sent through a chat or AI tool.
- Use ≥ 16 characters from `A-Z a-z 0-9` only. That avoids `.env` quoting
  and `#` comment pitfalls. Store it in the owner's password manager.
- Use a different value from the SUPER_ADMIN account password.

## Steps (run as root on the server, in an interactive shell)

`read -s` does not echo. `read` and `printf` are shell builtins, so the
value does not show up in `ps`, and it does not enter shell history.

```bash
cd /opt/vizu/VIZU-Academy/backend

# 0. state: prints only a count (0 = not set)
grep -c '^SUPER_ADMIN_VERIFICATION_PASSWORD=.' .env

# 1. backup of .env (same 600 permissions)
cp -p .env ".env.bak-$(date +%Y%m%d-%H%M%S)"

# 2. enter the value twice, without echo
read -rs -p "Admin verification password: " P1; echo
read -rs -p "Repeat: " P2; echo
if [ "$P1" != "$P2" ] || [ ${#P1} -lt 16 ] || ! [[ "$P1" =~ ^[A-Za-z0-9]+$ ]]; then
  echo "not set: mismatch, shorter than 16, or not alphanumeric"; unset P1 P2
else
  # 3. replace or add the line atomically, keeping mode 600
  umask 077
  grep -v '^SUPER_ADMIN_VERIFICATION_PASSWORD=' .env > .env.new
  printf 'SUPER_ADMIN_VERIFICATION_PASSWORD=%s\n' "$P1" >> .env.new
  unset P1 P2
  chmod 600 .env.new && mv .env.new .env
  echo "written"
fi

# 4. apply and verify (again no value printed)
grep -c '^SUPER_ADMIN_VERIFICATION_PASSWORD=.' .env          # expect 1
systemctl restart vizu-backend
sleep 15
journalctl -u vizu-backend --since "-1 min" --no-pager | grep -c 'SUPER_ADMIN_VERIFICATION_PASSWORD is not set'   # expect 0
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/health                                           # expect 200
```

Then log in as SUPER_ADMIN in the browser. The second step must accept the
new value. A wrong value must give "Incorrect administrator password".

**Rollback:** `mv .env.bak-<timestamp> .env && systemctl restart vizu-backend`.

**Rotation:** repeat the steps. Sessions already past the step are not
affected, because the check runs only once at login (see the limitation
below).

## Known limitation (separate fix, not part of this setup)

The second step is enforced only in the frontend. The backend never
requires it: every SUPER_ADMIN endpoint is gated by role only
(`require_super_admin`). The login form stores the tokens *before* the
second step, and `SessionRedirect` sends a SUPER_ADMIN with a stored token
straight to `/admin`. So a SUPER_ADMIN password alone gives full admin API
access, and a page reload skips the step. Proposed server-side fix:
record the verification on the login session (`refresh_tokens.session_id`,
e.g. an `admin_verified_at` column). Then make `require_super_admin` (and
the other staff gates) refuse a SUPER_ADMIN session that has not been
verified, and have the frontend keep the tokens in memory until the
verification succeeds.
