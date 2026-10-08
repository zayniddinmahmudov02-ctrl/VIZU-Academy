import secrets
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    BackgroundTasks,
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
from app.core.logging.logger import logger
from app.models.email_verification_code import PURPOSE_PASSWORD_RESET, PURPOSE_REGISTRATION
from app.schemas.auth.password import (
    EmailCodeRequest,
    EmailRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    ResetPasswordRequest,
    VerifyAdminPasswordRequest,
    VerifyCodeResponse,
)
from app.schemas.auth.telegram import TelegramAuthRequest
from app.schemas.auth.user import (
    RegisterResponse,
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
)

from app.services.auth import email_code_service as codes
from app.services.auth.email_code_service import CodeCheck, RateLimited
from app.services.auth.service import (
    apply_password_reset,
    authenticate_user,
    can_receive_email,
    create_user,
    display_name,
    get_or_create_telegram_user,
    get_user_by_email,
    issue_token_pair,
    mark_email_verified,
    needs_email_verification,
    refresh_access_token,
    revoke_refresh_token,
)
from app.services.email.email_service import EmailDeliveryError, EmailService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# Generic answers that never reveal whether an address is registered.
GENERIC_RESET_MESSAGE = "Falls diese E-Mail-Adresse registriert ist, wurde ein Bestätigungscode gesendet."
GENERIC_RESEND_MESSAGE = "Falls für diese E-Mail-Adresse eine Bestätigung aussteht, wurde ein neuer Code gesendet."


def _client_ip(request: Request) -> str | None:
    """Real client IP behind Cloudflare / nginx (used for rate limiting only)."""
    forwarded = request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for", "").split(",")[0]
    return forwarded.strip() or (request.client.host if request.client else None)


def _rate_limited(exc: RateLimited) -> HTTPException:
    return HTTPException(status_code=429, detail="RATE_LIMITED", headers={"Retry-After": str(exc.retry_after)})


def _code_error(result: CodeCheck) -> HTTPException:
    return HTTPException(status_code=400, detail=result.value)


