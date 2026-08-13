from datetime import datetime, timezone

from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import OAuth2PasswordBearer

from jose import ExpiredSignatureError, JWTError

from sqlalchemy.orm import Session

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

# auto_error=False — a missing/invalid token resolves to None instead of a
# 401, for endpoints that are browsable anonymously but behave differently
# for a logged-in (and possibly Premium) user, e.g. the public mock-exam
# routes.
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False,
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

    try:
        payload = decode_access_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    try:
        user = get_user_by_id(
            db=db,
            user_id=user_id,
        )
    except (ValueError, TypeError):
        # sub claim wasn't a well-formed UUID (or wasn't a string at all,
        # e.g. a forged/corrupted token) — UUID() raises ValueError for a
        # malformed string and TypeError for a non-string input.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Re-check standing on every request, not just at login — a ban or
    # suspension applied mid-session must take effect immediately instead
    # of waiting for the access token to naturally expire.
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account has been banned.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account is inactive.",
        )

    if user.suspended_until and user.suspended_until > datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account is suspended.",
        )

    return user


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> User | None:
    """Same resolution as get_current_user, but resolves to None instead
    of raising for "no token" or "invalid/expired/banned/etc" — for
    endpoints that are browsable anonymously but must still recognize a
    logged-in (and possibly Premium) caller, e.g. the public mock-exam
    routes gating content behind Premium."""
    if not token:
        return None
    try:
        return await get_current_user(token=token, db=db)
    except HTTPException:
        return None


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
