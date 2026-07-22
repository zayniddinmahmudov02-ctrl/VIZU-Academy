from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import OAuth2PasswordBearer

from jose import ExpiredSignatureError, JWTError

from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.core.security import (
    decode_access_token,
)
from app.core.security.roles import UserRole

from app.db.session import get_db

from app.models.user import User

from app.services.auth.service import (
    get_user_by_id,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolves the authenticated User from the bearer token.

    Every failure mode is turned into a clean 401 with a specific reason —
    never a KeyError/ValueError bubbling up as an unhandled 500. A missing
    Authorization header is already rejected by OAuth2PasswordBearer itself
    (auto_error=True) before this function runs.
    """

    # --- TEMPORARY DEBUG LOGGING (auth 401 investigation) — remove after root cause found ---
    logger.info(
        "[AUTH-DEBUG] Authorization header present, token received (len=%d, prefix=%s...)",
        len(token) if token else 0,
        token[:16] if token else None,
    )

    try:
        payload = decode_access_token(token)
        logger.info("[AUTH-DEBUG] JWT decoded successfully. payload=%s", payload)
    except ExpiredSignatureError as exc:
        logger.info("[AUTH-DEBUG] JWT decode FAILED: token expired. error=%s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except JWTError as exc:
        logger.info(
            "[AUTH-DEBUG] JWT decode FAILED: invalid token (bad signature/malformed/wrong SECRET_KEY "
            "or ALGORITHM). error=%s: %s",
            type(exc).__name__,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_id = payload.get("sub")
    logger.info("[AUTH-DEBUG] user_id extracted from 'sub' claim: %s", user_id)

    if not user_id:
        logger.info("[AUTH-DEBUG] 401 reason: payload has no 'sub' claim. Full payload=%s", payload)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    try:
        user = get_user_by_id(
            db=db,
            user_id=user_id,
        )
    except (ValueError, TypeError) as exc:
        # sub claim wasn't a well-formed UUID (or wasn't a string at all,
        # e.g. a forged/corrupted token) — UUID() raises ValueError for a
        # malformed string and TypeError for a non-string input.
        logger.info(
            "[AUTH-DEBUG] 401 reason: 'sub' claim is not a valid UUID. user_id=%s error=%s",
            user_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    if user is None:
        logger.info("[AUTH-DEBUG] 401 reason: no User row found for id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    logger.info(
        "[AUTH-DEBUG] User found: id=%s email=%s role=%s is_active=%s is_banned=%s "
        "suspended_until=%s -> AUTH SUCCESS",
        user.id,
        user.email,
        user.role,
        user.is_active,
        user.is_banned,
        user.suspended_until,
    )
    # --- END TEMPORARY DEBUG LOGGING ---

    return user


async def require_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Gate for /admin/* routes. SUPER_ADMIN only — matches the panel spec
    ("Only SUPER_ADMIN can access /admin"). Enforced here server-side; the
    frontend route guard is a UX convenience only, never the source of truth.
    """

    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )

    return current_user


async def require_admin_panel_access(
    current_user: User = Depends(get_current_user),
) -> User:
    """Broader gate for admin-panel read endpoints usable by any staff role
    (ADMIN, CONTENT_MANAGER, PAYMENT_MANAGER, SUPPORT, TEACHER), not just
    SUPER_ADMIN. Write/destructive endpoints should still use
    `require_super_admin` or a more specific role check until per-module
    permissions are built out.
    """

    if current_user.role not in UserRole.ADMIN_PANEL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin panel access required",
        )

    return current_user
