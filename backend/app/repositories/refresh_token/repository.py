from datetime import datetime
from uuid import UUID

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
        session_id: UUID | None = None,
    ) -> RefreshToken:

        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            session_id=session_id,
        )

        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)

        return refresh_token

    def session_is_active(
        self,
        session_id: UUID,
        now: datetime,
    ) -> bool:
        """True while the session still has an unexpired refresh token —
        the per-request check behind access-token revocation."""

        result = self.db.execute(
            select(RefreshToken.id).where(
                RefreshToken.session_id == session_id,
                RefreshToken.expires_at > now,
            ).limit(1)
        )

        return result.first() is not None

    def delete_session(
        self,
        session_id: UUID,
    ) -> None:
        """Logout: removes every refresh token of one login session."""

        self.db.query(RefreshToken).filter(
            RefreshToken.session_id == session_id,
        ).delete()

        self.db.commit()

    def delete_all_for_user(
        self,
        user_id: str,
    ) -> None:
        """Revokes every outstanding refresh token for this user — used
        after a password change so other sessions can't silently keep
        refreshing with the old credential's trust."""

        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
        ).delete()

        self.db.commit()
