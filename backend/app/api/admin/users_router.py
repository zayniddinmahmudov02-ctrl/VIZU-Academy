import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import (
    AuditLogResponse,
    BanRequest,
    DeviceHistoryItem,
    ExtendSubscriptionRequest,
    GrantPremiumRequest,
    ImpersonateResponse,
    LoginHistoryResponse,
    PaymentHistoryItem,
    ResetPasswordResponse,
    SubscriptionInfo,
    SuspendRequest,
    TagRequest,
    UserDetail,
    UserListResponse,
    UserProgressResponse,
    UserTagItem,
)
from app.services.admin.users_service import AdminUsersService

router = APIRouter(
    prefix="/admin/users",
    tags=["Admin - Users"],
)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


EXPORT_HEADERS = [
    "Email", "Username", "Role", "Active", "Verified", "Banned", "Suspended",
    "Premium", "Premium Until", "Last Login", "Created At", "Tags",
]


def _export_rows(rows: list[dict]) -> list[list]:
    return [
        [
            row["email"],
            row["username"],
            row["role"],
            row["is_active"],
            row["is_verified"],
            row["is_banned"],
            row["is_suspended"],
            row["is_premium"],
            row["premium_until"] or "",
            row["last_login"] or "",
            row["created_at"],
            ", ".join(t["label"] for t in row["tags"]),
        ]
        for row in rows
    ]


@router.get("", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    role: str | None = None,
    status: str | None = None,
    tag: str | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).list_users(
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        status=status,
        tag=tag,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.get("/export.csv")
def export_users_csv(
    search: str | None = None,
    role: str | None = None,
    status: str | None = None,
    tag: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    rows = AdminUsersService(db).list_all_for_export(search=search, role=role, status=status, tag=tag)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(EXPORT_HEADERS)
    writer.writerows(_export_rows(rows))

    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users_export.csv"},
    )


@router.get("/export.xlsx")
def export_users_excel(
    search: str | None = None,
    role: str | None = None,
    status: str | None = None,
    tag: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    from openpyxl import Workbook

    rows = AdminUsersService(db).list_all_for_export(search=search, role=role, status=status, tag=tag)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Users"
    sheet.append(EXPORT_HEADERS)

    for row in _export_rows(rows):
        sheet.append(row)

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=users_export.xlsx"},
    )


@router.get("/{user_id}", response_model=UserDetail)
def get_user_detail(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    detail = AdminUsersService(db).get_detail(user_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="User not found")
    return detail


@router.get("/{user_id}/progress", response_model=UserProgressResponse)
def get_user_progress(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).get_progress(user_id)


@router.get("/{user_id}/login-history", response_model=LoginHistoryResponse)
def get_user_login_history(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).get_login_history(user_id, page=page, page_size=page_size)


@router.get("/{user_id}/device-history", response_model=list[DeviceHistoryItem])
def get_user_device_history(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).get_device_history(user_id)


@router.get("/{user_id}/activity")
def get_user_activity(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).get_activity_timeline(user_id)


@router.get("/{user_id}/payments", response_model=list[PaymentHistoryItem])
def get_user_payments(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).get_payment_history(user_id)


@router.get("/{user_id}/subscription", response_model=SubscriptionInfo)
def get_user_subscription(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).get_subscription(user_id)


@router.post("/{user_id}/grant-premium", response_model=UserDetail)
def grant_premium(
    user_id: str,
    data: GrantPremiumRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).grant_premium(user_id, data.days, current_user, _client_ip(request))


@router.post("/{user_id}/extend-subscription", response_model=UserDetail)
def extend_subscription(
    user_id: str,
    data: ExtendSubscriptionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).extend_subscription(user_id, data.days, current_user, _client_ip(request))


@router.post("/{user_id}/ban", response_model=UserDetail)
def ban_user(
    user_id: str,
    data: BanRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).ban(user_id, data.reason, current_user, _client_ip(request))


@router.post("/{user_id}/unban", response_model=UserDetail)
def unban_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).unban(user_id, current_user, _client_ip(request))


@router.post("/{user_id}/suspend", response_model=UserDetail)
def suspend_user(
    user_id: str,
    data: SuspendRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).suspend(user_id, data.days, data.reason, current_user, _client_ip(request))


@router.post("/{user_id}/unsuspend", response_model=UserDetail)
def unsuspend_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).unsuspend(user_id, current_user, _client_ip(request))


@router.post("/{user_id}/reset-password", response_model=ResetPasswordResponse)
def reset_password(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    temp_password = AdminUsersService(db).reset_password(user_id, current_user, _client_ip(request))
    return {"temporary_password": temp_password}


@router.post("/{user_id}/tags", response_model=list[UserTagItem])
def add_tag(
    user_id: str,
    data: TagRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).add_tag(user_id, data.label, current_user)


@router.delete("/{user_id}/tags/{tag_id}", response_model=list[UserTagItem])
def remove_tag(
    user_id: str,
    tag_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).remove_tag(user_id, tag_id, current_user)


@router.post("/{user_id}/impersonate", response_model=ImpersonateResponse)
def impersonate_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    token, user_payload = AdminUsersService(db).impersonate(user_id, current_user, _client_ip(request))
    return {"access_token": token, "token_type": "bearer", "user": user_payload}


@router.get("/{user_id}/audit-log", response_model=AuditLogResponse)
def get_user_audit_log(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminUsersService(db).get_audit_log(user_id=user_id, page=page, page_size=page_size)
