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
