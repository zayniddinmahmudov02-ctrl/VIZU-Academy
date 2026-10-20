from fastapi import APIRouter
from fastapi import Depends, Query

from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access, require_super_admin
from app.db.session import get_db

from app.models.user import User

from app.schemas.admin import (
    AdminDashboardOverview,
    EnterpriseDashboardResponse,
)

from app.services.admin import (
    AdminService,
)
from app.services.admin.enterprise_dashboard_service import EnterpriseDashboardService

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get(
    "/dashboard",
    response_model=EnterpriseDashboardResponse,
)
def dashboard(
    range: str = Query(default="30d", pattern="^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    """Enterprise Dashboard. One optimized endpoint returning everything the
    dashboard needs (KPIs, charts, learning analytics, mock test analytics,
    VIZU-Multilevel, payments, content counts, AI stats, recent activity,
    server health) — see EnterpriseDashboardService. Every admin-panel role
    may open it; revenue / payments and server health are returned only to
    the roles allowed to see them (FINANCE_ROLES / SYSTEM_ROLES), else null."""

    return EnterpriseDashboardService(db).get_dashboard(range, role=str(current_user.role))


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
