"""Bootstrap script: creates the platform's first SUPER_ADMIN account.

The `promote_initial_super_admin` migration only UPDATEs an existing user's
role by email — it's a silent no-op on an empty `users` table, which is
exactly what happened here. This script does the other half: it INSERTs
the account if (and only if) it doesn't already exist, using the same
SQLAlchemy session and password hashing as normal registration.

Safe to re-run — does nothing if the account is already present.

Run from the `backend/` directory:

    python -m app.scripts.create_super_admin
"""

import app.models  # noqa: F401 — registers every model with Base before querying

from sqlalchemy.exc import IntegrityError

from app.core.security.password import hash_password
from app.core.security.roles import UserRole
from app.db.session import SessionLocal
from app.models.user import User

EMAIL = "zayniddin.mahmudov.02@gmail.com"
USERNAME = "zayniddin"
PASSWORD = "12345678"


def main() -> None:
    db = SessionLocal()

    try:
        existing = db.query(User).filter(User.email == EMAIL).first()

        if existing is not None:
            print(
                f"User already exists — nothing to do. "
                f"id={existing.id} role={existing.role}"
            )
            return

        user = User(
            email=EMAIL,
            username=USERNAME,
            password_hash=hash_password(PASSWORD),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
        )

        db.add(user)

        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            print(f"Insert failed (likely a duplicate email/username): {exc}")
            raise SystemExit(1)

        db.refresh(user)

        print(
            f"Created SUPER_ADMIN: id={user.id} email={user.email} "
            f"username={user.username} role={user.role}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()
