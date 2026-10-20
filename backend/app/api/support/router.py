"""Hilfe benötigt / Support — student API (own tickets only) and the admin
"Support / Hilfeanfragen" API (support roles only)."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.audit import write_audit
from app.db.session import get_db
from app.models.user import User
from app.services import support as service

router = APIRouter(prefix="/support", tags=["Support"])


class TicketIn(BaseModel):
    subject: str = Field(max_length=500)
    category: str = Field(max_length=20)
    message: str = Field(max_length=20_000)
    request_id: str | None = Field(default=None, max_length=64)


class MessageIn(BaseModel):
    message: str = Field(max_length=20_000)
    request_id: str | None = Field(default=None, max_length=64)


@router.get("/tickets")
def my_tickets(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.list_own(db, user, page, page_size)


@router.post("/tickets", status_code=201)
def create_ticket(data: TicketIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The student is the logged-in user. A repeated submit returns the same ticket (`created: false`)."""
    ticket, created = service.create_ticket(db, user, data.subject, data.category, data.message, data.request_id)
    return {**service.detail(db, ticket, staff_view=False), "created": created}


@router.get("/tickets/{ticket_id}")
def my_ticket(ticket_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.detail(db, service.own_ticket(db, user, ticket_id), staff_view=False)


@router.post("/tickets/{ticket_id}/messages")
def add_message(ticket_id: UUID, data: MessageIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ticket = service.add_student_message(db, user, ticket_id, data.message, data.request_id)
    return service.detail(db, ticket, staff_view=False)


# ============================================================
# Admin
# ============================================================

admin_router = APIRouter(prefix="/admin/support", tags=["Admin - Support"])


def support_staff(current_user: User = Depends(get_current_user)) -> User:
    service.require_support_staff(current_user)
    return current_user


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@admin_router.get("/tickets")
def list_tickets(
    status: str | None = None, category: str | None = None, q: str | None = None, date_from: datetime | None = None,
    date_to: datetime | None = None, assigned: str | None = None, page: int = 1, page_size: int = 25,
    db: Session = Depends(get_db), staff: User = Depends(support_staff),
):
    return service.staff_list(db, status=status, category=category, q=q, date_from=date_from, date_to=date_to, assigned=assigned, me=staff,
                              page=page, page_size=page_size)


@admin_router.get("/staff")
def list_staff(db: Session = Depends(get_db), _: User = Depends(support_staff)):
    rows = db.scalars(select(User).where(User.role.in_(service.SUPPORT_ROLES), User.is_active.is_(True)).order_by(User.first_name)).all()
    return [{"id": str(u.id), "name": service._name(u), "role": u.role} for u in rows]


@admin_router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: UUID, db: Session = Depends(get_db), _: User = Depends(support_staff)):
    return service.detail(db, service.staff_ticket(db, ticket_id), staff_view=True)


class ReplyIn(BaseModel):
    message: str = Field(max_length=20_000)
    status: str | None = Field(default=None, max_length=20)
    request_id: str | None = Field(default=None, max_length=64)


@admin_router.post("/tickets/{ticket_id}/reply")
def reply(ticket_id: UUID, data: ReplyIn, request: Request, db: Session = Depends(get_db), staff: User = Depends(support_staff)):
    ticket = service.staff_reply(db, staff, ticket_id, data.message, data.status, data.request_id)
    write_audit(db, str(staff.id), "support_reply", target_user_id=str(ticket.user_id), details=f"{service.display_number(ticket)} -> {ticket.status}",
                ip_address=_ip(request))
    return service.detail(db, ticket, staff_view=True)


class StatusIn(BaseModel):
    status: str = Field(max_length=20)


@admin_router.patch("/tickets/{ticket_id}/status")
def change_status(ticket_id: UUID, data: StatusIn, request: Request, db: Session = Depends(get_db), staff: User = Depends(support_staff)):
    ticket = service.set_status(db, ticket_id, data.status)
    write_audit(db, str(staff.id), "support_status", target_user_id=str(ticket.user_id), details=f"{service.display_number(ticket)} -> {ticket.status}",
                ip_address=_ip(request))
    return service.detail(db, ticket, staff_view=True)


class AssignIn(BaseModel):
    assignee_id: UUID | None = None


@admin_router.patch("/tickets/{ticket_id}/assign")
def assign(ticket_id: UUID, data: AssignIn, request: Request, db: Session = Depends(get_db), staff: User = Depends(support_staff)):
    ticket = service.assign(db, ticket_id, data.assignee_id)
    write_audit(db, str(staff.id), "support_assign", target_user_id=str(ticket.user_id),
                details=f"{service.display_number(ticket)} -> {data.assignee_id or 'none'}", ip_address=_ip(request))
    return service.detail(db, ticket, staff_view=True)
