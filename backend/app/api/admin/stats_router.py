"""Admin student statistics (rules: app/services/admin/student_stats.py). Fresh PostgreSQL counts on every call, no-store.

* GET /admin/stats/overview — numbers only: `require_admin_panel_access` (the dashboard that shows them has the same gate);
  `can_list_students` tells the UI whether the list below is allowed.
* GET /admin/stats/students — names / contacts (personal data): `require_super_admin`, like the Users page."""

from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access, require_super_admin
from app.core.security.roles import UserRole
from app.db.session import get_db
from app.models.user import User
from app.services.admin import student_stats

router = APIRouter(prefix="/admin/stats", tags=["Admin statistics"])


@router.get("/overview")
def stats_overview(response: Response, db: Session = Depends(get_db), user: User = Depends(require_admin_panel_access)):
    response.headers["Cache-Control"] = "no-store"
    out = student_stats.overview(db)
    out["can_list_students"] = user.role == UserRole.SUPER_ADMIN
    return out


@router.get("/students")
def stats_students(
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Literal["all", "active", "inactive", "blocked", "test_takers", "test_accounts"] = "all",
    search: str | None = Query(None, max_length=100),
    sort: Literal["newest", "oldest", "last_login", "name"] = "newest",
    db: Session = Depends(get_db),
    _admin: User = Depends(require_super_admin),
):
    response.headers["Cache-Control"] = "no-store"
    return student_stats.list_students(db, page=page, page_size=page_size, status=status, search=search, sort=sort)
