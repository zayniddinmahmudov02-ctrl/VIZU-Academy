from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user

from app.core.security.roles import UserRole

from app.db.session import get_db

from app.models.user import User

from app.schemas.dashboard.schema import (
    DashboardResponse,
)

from app.services.dashboard.service import (
    DashboardService,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


# ==================================================
# Lernserie (own data only — there is no user id in the path)
# ==================================================

@router.get("/me/learning-activity")
def my_learning_activity(
    tz: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Streak, total learning time, last activity and the last 7 days —
    server-confirmed activity only (app.services.learning_activity). `tz` is
    the student's IANA time zone (browser); unknown -> Asia/Tashkent."""
    from app.services import learning_activity

    return learning_activity.summary(db, current_user.id, tz)


# ==================================================
# Dashboard Overview
# ==================================================

@router.get(
    "/{user_id}",
    response_model=DashboardResponse,
)
def get_dashboard(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if (
        str(user_id) != str(current_user.id)
        and current_user.role not in UserRole.ADMIN_PANEL_ROLES
    ):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this dashboard",
        )

    service = DashboardService(db)

    return service.get_dashboard(
        user_id=user_id,
    )
