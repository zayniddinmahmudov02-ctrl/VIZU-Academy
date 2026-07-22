from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.db.session import get_db

from app.models.user import User

from app.schemas.admin import (
    AdminDashboardOverview,
    AdminDashboardResponse,
)

from app.services.admin import (
    AdminService,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get(
    "/dashboard",
    response_model=AdminDashboardResponse,
)
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):

    return AdminService(
        db,
    ).dashboard()


@router.get(
    "/dashboard/overview",
    response_model=AdminDashboardOverview,
)
def dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):

    return AdminService(
        db,
    ).dashboard_overview()
