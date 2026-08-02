import bcrypt

# bcrypt only uses the first 72 bytes of the input; anything past that is
# silently ignored by the algorithm itself. We cap explicitly rather than
# let long inputs pass through unnoticed.
_MAX_PASSWORD_BYTES = 72


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:_MAX_PASSWORD_BYTES]


def hash_password(
    password: str,
) -> str:

    hashed = bcrypt.hashpw(
        _encode(password),
        bcrypt.gensalt(),
    )

    return hashed.decode("utf-8")


def verify_password(
    password: str,
    password_hash: str,
) -> bool:

    try:
        return bcrypt.checkpw(
            _encode(password),
            password_hash.encode("utf-8"),
        )
    except ValueError:
        # Malformed/unsupported hash (e.g. a corrupted or non-bcrypt
        # value) — never a real match, and never a 500 for the caller.
        return False