def _send_code_email(user_id, purpose: str) -> None:
    """Background job: issue + e-mail a code. The HTTP response never
    depends on it, so its timing reveals nothing about the account."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if user is None:
            return
        code = codes.issue_code(db, user, purpose)
        service = EmailService()
        if purpose == PURPOSE_REGISTRATION:
            service.send_verification_code(user.email, display_name(user), code)
        else:
            service.send_password_reset_code(user.email, display_name(user), code)
    except EmailDeliveryError:
        user = db.get(User, user_id)
        if user is not None:
            codes.invalidate_active(db, user, purpose)
            db.commit()
    except Exception:
        logger.exception("Code e-mail job failed: purpose=%s", purpose)
    finally:
        db.close()


@router.post(
    "/register",
    response_model=RegisterResponse,
)
def register(
    data: UserRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    """Creates the account (unverified) and e-mails a 6-digit code. If the
    e-mail cannot be sent, the account still exists and the user can request
    a new code on the verification page."""

    user = create_user(
        db,
        data,
    )

    sent = False
    try:
        codes.check_and_record_send(db, PURPOSE_REGISTRATION, user.email, _client_ip(request))
        code = codes.issue_code(db, user, PURPOSE_REGISTRATION)
        try:
            EmailService().send_verification_code(user.email, display_name(user), code)
            sent = True
            logger.info("Email verification code sent: user_id=%s", user.id)
        except EmailDeliveryError:
            codes.invalidate_active(db, user, PURPOSE_REGISTRATION)
            db.commit()
    except RateLimited:
        pass

    return RegisterResponse(
        **UserResponse.model_validate(user).model_dump(),
        email_verification_required=True,
        verification_email_sent=sent,
    )


@router.post(
    "/verify-email",
    response_model=MessageResponse,
)
def verify_email(
    data: EmailCodeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Confirms the address with the 6-digit code (single use)."""
    try:
        codes.check_and_record_verify(db, _client_ip(request))
    except RateLimited as exc:
        raise _rate_limited(exc)
    user = get_user_by_email(db, data.email)
    if user is None or not needs_email_verification(user):
        raise _code_error(CodeCheck.INVALID)
    result = codes.check_code(db, user, PURPOSE_REGISTRATION, data.code, consume=True)
    if result is not CodeCheck.OK:
        raise _code_error(result)
    mark_email_verified(db, user)
    logger.info("Email address verified: user_id=%s", user.id)
    return {"message": "E-Mail-Adresse erfolgreich bestätigt."}


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
)
def resend_verification(
    data: EmailRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """New registration code (the previous one becomes invalid). Same answer
    for every address; 429 while the cooldown / hourly limit applies."""
    try:
        codes.check_and_record_send(db, PURPOSE_REGISTRATION, data.email, _client_ip(request))
    except RateLimited as exc:
        raise _rate_limited(exc)
    user = get_user_by_email(db, data.email)
    if user is not None and needs_email_verification(user):
        background_tasks.add_task(_send_code_email, user.id, PURPOSE_REGISTRATION)
        logger.info("Email verification code re-requested: user_id=%s", user.id)
    return {"message": GENERIC_RESEND_MESSAGE}


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
    if needs_email_verification(user):
        # Correct password, but the address is not confirmed yet: no session.
        raise HTTPException(
            status_code=403,
            detail="EMAIL_NOT_VERIFIED",
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
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Sends a 6-digit reset code. Never reveals whether the address is
    registered: same message, the e-mail goes out in the background, and the
    rate limit counts every request alike."""
    try:
        codes.check_and_record_send(db, PURPOSE_PASSWORD_RESET, data.email, _client_ip(request))
    except RateLimited as exc:
        raise _rate_limited(exc)
    user = get_user_by_email(db, data.email)
    if user is not None and can_receive_email(user) and user.is_active:
        background_tasks.add_task(_send_code_email, user.id, PURPOSE_PASSWORD_RESET)
        logger.info("Password reset code requested: user_id=%s", user.id)

    return ForgotPasswordResponse(message=GENERIC_RESET_MESSAGE)


@router.post(
    "/verify-reset-code",
    response_model=VerifyCodeResponse,
)
def verify_reset_code(
    data: EmailCodeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Checks the reset code before the new-password step (does not use it
    up; wrong guesses count against it)."""
    try:
        codes.check_and_record_verify(db, _client_ip(request))
    except RateLimited as exc:
        raise _rate_limited(exc)
    user = get_user_by_email(db, data.email)
    result = codes.check_code(db, user, PURPOSE_PASSWORD_RESET, data.code, consume=False)
    if result is not CodeCheck.OK:
        raise _code_error(result)
    return {"valid": True}


@router.post(
    "/reset-password",
    response_model=MessageResponse,
)
def reset_password(
    data: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Sets the new password with a valid reset code (single use) and ends
    every existing session of the account."""
    try:
        codes.check_and_record_verify(db, _client_ip(request))
    except RateLimited as exc:
        raise _rate_limited(exc)
    user = get_user_by_email(db, data.email)
    result = codes.check_code(db, user, PURPOSE_PASSWORD_RESET, data.code, consume=True)
    if result is not CodeCheck.OK:
        raise _code_error(result)
    apply_password_reset(db, user, data.new_password)
    logger.info("Password reset completed: user_id=%s", user.id)
    return {"message": "Passwort erfolgreich zurückgesetzt."}


@router.post("/verify-admin-password")
def verify_admin_password(
    data: VerifyAdminPasswordRequest,
    current_user: User = Depends(require_super_admin),
):

    expected = settings.SUPER_ADMIN_VERIFICATION_PASSWORD
    if not expected:
        # Configuration error — never fall back to a built-in password.
        logger.error("SUPER_ADMIN_VERIFICATION_PASSWORD is not configured; admin verification refused.")
        raise HTTPException(
            status_code=503,
            detail="ADMIN_VERIFICATION_NOT_CONFIGURED",
        )

    if not secrets.compare_digest(
        data.password.encode("utf-8"),
        expected.encode("utf-8"),
    ):
        raise HTTPException(
            status_code=403,
            detail="Incorrect administrator password.",
        )

    return {"message": "Admin verification successful."}