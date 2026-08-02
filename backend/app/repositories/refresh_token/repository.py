from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            RefreshToken,
            db,
        )

    def get_by_token(
        self,
        token: str,
    ) -> RefreshToken | None:

        result = self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == token,
            )
        )

        return result.scalars().first()

    def issue(
        self,
        user_id: str,
        token: str,
        expires_at: datetime,
    ) -> RefreshToken:

        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )

        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)

        return refresh_token
