#!/usr/bin/env bash
# VIZU Academy — SSH access to the production server from a Windows PC
# (Git Bash / the Bash tool of Claude Code). Public-key authentication only:
# no password is stored, asked for or passed anywhere by this script.
#
# What this script can NOT do: it cannot grant itself access. The public key
# must first be installed on the server by someone who already has access
# (see scripts/server_setup_on_server.sh and scripts/SERVER_SSH.md).
#
# Usage:
#   bash scripts/server_connect.sh check      local checks: key, permissions, agent, not in git
#   bash scripts/server_connect.sh pubkey     print the PUBLIC key (to install on the server)
#   bash scripts/server_connect.sh test       non-interactive login test (whoami, hostname)
#   bash scripts/server_connect.sh diagnose   READ-ONLY diagnostics on the server (nothing is changed)
#   bash scripts/server_connect.sh shell      interactive shell on the server
#
# Settings (environment, optional):
#   VIZU_SSH_HOST (217.76.62.208)  VIZU_SSH_USER (vizu)  VIZU_SSH_KEY (~/.ssh/claude_vizu)  VIZU_SSH_PORT (22)

set -euo pipefail

HOST="${VIZU_SSH_HOST:-217.76.62.208}"
SSH_USER="${VIZU_SSH_USER:-vizu}"
KEY="${VIZU_SSH_KEY:-$HOME/.ssh/claude_vizu}"
PORT="${VIZU_SSH_PORT:-22}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"

# Windows: prefer the Windows OpenSSH client — it uses the Windows ssh-agent
# service, so a passphrase-protected key works without typing the passphrase
# in a non-interactive session (Claude Code). Elsewhere: the normal ssh.
SSH=ssh
if [ -x "/c/Windows/System32/OpenSSH/ssh.exe" ]; then
  SSH="/c/Windows/System32/OpenSSH/ssh.exe"
  SSH_ADD="/c/Windows/System32/OpenSSH/ssh-add.exe"
else
  SSH_ADD=ssh-add
fi

# public key only, known host must match (no blind trust), never a password prompt
OPTS=(-p "$PORT" -o IdentitiesOnly=yes -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no
      -o PreferredAuthentications=publickey -o StrictHostKeyChecking=yes -o ConnectTimeout=15)
key_path_for_ssh() {
  # the Windows ssh.exe needs a Windows path
  if [[ "$SSH" == *.exe ]] && command -v cygpath >/dev/null 2>&1; then cygpath -w "$KEY"; else echo "$KEY"; fi
}

die() { echo "ERROR: $*" >&2; exit 1; }

check() {
  echo "== local SSH checks"
  [ -f "$KEY" ] || die "private key $KEY not found (create: ssh-keygen -t ed25519 -f ~/.ssh/claude_vizu -C claude-vizu)"
  [ -f "$KEY.pub" ] || die "public key $KEY.pub not found"
  echo "key:          $KEY"
  echo "fingerprint:  $(ssh-keygen -lf "$KEY.pub")"
  if ssh-keygen -y -P "" -f "$KEY" >/dev/null 2>&1; then
    echo "passphrase:   NONE — consider adding one: ssh-keygen -p -f \"$KEY\""
  else
    echo "passphrase:   yes (good) — it must be loaded into the ssh-agent for non-interactive use"
  fi
  if "$SSH_ADD" -l 2>/dev/null | grep -q "$(ssh-keygen -lf "$KEY.pub" | awk '{print $2}')"; then
    echo "ssh-agent:    key loaded"
  else
    echo "ssh-agent:    key NOT loaded — Windows PowerShell (once, as administrator for the service):"
    echo "                Set-Service ssh-agent -StartupType Automatic; Start-Service ssh-agent"
    echo "              then as your user:  ssh-add \$env:USERPROFILE\\.ssh\\claude_vizu"
  fi
  if command -v icacls >/dev/null 2>&1 || [ -x /c/Windows/System32/icacls.exe ]; then
    echo "permissions:"; /c/Windows/System32/icacls.exe "$(cygpath -w "$KEY" 2>/dev/null || echo "$KEY")" 2>/dev/null | sed 's/^/              /' | head -6
  fi
  # the private key must never be inside the repository
  case "$(cd "$(dirname "$KEY")" && pwd)" in
    "$REPO"*) die "the private key lies inside the repository ($KEY) — move it to ~/.ssh" ;;
  esac
  if git -C "$REPO" ls-files | grep -Eiq '(^|/)(id_(rsa|ed25519|ecdsa)|claude_vizu)(\.pub)?$|\.pem$|\.ppk$'; then
    die "a key-like file is tracked by git: $(git -C "$REPO" ls-files | grep -Ei '(id_(rsa|ed25519|ecdsa)|claude_vizu)|\.pem$|\.ppk$')"
  fi
  echo "repository:   no key files tracked by git"
  grep -q "$HOST" "$HOME/.ssh/known_hosts" 2>/dev/null && echo "known_hosts:  $HOST present" \
    || echo "known_hosts:  $HOST missing — connect once interactively and compare the host key fingerprint with the server (ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub)"
}

pubkey() {
  echo "# PUBLIC key — safe to share, install it on the server (scripts/server_setup_on_server.sh):"
  cat "$KEY.pub"
}

run_remote() {
  "$SSH" "${OPTS[@]}" -o BatchMode=yes -i "$(key_path_for_ssh)" "$SSH_USER@$HOST" "$@"
}

test_login() {
  echo "== login test $SSH_USER@$HOST:$PORT (public key only, no password)"
  run_remote 'echo "connected as $(whoami) on $(hostname) — $(. /etc/os-release && echo "$PRETTY_NAME")"; id' \
    || die "login failed — key not installed for $SSH_USER, key not in the agent, or host key changed (see: bash scripts/server_connect.sh check)"
}

diagnose() {
  echo "== READ-ONLY diagnostics on $SSH_USER@$HOST (nothing is changed on the server)"
  # CRLF of a Windows checkout would break bash on the server
  tr -d '\r' < "$HERE/server_diagnose.sh" | run_remote 'bash -s'
}

shell() {
  "$SSH" "${OPTS[@]}" -i "$(key_path_for_ssh)" -t "$SSH_USER@$HOST"
}

case "${1:-}" in
  check) check ;;
  pubkey) pubkey ;;
  test) test_login ;;
  diagnose) diagnose ;;
  shell) shell ;;
  *) sed -n '2,20p' "$0"; exit 1 ;;
esac
