#!/usr/bin/env bash
# VIZU Academy — run ON THE SERVER, by the server owner, in his own session
# (as root or with sudo). Installs ONE public key for the deploy user and
# checks that SSH key login, the project directory and the needed sudo
# rights are in place. It never changes sshd_config, never restarts sshd or
# the VIZU services and never touches the project or the database.
#
#   sudo bash server_setup_on_server.sh install "ssh-ed25519 AAAA... claude-vizu"   # add the key
#   sudo bash server_setup_on_server.sh check                                        # only report
#   sudo bash server_setup_on_server.sh remove  "claude-vizu"                        # revoke the key again
#
# Settings: VIZU_USER (vizu)  VIZU_PROJECT (/opt/vizu/VIZU-Academy)
#           VIZU_KEY_FROM (optional, e.g. "203.0.113.7" — the key then works only from that IP)

set -euo pipefail
USER_NAME="${VIZU_USER:-vizu}"
PROJECT="${VIZU_PROJECT:-/opt/vizu/VIZU-Academy}"
SERVICES=(vizu-backend vizu-frontend)

[ "$(id -u)" -eq 0 ] || { echo "run with sudo (needs to write ~$USER_NAME/.ssh and read the sshd config)"; exit 1; }
id "$USER_NAME" >/dev/null 2>&1 || { echo "user '$USER_NAME' does not exist. Create it deliberately, e.g.: adduser --disabled-password $USER_NAME"; exit 1; }
HOME_DIR="$(getent passwd "$USER_NAME" | cut -d: -f6)"
AK="$HOME_DIR/.ssh/authorized_keys"

install_key() {
  local key="$1"
  [[ "$key" =~ ^(ssh-ed25519|ecdsa-sha2-nistp(256|384|521)|ssh-rsa)\ [A-Za-z0-9+/=]+(\ .*)?$ ]] || { echo "not a public key line (expected 'ssh-ed25519 AAAA… comment')"; exit 1; }
  printf '%s\n' "$key" > /tmp/.vizu_key_check.pub && ssh-keygen -lf /tmp/.vizu_key_check.pub && rm -f /tmp/.vizu_key_check.pub
  install -d -m 700 -o "$USER_NAME" -g "$(id -gn "$USER_NAME")" "$HOME_DIR/.ssh"
  touch "$AK"; chown "$USER_NAME:$(id -gn "$USER_NAME")" "$AK"; chmod 600 "$AK"
  local blob; blob="$(awk '{print $2}' <<<"$key")"
  if grep -q "$blob" "$AK"; then
    echo "key already installed for $USER_NAME"
  else
    local prefix=""
    [ -n "${VIZU_KEY_FROM:-}" ] && prefix="from=\"$VIZU_KEY_FROM\",no-agent-forwarding,no-X11-forwarding "
    printf '%s%s\n' "$prefix" "$key" >> "$AK"
    echo "key added to $AK${prefix:+ (restricted: $prefix)}"
  fi
}

remove_key() {
  local pattern="$1" backup
  [ -f "$AK" ] || { echo "no $AK"; return; }
  backup="$AK.bak.$(date +%Y%m%d%H%M%S)"
  cp -p "$AK" "$backup"
  grep -vF -- "$pattern" "$backup" > "$AK" || true
  chown "$USER_NAME:$(id -gn "$USER_NAME")" "$AK"; chmod 600 "$AK"
  echo "$(( $(wc -l < "$backup") - $(wc -l < "$AK") )) line(s) containing '$pattern' removed from $AK (backup: $backup)"
}

