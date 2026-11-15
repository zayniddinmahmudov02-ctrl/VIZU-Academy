"""Manual card payments for PAID books (Bibliothek).

Flow: the student sees the academy's card number, transfers the price, and sends a payment request — with a receipt (JPEG / PNG / WebP / PDF),
or, without one, the date and time of the transfer. The request is PENDING and gives NO access. Only the Super Admin can APPROVE it (the book
then opens: a `media_purchases` row becomes GRANTED, linked to the request) or REJECT it with a reason; the student can CANCEL a pending one and
send a new request after a rejection / cancellation.

Rules that are enforced here, not in the browser
  * the amount is the book's price read from the database at the moment of the request — a price sent by the client is not accepted;
  * one open (PENDING) request per student and book (database unique index), at most a few submissions per hour (rate limit);
  * receipts: content-checked, size-limited, images re-encoded (EXIF / location data removed), random names in the private storage, never a public
    URL — only the owner and the Super Admin can fetch one, with `no-store`, `nosniff` and a sandboxing CSP;
  * a decision works only on a PENDING request (row lock): a request can be approved or rejected exactly once; nobody reviews their own request;
  * every submission and decision is written to the audit log (card numbers are never logged)."""

from __future__ import annotations

import asyncio
import io
import logging
import re
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.security.roles import UserRole
from app.models.app_setting import AppSetting
from app.models.medien import (ACCESS_PAID, KIND_BOOK, PAYMENT_APPROVED, PAYMENT_CANCELLED, PAYMENT_PENDING, PAYMENT_REJECTED, PAYMENT_STATUSES,
                               PURCHASE_GRANTED, PURCHASE_REQUESTED, BookPaymentRequest, MediaBook, MediaPurchase)
from app.models.user import User
from app.services.auth import rate_limit
from app.services.medien import common as c
from app.services.vizu_pay import plans as vizu_pay_plans

log = logging.getLogger("vizu.medien.payments")

SETTINGS_KEY = "medien_book_payment"
TASHKENT = timezone(timedelta(hours=5))  # Uzbekistan has no daylight saving time
MAX_TRANSFER_AGE = timedelta(days=30)
MAX_NOTE = 500
MAX_REASON = 500
MIN_REASON = 3
MAX_PIXELS = 30_000_000
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f​-‏‪-‮﻿]")
_TIME = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


# ---------------- card settings ----------------


