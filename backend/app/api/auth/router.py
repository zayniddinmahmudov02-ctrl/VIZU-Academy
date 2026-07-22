from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)

from sqlalchemy.orm import Session

from app.core.security import (
    create_user_token,
)
from app.core.utils import parse_user_agent

from app.db.session import get_db

from app.models.login_history import LoginHistory

from app.schemas.auth.user import (
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
)

from app.services.auth.service import (
    authenticate_user,
    create_user,
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

    token = create_user_token(user)

    return {
        "access_token": token,
        "token_type": "bearer",
    }