import secrets
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)

from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.core.config import settings
from app.core.utils import parse_user_agent

from app.db.session import get_db

from app.models.login_history import LoginHistory
from app.models.user import User

from app.core.security.telegram import validate_telegram_init_data
from app.schemas.auth.password import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LogoutRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    VerifyAdminPasswordRequest,
)
from app.schemas.auth.telegram import TelegramAuthRequest
from app.schemas.auth.user import (
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
)

from app.services.auth.service import (
    authenticate_user,
    create_user,
    get_or_create_telegram_user,
    issue_token_pair,
    refresh_access_token,
    request_password_reset,
    reset_password as reset_password_service,
    revoke_refresh_token,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db),
):

    return create_user(
        db,
        data,
    )


@router.post(
    "/login",
    response_model=Token,
)
def login(
    data: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):

    user = authenticate_user(
        db,
        data.email,
        data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    parsed_ua = parse_user_agent(user_agent)

    if user.is_banned:
        db.add(
            LoginHistory(
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                **parsed_ua,
            )
        )
        db.commit()
        raise HTTPException(
            status_code=403,
            detail="This account has been banned.",
        )

    if user.suspended_until and user.suspended_until > datetime.now(timezone.utc).replace(tzinfo=None):
        db.add(
            LoginHistory(
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                **parsed_ua,
            )
        )
        db.commit()
        raise HTTPException(
            status_code=403,
            detail="This account is suspended.",
        )

    db.add(
        LoginHistory(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            **parsed_ua,
        )
    )
    user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()

    return issue_token_pair(db, user)


@router.post(
    "/telegram",
    response_model=Token,
)
def telegram_login(
    data: TelegramAuthRequest,
    db: Session = Depends(get_db),
):
    """New login *method* alongside (never instead of) POST /login — same
    issue_token_pair() at the end, same Token response shape, no change
    to email/password login at all. initData is the frontend's
    Telegram.WebApp.initData (signed by Telegram); initDataUnsafe is
    never accepted here or anywhere in this flow — only the verified
    fields from validate_telegram_init_data() are ever trusted."""

    if not data.init_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram authentication data",
        )

    try:
        fields = validate_telegram_init_data(data.init_data)
    except RuntimeError:
        # Configuration error (TELEGRAM_BOT_TOKEN unset) — distinct from
        # "the data itself is invalid," so this is a 500, not a 401.
        raise HTTPException(
            status_code=500,
            detail="Telegram authentication is not configured.",
        )

    if fields is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram authentication data",
        )

    telegram_user = fields.get("user")
    if not isinstance(telegram_user, dict) or "id" not in telegram_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram authentication data",
        )

    user = get_or_create_telegram_user(db, telegram_user)

    # Same standing checks POST /login already applies — a banned/
    # suspended account must not get a second, Telegram-shaped way in.
    if user.is_banned:
        raise HTTPException(
            status_code=403,
            detail="This account has been banned.",
        )

    if user.suspended_until and user.suspended_until > datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(
            status_code=403,
            detail="This account is suspended.",
        )

    user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()

    return issue_token_pair(db, user)


@router.post(
    "/refresh",
    response_model=Token,
)
def refresh(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):

    token_pair = refresh_access_token(db, data.refresh_token)

    if token_pair is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        )

    return token_pair


@router.post("/logout")
def logout(
    data: LogoutRequest,
    db: Session = Depends(get_db),
):

    revoke_refresh_token(db, data.refresh_token)

    return {"message": "Logged out successfully."}


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
)
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):

    request_password_reset(db, data.email)

    return ForgotPasswordResponse(
        message="If an account with that email exists, a password reset link has been sent.",
    )


@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):

    success = reset_password_service(db, data.token, data.new_password)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token",
        )

    return {"message": "Password has been reset successfully."}


@router.post("/verify-admin-password")
def verify_admin_password(
    data: VerifyAdminPasswordRequest,
    current_user: User = Depends(require_super_admin),
):

    if not secrets.compare_digest(
        data.password,
        settings.SUPER_ADMIN_VERIFICATION_PASSWORD,
    ):
        raise HTTPException(
            status_code=403,
            detail="Incorrect administrator password.",
        )

    return {"message": "Admin verification successful."}