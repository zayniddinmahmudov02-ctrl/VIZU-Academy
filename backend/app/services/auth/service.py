from uuid import UUID

from fastapi import HTTPException

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
)

from app.models.user import User

from app.schemas.auth.user import (
    UserRegister,
)


def create_user(
    db: Session,
    data: UserRegister,
) -> User:

    existing_email = db.scalar(
        select(User).where(
            User.email == data.email,
        )
    )

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email already exists.",
        )

    existing_username = db.scalar(
        select(User).where(
            User.username == data.username,
        )
    )

    if existing_username:
        raise HTTPException(
            status_code=409,
            detail="Username already exists.",
        )

    user = User(
        email=data.email,
        username=data.username,
        password_hash=hash_password(
            data.password,
        ),
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
):

    user = db.scalar(
        select(User).where(
            User.email == email,
        )
    )

    if user is None:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user


def get_user_by_id(
    db: Session,
    user_id: str,
):

    return db.get(
        User,
        UUID(user_id),
    )