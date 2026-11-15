"""Medienwelt: book preview + reading position, manual book payments, song audio metadata.

Additive only (nothing is rewritten or deleted; existing books, songs, progress and purchases keep every value):
  * media_books.preview_pages_count (default 10 = the first 10 pages of a PAID book are free to read), media_books.page_count (nullable;
    read from the PDF when the file is uploaded or the book is first opened)
  * media_progress.scroll_position (0..1 inside the page) and last_opened_at
  * songs.audio_format / bitrate_kbps / metadata_status (default 'OK') / metadata_note
  * book_payment_requests (new): a student's card payment for a PAID book, PENDING until the Super Admin decides
  * media_purchases.payment_request_id (nullable): the approved payment that created the purchase
Downgrade drops exactly these (receipt files on disk stay).

Revision ID: c2f7a9d1e4b6
Revises: b6e2d9f4a1c8
Create Date: 2026-11-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c2f7a9d1e4b6"
down_revision: Union[str, Sequence[str], None] = "b6e2d9f4a1c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.add_column("media_books", sa.Column("preview_pages_count", sa.Integer(), nullable=False, server_default="10"))
    op.add_column("media_books", sa.Column("page_count", sa.Integer(), nullable=True))

    op.add_column("media_progress", sa.Column("scroll_position", sa.Float(), nullable=True))
    op.add_column("media_progress", sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("songs", sa.Column("audio_format", sa.String(10), nullable=True))
    op.add_column("songs", sa.Column("bitrate_kbps", sa.Integer(), nullable=True))
    op.add_column("songs", sa.Column("metadata_status", sa.String(10), nullable=False, server_default="OK"))
    op.add_column("songs", sa.Column("metadata_note", sa.String(300), nullable=True))

    op.create_table(
        "book_payment_requests",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE", name="fk_book_payment_requests_user_id"), nullable=False),
        sa.Column("book_id", UUID, sa.ForeignKey("media_books.id", ondelete="SET NULL", name="fk_book_payment_requests_book_id"), nullable=True),
        sa.Column("book_title", sa.String(255), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="UZS"),
        sa.Column("receipt_key", sa.String(300), nullable=True),
        sa.Column("receipt_type", sa.String(10), nullable=True),
        sa.Column("receipt_size", sa.Integer(), nullable=True),
        sa.Column("no_receipt", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("transfer_date", sa.Date(), nullable=True),
        sa.Column("transfer_time", sa.Time(), nullable=True),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("card_last4", sa.String(4), nullable=True),
        sa.Column("payment_status", sa.String(10), nullable=False, server_default="PENDING"),
        sa.Column("admin_note", sa.String(500), nullable=True),
        sa.Column("reviewed_by_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL", name="fk_book_payment_requests_reviewed_by_id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("payment_status IN ('PENDING','APPROVED','REJECTED','CANCELLED')", name="ck_book_payment_requests_status"),
        sa.CheckConstraint("amount > 0", name="ck_book_payment_requests_amount"),
    )
    for column in ("user_id", "book_id", "reviewed_by_id", "payment_status"):
        op.create_index(f"ix_book_payment_requests_{column}", "book_payment_requests", [column])
    op.create_index("uq_book_payment_requests_open", "book_payment_requests", ["user_id", "book_id"], unique=True,
                    postgresql_where=sa.text("payment_status = 'PENDING'"))

    op.add_column("media_purchases", sa.Column("payment_request_id", UUID, nullable=True))
    op.create_foreign_key("fk_media_purchases_payment_request_id", "media_purchases", "book_payment_requests", ["payment_request_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_media_purchases_payment_request_id", "media_purchases", ["payment_request_id"])


def downgrade() -> None:
    op.drop_index("ix_media_purchases_payment_request_id", table_name="media_purchases")
    op.drop_constraint("fk_media_purchases_payment_request_id", "media_purchases", type_="foreignkey")
    op.drop_column("media_purchases", "payment_request_id")
    op.drop_table("book_payment_requests")
    for column in ("metadata_note", "metadata_status", "bitrate_kbps", "audio_format"):
        op.drop_column("songs", column)
    op.drop_column("media_progress", "last_opened_at")
    op.drop_column("media_progress", "scroll_position")
    op.drop_column("media_books", "page_count")
    op.drop_column("media_books", "preview_pages_count")