def _digits(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")


def payment_info(db: Session) -> dict:
    """The card students pay to. The Super Admin can set the number and the holder; without a setting the academy's VIZU Pay card is used."""
    stored = db.scalar(select(AppSetting.value).where(AppSetting.key == SETTINGS_KEY)) or {}
    number = _digits(stored.get("card_number")) or _digits((vizu_pay_plans.PAYMENT_CARDS or [{}])[0].get("number"))
    return {"card_number": number, "card_holder": (stored.get("card_holder") or "").strip(), "currency": "UZS", "configured": bool(number)}


def save_payment_settings(db: Session, user: User, data: dict) -> dict:
    row = db.scalar(select(AppSetting).where(AppSetting.key == SETTINGS_KEY).with_for_update())
    value = dict(row.value or {}) if row else {}
    if "card_number" in data:
        raw = str(data["card_number"] or "")
        number = _digits(raw)
        if re.search(r"[^\d\s-]", raw) or (number and not 16 <= len(number) <= 19):  # digits (spaces / dashes allowed); empty = the default card
            raise c.err(422, "INVALID_CARD_NUMBER: a card number has 16 to 19 digits.")
        value["card_number"] = number
    if "card_holder" in data:
        holder = " ".join(_CONTROL.sub(" ", str(data["card_holder"] or "")).split())
        if len(holder) > 80:
            raise c.err(422, "CARD_HOLDER_TOO_LONG: at most 80 characters.")
        value["card_holder"] = holder
    if row is None:
        db.add(AppSetting(key=SETTINGS_KEY, value=value))
    else:
        row.value = value
    db.commit()
    write_audit(db, actor_id=user.id, action="medien_book_payment_settings", details=f"card ****{_digits(value.get('card_number'))[-4:]} holder set={bool(value.get('card_holder'))}")
    return payment_info(db)


# ---------------- serialization ----------------


def _name(user: User | None) -> str | None:
    if user is None:
        return None
    return f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username


def serialize(row: BookPaymentRequest, *, admin: bool = False, user: User | None = None, reviewer: User | None = None) -> dict:
    out = {"id": row.id, "book_id": row.book_id, "book_title": row.book_title, "amount": row.amount, "currency": row.currency, "status": row.payment_status,
           "has_receipt": bool(row.receipt_key), "receipt_type": row.receipt_type, "no_receipt": row.no_receipt,
           "transfer_date": row.transfer_date.isoformat() if row.transfer_date else None,
           "transfer_time": row.transfer_time.strftime("%H:%M") if row.transfer_time else None, "note": row.note, "created_at": row.created_at,
           "reviewed_at": row.reviewed_at, "can_cancel": row.payment_status == PAYMENT_PENDING,
           # the student sees the reason of a rejection (that is what it is for); an approval note stays internal
           "admin_note": row.admin_note if (admin or row.payment_status == PAYMENT_REJECTED) else None}
    if admin:
        out.update(user_id=row.user_id, user_name=_name(user), user_email=user.email if user else None, card_last4=row.card_last4, receipt_size=row.receipt_size,
                   reviewed_by_id=row.reviewed_by_id, reviewed_by_name=_name(reviewer))
    return out


# ---------------- student side ----------------


def _clean_note(value: str | None) -> str | None:
    text = " ".join(_CONTROL.sub(" ", str(value or "")).split())
    if len(text) > MAX_NOTE:
        raise c.err(422, f"NOTE_TOO_LONG: at most {MAX_NOTE} characters.")
    return text or None


def _parse_transfer(date_text: str | None, time_text: str | None) -> tuple[date | None, time | None]:
    date_text, time_text = (date_text or "").strip(), (time_text or "").strip()
    if not date_text and not time_text:
        return None, None
    if not date_text or not time_text:
        raise c.err(422, "TRANSFER_DATE_AND_TIME_REQUIRED: give both the date and the time of the transfer.")
    try:
        day = date.fromisoformat(date_text)
    except ValueError:
        raise c.err(422, "INVALID_TRANSFER_DATE: use the format YYYY-MM-DD.") from None
    m = _TIME.match(time_text)
    if not m:
        raise c.err(422, "INVALID_TRANSFER_TIME: use the format HH:MM.")
    clock = time(int(m.group(1)), int(m.group(2)))
    moment = datetime.combine(day, clock, TASHKENT)
    now = datetime.now(TASHKENT)
    if moment > now + timedelta(minutes=5):
        raise c.err(422, "TRANSFER_IN_FUTURE: the transfer cannot be in the future.")
    if moment < now - MAX_TRANSFER_AGE:
        raise c.err(422, "TRANSFER_TOO_OLD: the transfer is older than 30 days — contact support.")
    return day, clock


def _sanitize_receipt(path: Path, ext: str) -> int:
    """Checks the stored receipt and removes what it must not keep. Images are decoded and re-saved (EXIF, GPS and any appended data are gone);
    a PDF must be a readable document of a few pages. Returns the final size; raises a coded 400 for anything else."""
    try:
        if ext == "pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(path), strict=False)
            if reader.is_encrypted or not 1 <= len(reader.pages) <= 20:
                raise ValueError("pdf")
            return path.stat().st_size
        from PIL import Image, ImageOps

        with Image.open(path) as image:
            if image.width * image.height > MAX_PIXELS:  # the header is read first: a huge image is never decoded
                raise ValueError("pixels")
            image.load()
            image = ImageOps.exif_transpose(image)
            fmt = {"jpg": "JPEG", "png": "PNG", "webp": "WEBP"}[ext]
            if fmt == "JPEG" and image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            buffer = io.BytesIO()
            image.save(buffer, fmt, **({"quality": 90} if fmt != "PNG" else {}))
        path.write_bytes(buffer.getvalue())
        return len(buffer.getvalue())
    except Exception as exc:  # any decoder problem means: not a usable receipt
        log.info("receipt refused (%s)", type(exc).__name__)
        path.unlink(missing_ok=True)
        raise c.err(400, "INVALID_RECEIPT: the receipt must be a readable JPG, PNG, WebP image or PDF.") from None


async def create_request(db: Session, user: User, book_id: UUID, *, receipt: UploadFile | None, no_receipt: bool, transfer_date: str | None,
                         transfer_time: str | None, note: str | None, ip: str | None) -> dict:
    """A payment request for `book_id`. Raises coded errors: 404 / 409 (already owned, already pending) / 422 (form) / 429 (rate limit)."""
    try:
        rate_limit.check_and_record_book_payment(db, user.id, ip)
    except rate_limit.RateLimited as exc:
        raise HTTPException(status_code=429, detail="RATE_LIMITED: too many payment requests, try again later.", headers={"Retry-After": str(exc.retry_after)}) from None
    book = c.item_or_404(db, KIND_BOOK, book_id, user)
    if book.access_type != ACCESS_PAID or not book.price:
        raise c.err(409, "NOT_PAID: this book is free.")
    if c.can_access(db, user, KIND_BOOK, book):
        raise c.err(409, "ALREADY_OWNED: you already have access to this book.")
    if db.scalar(select(BookPaymentRequest.id).where(BookPaymentRequest.user_id == user.id, BookPaymentRequest.book_id == book.id,
                                                      BookPaymentRequest.payment_status == PAYMENT_PENDING)):
        raise c.err(409, "PAYMENT_PENDING: your payment for this book is already being checked.")
    has_file = receipt is not None and bool(receipt.filename)
    day, clock = _parse_transfer(transfer_date, transfer_time)
    if not has_file and not no_receipt:
        raise c.err(422, "RECEIPT_OR_NO_RECEIPT: upload the receipt, or confirm that you have none and give the transfer date and time.")
    if not has_file and (day is None or clock is None):
        raise c.err(422, "TRANSFER_TIME_REQUIRED: without a receipt the transfer date and time are required.")
    text = _clean_note(note)
    key = ext = None
    size = None
    if has_file:
        key, ext, size = await c.save_upload(receipt, "receipts", c.sniff_receipt, c.MAX_RECEIPT, "The receipt")
        size = await asyncio.to_thread(_sanitize_receipt, c.storage.ROOT / key, ext)
    info = payment_info(db)
    row = BookPaymentRequest(user_id=user.id, book_id=book.id, book_title=book.title[:255], amount=int(book.price), currency="UZS", receipt_key=key,
                             receipt_type=ext, receipt_size=size, no_receipt=not has_file, transfer_date=day, transfer_time=clock, note=text,
                             card_last4=info["card_number"][-4:] or None, payment_status=PAYMENT_PENDING)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:  # two requests at once: the unique index lets only one PENDING row through
        db.rollback()
        await c.remove_file(key)
        raise c.err(409, "PAYMENT_PENDING: your payment for this book is already being checked.") from None
    db.refresh(row)
    write_audit(db, actor_id=user.id, action="book_payment_requested", details=f"request {row.id} book {book.id} amount {row.amount} receipt={bool(key)}", ip_address=ip)
    return serialize(row)


def my_requests(db: Session, user: User) -> list[dict]:
    rows = db.scalars(select(BookPaymentRequest).where(BookPaymentRequest.user_id == user.id).order_by(BookPaymentRequest.created_at.desc()).limit(100)).all()
    return [serialize(r) for r in rows]


def cancel_request(db: Session, user: User, request_id: UUID) -> dict:
    row = db.scalar(select(BookPaymentRequest).where(BookPaymentRequest.id == request_id, BookPaymentRequest.user_id == user.id).with_for_update())
    if row is None:  # also another student's request: indistinguishable from a missing one
        raise c.err(404, "NOT_FOUND")
    if row.payment_status != PAYMENT_PENDING:
        raise c.err(409, f"INVALID_TRANSITION: {row.payment_status} -> {PAYMENT_CANCELLED}")
    row.payment_status = PAYMENT_CANCELLED
    row.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    write_audit(db, actor_id=user.id, action="book_payment_cancelled", details=f"request {row.id}")
    return serialize(row)


def receipt_target(db: Session, user: User, request_id: UUID):
    """(path, content type) of a receipt for its owner or the Super Admin — everyone else gets the same 404 as for a missing receipt."""
    row = db.get(BookPaymentRequest, request_id)
    if row is None or not row.receipt_key or (row.user_id != user.id and user.role != UserRole.SUPER_ADMIN):
        raise c.err(404, "NOT_FOUND")
    path = c.file_path(row.receipt_key)
    if path is None:
        raise c.err(404, "FILE_MISSING")
    return path, c.CONTENT_TYPES.get(row.receipt_type or "", "application/octet-stream")


# ---------------- admin side (Super Admin) ----------------


def counts(db: Session) -> dict:
    rows = dict(db.execute(select(BookPaymentRequest.payment_status, func.count()).group_by(BookPaymentRequest.payment_status)).all())
    return {s: int(rows.get(s, 0)) for s in PAYMENT_STATUSES}


def list_requests(db: Session, *, status: str | None = None, q: str | None = None, page: int = 1, page_size: int = 30) -> dict:
    stmt = select(BookPaymentRequest, User).join(User, User.id == BookPaymentRequest.user_id)
    if status in PAYMENT_STATUSES:
        stmt = stmt.where(BookPaymentRequest.payment_status == status)
    if q and q.strip():
        like = f"%{q.strip().replace(chr(92), chr(92) * 2).replace('%', chr(92) + '%').replace('_', chr(92) + '_')}%"
        stmt = stmt.where(or_(BookPaymentRequest.book_title.ilike(like, escape="\\"), User.email.ilike(like, escape="\\"), User.username.ilike(like, escape="\\"),
                              User.first_name.ilike(like, escape="\\"), User.last_name.ilike(like, escape="\\")))
    size, page = max(1, min(page_size, 100)), max(1, page)
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    # pending first (they wait for a decision), then newest
    order = (case((BookPaymentRequest.payment_status == PAYMENT_PENDING, 0), else_=1).asc(), BookPaymentRequest.created_at.desc())
    rows = db.execute(stmt.order_by(*order).limit(size).offset((page - 1) * size)).all()
    return {"items": [serialize(r, admin=True, user=u) for r, u in rows], "total": total, "page": page, "page_size": size, "counts": counts(db)}


def get_request(db: Session, request_id: UUID) -> dict:
    """One request with everything the admin checks before deciding: the student, the book now (price may have changed), the student's earlier
    requests for it and the purchase history."""
    row = db.get(BookPaymentRequest, request_id)
    if row is None:
        raise c.err(404, "NOT_FOUND")
    user = db.get(User, row.user_id)
    reviewer = db.get(User, row.reviewed_by_id) if row.reviewed_by_id else None
    book = db.get(MediaBook, row.book_id) if row.book_id else None
    history = db.scalars(select(BookPaymentRequest).where(BookPaymentRequest.user_id == row.user_id, BookPaymentRequest.book_id == row.book_id,
                                                          BookPaymentRequest.id != row.id).order_by(BookPaymentRequest.created_at.desc()).limit(20)).all() if row.book_id else []
    purchases = db.scalars(select(MediaPurchase).where(MediaPurchase.user_id == row.user_id).order_by(MediaPurchase.created_at.desc()).limit(30)).all()
    bought = []
    for p in purchases:
        item = db.get(c.MODELS[p.content_type], p.content_id)
        bought.append({"id": p.id, "kind": p.content_type, "title": item.title if item else None, "status": p.status, "price": p.price,
                       "decided_at": p.decided_at, "payment_request_id": p.payment_request_id})
    return {**serialize(row, admin=True, user=user, reviewer=reviewer), "book_exists": book is not None, "book_price": book.price if book else None,
            "book_access": book.access_type if book else None,
            "history": [serialize(h, admin=True, user=user) for h in history], "purchases": bought}


def decide(db: Session, admin: User, request_id: UUID, decision: str, note: str | None, ip: str | None = None) -> dict:
    """APPROVED opens the book for the student; REJECTED (reason required) keeps it closed. Works once, on a PENDING request only."""
    if decision not in (PAYMENT_APPROVED, PAYMENT_REJECTED):
        raise c.err(422, "INVALID_DECISION: APPROVED or REJECTED.")
    row = db.scalar(select(BookPaymentRequest).where(BookPaymentRequest.id == request_id).with_for_update())
    if row is None:
        raise c.err(404, "NOT_FOUND")
    if row.payment_status != PAYMENT_PENDING:
        raise c.err(409, f"INVALID_TRANSITION: {row.payment_status} -> {decision}")
    if row.user_id == admin.id:
        raise c.err(403, "SELF_REVIEW_FORBIDDEN: nobody decides on their own payment.")
    text = " ".join(_CONTROL.sub(" ", str(note or "")).split())
    if len(text) > MAX_REASON:
        raise c.err(422, f"NOTE_TOO_LONG: at most {MAX_REASON} characters.")
    if decision == PAYMENT_REJECTED and len(text) < MIN_REASON:
        raise c.err(422, "REASON_REQUIRED: tell the student why the payment is rejected.")
    now = datetime.now(timezone.utc)
    if decision == PAYMENT_APPROVED:
        book = db.get(MediaBook, row.book_id) if row.book_id else None
        if book is None:
            raise c.err(409, "BOOK_GONE: the book no longer exists.")
        purchase = db.scalar(select(MediaPurchase).where(MediaPurchase.user_id == row.user_id, MediaPurchase.content_type == KIND_BOOK,
                                                          MediaPurchase.content_id == book.id, MediaPurchase.status.in_((PURCHASE_REQUESTED, PURCHASE_GRANTED))).with_for_update())
        if purchase is None:
            purchase = MediaPurchase(user_id=row.user_id, content_type=KIND_BOOK, content_id=book.id)
            db.add(purchase)
        if purchase.status != PURCHASE_GRANTED:  # an existing GRANTED row (direct grant) is kept as it is — no second purchase for one book
            purchase.status, purchase.price = PURCHASE_GRANTED, row.amount
            purchase.decided_by_id, purchase.decided_at = admin.id, now
        purchase.payment_request_id = purchase.payment_request_id or row.id
        purchase.note = (text or purchase.note or "")[:500] or None
        db.flush()
    row.payment_status, row.admin_note = decision, text or None
    row.reviewed_by_id, row.reviewed_at = admin.id, now
    db.commit()
    write_audit(db, actor_id=admin.id, action=f"book_payment_{decision.lower()}", target_user_id=row.user_id, details=f"request {row.id} book {row.book_id} amount {row.amount}", ip_address=ip)
    return get_request(db, row.id)