check() {
  echo "== user $USER_NAME"
  id "$USER_NAME"
  echo "shell: $(getent passwd "$USER_NAME" | cut -d: -f7)   home: $HOME_DIR"
  passwd -S "$USER_NAME" 2>/dev/null | awk '{print "password state: "$2" (L = locked, P = set, NP = none)"}'

  echo; echo "== ~/.ssh permissions (sshd ignores keys with loose permissions)"
  stat -c '%A %U:%G %n' "$HOME_DIR" "$HOME_DIR/.ssh" "$AK" 2>/dev/null || echo "no $AK yet"
  [ -f "$AK" ] && { echo "installed keys:"; ssh-keygen -lf "$AK" 2>/dev/null | sed 's/^/  /'; }

  echo; echo "== sshd effective settings (read only)"
  sshd -T 2>/dev/null | grep -Ei '^(port|pubkeyauthentication|passwordauthentication|kbdinteractiveauthentication|permitrootlogin|authorizedkeysfile|allowusers|allowgroups|denyusers|maxauthtries) ' | sed 's/^/  /'
  echo "  (recommended: pubkeyauthentication yes, passwordauthentication no — change it yourself only after the key login works)"
  echo "host key fingerprints (compare with the first connection on Windows):"
  for f in /etc/ssh/ssh_host_ed25519_key.pub /etc/ssh/ssh_host_ecdsa_key.pub; do [ -f "$f" ] && ssh-keygen -lf "$f" | sed 's/^/  /'; done

  echo; echo "== firewall / ssh service"
  systemctl is-active ssh 2>/dev/null | sed 's/^/  ssh service: /' || true
  command -v ufw >/dev/null && ufw status 2>/dev/null | head -8 | sed 's/^/  /'

  echo; echo "== project directory $PROJECT as $USER_NAME"
  ls -ld "$PROJECT" 2>/dev/null || echo "  missing: $PROJECT"
  for t in "-r:read" "-w:write" "-x:enter"; do
    sudo -u "$USER_NAME" test "${t%%:*}" "$PROJECT" && echo "  can ${t#*:}" || echo "  can NOT ${t#*:}"
  done
  sudo -u "$USER_NAME" git -C "$PROJECT" --no-optional-locks rev-parse --abbrev-ref HEAD 2>&1 | sed 's/^/  git branch: /'
  echo "  files not owned by $USER_NAME: $(find "$PROJECT" -path "$PROJECT/node_modules" -prune -o -path "$PROJECT/frontend/node_modules" -prune -o ! -user "$USER_NAME" -print 2>/dev/null | wc -l)"

  echo; echo "== services"
  for s in "${SERVICES[@]}"; do
    printf '  %-15s %s  user=%s  dir=%s\n' "$s" "$(systemctl is-active "$s" 2>/dev/null)" \
      "$(systemctl show -p User --value "$s")" "$(systemctl show -p WorkingDirectory --value "$s")"
  done
  echo "  journal readable by $USER_NAME: $(id -nG "$USER_NAME" | grep -qwE 'adm|systemd-journal' && echo yes || echo 'no (add to group systemd-journal for log reading)')"

  echo; echo "== sudo rights of $USER_NAME (what deploy steps can it do?)"
  sudo -l -U "$USER_NAME" 2>/dev/null | sed 's/^/  /' | tail -n +1 | head -20
  cat <<EOF

  Needs root / sudo (decide yourself what to allow, e.g. via /etc/sudoers.d/vizu, edited with visudo):
    systemctl restart vizu-backend | vizu-frontend   — after a deploy
    nginx -t / systemctl reload nginx / nginx -T     — web server config (client_max_body_size)
    journalctl -u vizu-*                             — unless $USER_NAME is in group systemd-journal
    apt, ufw, /etc/*                                 — never needed for a normal deploy
  Does NOT need sudo when $USER_NAME owns $PROJECT:
    git pull, pip install / alembic upgrade in the venv, npm ci / next build, the A1 import scripts
EOF
}

case "${1:-}" in
  install) [ -n "${2:-}" ] || { echo "usage: $0 install \"ssh-ed25519 AAAA… comment\""; exit 1; }; install_key "$2"; check ;;
  check) check ;;
  remove) [ -n "${2:-}" ] || { echo "usage: $0 remove <comment or key part>"; exit 1; }; remove_key "$2" ;;
  *) sed -n '2,15p' "$0"; exit 1 ;;
esac
