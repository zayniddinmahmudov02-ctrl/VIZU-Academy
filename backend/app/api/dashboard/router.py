from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.db.session import get_db

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
):

    service = DashboardService(db)

    return service.get_dashboard(
        user_id=user_id,
    )