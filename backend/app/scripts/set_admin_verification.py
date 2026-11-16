"""Sets SUPER_ADMIN_VERIFICATION_PASSWORD in backend/.env — the Super Admin's second factor ("Admin-Passwort" after the login).

Without it `POST /auth/verify-admin-password` answers 503 ADMIN_VERIFICATION_NOT_CONFIGURED and the Super Admin cannot confirm (known-issues #7).
The owner runs this on the server — the value is typed into a hidden prompt, so it never appears in a chat, a shell history, a log or a report:

    cd /opt/vizu/VIZU-Academy/backend
    .venv/bin/python -m app.scripts.set_admin_verification            # dry run: only says whether the setting exists
    .venv/bin/python -m app.scripts.set_admin_verification --apply    # asks twice (no echo), writes .env (mode 600), audit entry without the value
    systemctl restart vizu-backend

12–128 characters from letters, digits and `! % & ( ) * + , - . / : ; < = > ? @ [ ] ^ _ { | } ~` (no spaces, quotes, `$`, `#` or backslash: such a value
is safe to write unquoted). Every other line of `.env` stays untouched; an existing value is replaced.
"""

from __future__ import annotations

import argparse
import getpass
import os
import re
import secrets
import sys
import tempfile
from pathlib import Path

KEY = "SUPER_ADMIN_VERIFICATION_PASSWORD"
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
ALLOWED = re.compile(r"^[A-Za-z0-9!%&()*+,\-./:;<=>?@\[\]^_{|}~]{12,128}$")


def is_valid(password: str) -> bool:
    return bool(ALLOWED.fullmatch(password))


def is_configured(text: str) -> bool:
    """True when a non-empty KEY=value line exists (the value itself is never returned)."""
    for line in text.splitlines():
        name, sep, value = line.partition("=")
        if sep and name.strip() == KEY and value.strip().strip("'\""):
            return True
    return False


def merge_env(text: str, password: str) -> str:
    """The .env text with KEY set to the password: the old KEY line is replaced, everything else (order, comments, other settings) stays."""
    if not is_valid(password):
        raise ValueError("invalid password")
    lines, done = [], False
    for line in text.splitlines():
        if line.partition("=")[0].strip() == KEY:
            if not done:
                lines.append(f"{KEY}={password}")
                done = True
            continue  # a duplicate KEY line would silently win or lose: keep exactly one
        lines.append(line)
    if not done:
        lines.append(f"{KEY}={password}")
    return "\n".join(lines) + "\n"


def _write_private(path: Path, content: str) -> None:
    """Atomic write with mode 600 (the .env holds other secrets too)."""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".env.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Set the Super Admin verification password (hidden prompt).")
    parser.add_argument("--apply", action="store_true", help="really write it (default: dry run)")
    parser.add_argument("--env-file", default=str(ENV_PATH), help="the .env to change (default: backend/.env)")
    args = parser.parse_args(argv)
    path = Path(args.env_file)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    print(f"{path}: {KEY} is {'set' if is_configured(text) else 'NOT set'}")
    if not args.apply:
        print("dry run: nothing changed. Run again with --apply to set it.")
        return 0
    if not sys.stdin.isatty():
        print("refused: the password must be typed into the prompt (no pipes, no arguments), so it cannot end up in a history or a log.")
        return 2
    first = getpass.getpass("New Super Admin verification password (hidden): ")
    second = getpass.getpass("Again: ")
    if not secrets.compare_digest(first.encode(), second.encode()):
        print("the two entries differ — nothing changed.")
        return 1
    if not is_valid(first):
        print("not accepted: 12-128 characters from letters, digits and ! % & ( ) * + , - . / : ; < = > ? @ [ ] ^ _ { | } ~ (no spaces, quotes, $, # or backslash).")
        return 1
    _write_private(path, merge_env(text, first))
    print(f"{KEY} written to {path} (mode 600). Restart the backend: systemctl restart vizu-backend")
    try:  # the audit entry names the action only, never the value
        from app.core.audit import write_audit
        from app.db.session import SessionLocal

        with SessionLocal() as db:
            write_audit(db, actor_id=None, action="admin_verification_configured", details="SUPER_ADMIN_VERIFICATION_PASSWORD set with app.scripts.set_admin_verification (value not recorded)")
    except Exception as exc:  # the file is written either way
        print(f"(audit entry not written: {type(exc).__name__})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
