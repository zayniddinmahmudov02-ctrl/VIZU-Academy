from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Sequence, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

CATEGORIES = ("COURSE", "PAYMENT", "MEDIA", "TESTS", "CERTIFICATE", "TECHNICAL", "OTHER")

S_NEW = "NEW"  # Neu
S_IN_PROGRESS = "IN_PROGRESS"  # In Bearbeitung
S_WAITING = "WAITING"  # Warten auf Antwort (of the student)
S_ANSWERED = "ANSWERED"  # Beantwortet
S_CLOSED = "CLOSED"  # Geschlossen
STATUSES = (S_NEW, S_IN_PROGRESS, S_WAITING, S_ANSWERED, S_CLOSED)

AUTHOR_STUDENT = "STUDENT"
AUTHOR_STAFF = "STAFF"

ticket_number_seq = Sequence("support_ticket_number_seq", start=1001)


class SupportTicket(BaseModel):
    """A student's "Hilfeanfrage". The student comes from the login, never
    from the request body; `number` is the public ticket number (#1001 ...)."""

    __tablename__ = "support_tickets"
    __table_args__ = (
        UniqueConstraint("user_id", "client_request_id", name="uq_support_ticket_request"),
        Index("ix_support_tickets_status_last", "status", "last_message_at"),
    )

    number: Mapped[int] = mapped_column(Integer, ticket_number_seq, server_default=ticket_number_seq.next_value(), nullable=False, unique=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=S_NEW, server_default=S_NEW)
    assigned_to_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # idempotency: a repeated submit with the same id returns the same ticket
    client_request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user = relationship("User", foreign_keys=[user_id], lazy="joined")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], lazy="joined")


class SupportMessage(BaseModel):
    """One message of a ticket — author, role and time are kept forever
    (closing a ticket never deletes its conversation). Plain text."""

    __tablename__ = "support_messages"
    __table_args__ = (
        UniqueConstraint("ticket_id", "client_request_id", name="uq_support_message_request"),
        Index("ix_support_messages_ticket_created", "ticket_id", "created_at"),
    )

    ticket_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    author_role: Mapped[str] = mapped_column(String(10), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    client_request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    author = relationship("User", lazy="joined")
