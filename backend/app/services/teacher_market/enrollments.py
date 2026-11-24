"""Course enrollment ("Anmelden"), interest lists and the payment of paid teacher courses.

* Only STUDENT accounts enroll. The course row is locked (FOR UPDATE) while the free places are counted, so two students can
  never take the last place together; one live enrollment per student and course (partial unique index → 409).
* Free course: ACTIVE at once, the student joins the course group, student + teacher are notified.
* Paid course: the student pays by card transfer and sends the receipt (or "Chek mavjud emas" + date / time) — the same manual
  VIZU Pay flow as every purchase (no online provider is configured; nothing is ever marked paid by the client). The server
  creates a PENDING order (plan TEACHER_COURSE, amount = the approved course price) and a PENDING_PAYMENT enrollment that holds
  the place. A SUPER_ADMIN approves the order in Admin → Payments → the enrollment becomes ACTIVE (activate_for_order); a
  rejection frees the place (release_for_order); a refund ends it (revoke_for_order). The existing rejection block applies.
* Upcoming course: "Interesse" only — a separate list, never an enrollment."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.models.subscription_order import SubscriptionOrder
from app.models.teacher_market import (
    COURSE_FREE,
    COURSE_PAID,
    COURSE_UPCOMING,
    EN_ACTIVE,
    EN_LIVE,
    EN_PENDING_PAYMENT,
    EN_REFUNDED,
    EN_REJECTED,
    ST_ABGESAGT,
    TeacherCourse,
    TeacherCourseEnrollment,
    TeacherCourseInterest,
)
from app.models.user import User
from app.services.teacher_market import common as c
from app.services.teacher_market import courses as courses_svc

MAX_NOTE = 1000


def _course_locked(db: Session, course_id) -> TeacherCourse:
    course = db.scalar(select(TeacherCourse).where(TeacherCourse.id == c.parse_uuid(course_id)).with_for_update(of=TeacherCourse))
    if course is None:
        raise c.err(404, "COURSE_NOT_FOUND")
    return course


def _live_enrollment(db: Session, course_id, student_id) -> TeacherCourseEnrollment | None:
    return db.scalar(select(TeacherCourseEnrollment).where(TeacherCourseEnrollment.course_id == course_id,
                                                           TeacherCourseEnrollment.student_id == student_id,
                                                           TeacherCourseEnrollment.status.in_(EN_LIVE)))


def _check_open(db: Session, course: TeacherCourse, student: User, kind: str) -> None:
    if course.approval_status != "APPROVED" or not c.listed(course.teacher, c.profile_of(db, course.teacher_id)):
        raise c.err(404, "COURSE_NOT_FOUND")
    if course.course_type != kind:
        raise c.err(409, "COURSE_TYPE_MISMATCH")
    if _live_enrollment(db, course.id, student.id) is not None:
        raise c.err(409, "ALREADY_ENROLLED")
    taken = courses_svc.seats_taken(db, course.id)
    if taken >= course.max_students:
        raise c.err(409, "COURSE_FULL")
    if not courses_svc.enrollable(db, course, taken):
        raise c.err(409, "ENROLLMENT_CLOSED")


def _activate(db: Session, course: TeacherCourse, e: TeacherCourseEnrollment) -> None:
    e.status, e.activated_at = EN_ACTIVE, c.now()
    courses_svc.join_group(db, course, e.student_id)
    link = f"/groups/{course.group_id}" if course.group_id else f"/my-teacher/{course.teacher_id}?course={course.id}"
    c.notify(db, e.student_id, "Kursga yozildingiz / Anmeldung bestätigt", f"«{course.title}» — {c.display_name(course.teacher)}.", link, course=True)
    c.notify(db, course.teacher_id, "Yangi o'quvchi / Neue Anmeldung", f"{c.display_name(e.student)} «{course.title}» kursiga yozildi.",
             f"/teacher/meine-kurse?course={course.id}")


def enroll_free(db: Session, student: User, course_id) -> dict:
    c.require_student(student)
    course = _course_locked(db, course_id)
    _check_open(db, course, student, COURSE_FREE)
    e = TeacherCourseEnrollment(course_id=course.id, student_id=student.id, status=EN_PENDING_PAYMENT, source="free", price_snapshot=0)
    e.student = student
    db.add(e)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise c.err(409, "ALREADY_ENROLLED") from None
    _activate(db, course, e)
    db.commit()
    return {"enrollment_id": e.id, "status": e.status, "group_id": course.group_id}


def interest(db: Session, student: User, course_id, on: bool) -> dict:
    c.require_student(student)
    course = db.get(TeacherCourse, c.parse_uuid(course_id))
    if course is None or course.approval_status != "APPROVED" or not c.listed(course.teacher, c.profile_of(db, course.teacher_id)):
        raise c.err(404, "COURSE_NOT_FOUND")
    if course.course_type != COURSE_UPCOMING or course.status == ST_ABGESAGT:
        raise c.err(409, "INTEREST_NOT_POSSIBLE")
    row = db.scalar(select(TeacherCourseInterest).where(TeacherCourseInterest.course_id == course.id, TeacherCourseInterest.student_id == student.id))
    if on and row is None:
        db.add(TeacherCourseInterest(course_id=course.id, student_id=student.id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
    elif not on and row is not None:
        db.delete(row)
        db.commit()
    return {"interested": on}


def checkout(db: Session, student: User, course_id) -> dict:
    """What the payment window shows (read only; create_order checks everything again)."""
    from app.services.vizu_pay import plans as plan_config
    from app.services.vizu_pay.service import VizuPayService

    c.require_student(student)
    course = db.get(TeacherCourse, c.parse_uuid(course_id))
    if course is None or course.approval_status != "APPROVED" or course.course_type != COURSE_PAID:
        raise c.err(404, "COURSE_NOT_FOUND")
    pay = VizuPayService(db)
    mine = _live_enrollment(db, course.id, student.id)
    order = db.get(SubscriptionOrder, mine.order_id) if mine is not None and mine.order_id else None
    return {"course": {"id": course.id, "title": course.title, "teacher": c.display_name(course.teacher), "price": course.price, "currency": "UZS"},
            "cards": plan_config.PAYMENT_CARDS, "blocked": pay.is_user_blocked(student.id),
            "enrollment": {"id": mine.id, "status": mine.status} if mine else None,
            "pending_order": pay.serialize_order(order) if order is not None and order.status == "PENDING" else None,
            "can_pay": mine is None and courses_svc.enrollable(db, course)}


async def create_order(db: Session, student: User, course_id, *, no_receipt: bool, paid_date: str | None, paid_time: str | None,
                       note: str | None, proof, ip: str | None) -> dict:
    from app.services.vizu_pay import multilevel_premium, plans as plan_config
    from app.services.vizu_pay.offers import TEACHER_COURSE_PLAN
    from app.services.vizu_pay.service import MAX_PROOF_SIZE_BYTES, VizuPayService

    c.require_student(student)
    pay = VizuPayService(db)
    if pay.is_user_blocked(student.id):
        raise c.err(403, "PAYMENT_REQUEST_BLOCKED")
    paid_at = multilevel_premium._paid_at(paid_date, paid_time)
    text_ = (note or "").strip()
    if len(text_) > MAX_NOTE:
        raise c.err(422, "NOTE_TOO_LONG")
    has_file = proof is not None and bool(proof.filename)
    if no_receipt:
        if has_file:
            raise c.err(422, "RECEIPT_AND_NO_RECEIPT")
        if paid_at is None:
            raise c.err(422, "PAID_AT_REQUIRED")
    elif not has_file:
        raise c.err(422, "RECEIPT_REQUIRED")
    contents = b""
    if has_file:
        contents = await proof.read()
        if not contents:
            raise c.err(422, "RECEIPT_EMPTY")
        if len(contents) > MAX_PROOF_SIZE_BYTES:
            raise c.err(413, "RECEIPT_TOO_LARGE")
        await proof.seek(0)

    course = _course_locked(db, course_id)
    _check_open(db, course, student, COURSE_PAID)
    order_id = uuid4()
    proof_path = proof_type = None
    if has_file:
        proof_path, proof_type = pay._build_proof_path(order_id, proof, contents)
    order = SubscriptionOrder(
        id=order_id, user_id=student.id, plan=TEACHER_COURSE_PLAN, duration_days=0, included_levels=None, base_amount=course.price,
        discount_amount=0, promo_discount_amount=0, reward_discount_amount=0, final_amount=course.price, currency="UZS",
        payment_method=plan_config.PAYMENT_METHOD_UZCARD, status=plan_config.STATUS_PENDING, proof_url=proof_path, proof_type=proof_type,
        gateway="manual", expires_at=None, paid_at=paid_at, no_receipt=bool(no_receipt), student_note=text_ or None, teacher_course_id=course.id,
    )
    db.add(order)
    db.flush()
    e = TeacherCourseEnrollment(course_id=course.id, student_id=student.id, status=EN_PENDING_PAYMENT, source="payment", order_id=order.id,
                                price_snapshot=course.price)
    db.add(e)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise c.err(409, "ALREADY_ENROLLED") from None
    if has_file:
        await pay.proof_storage.upload(proof, proof_path)
    c.notify(db, student.id, "To'lov so'rovi yuborildi / Zahlung eingereicht",
             f"«{course.title}»: {course.price:,} so'm. Administrator tekshirgach kursga yozilasiz.".replace(",", " "), "/my-teacher/meine-kurse")
    c.notify_admins(db, "Kurs to'lovi / Kurszahlung", f"{c.display_name(student)}: «{course.title}» — {course.price} UZS.",
                    "/admin/payments")
    db.commit()
    db.refresh(order)
    write_audit(db, actor_id=student.id, action="order_created", target_user_id=student.id,
                details=f"{TEACHER_COURSE_PLAN} course={course.id}, final={order.final_amount} UZS, receipt={'no' if no_receipt else 'yes'}",
                ip_address=ip)
    return {"order": pay.serialize_order(order), "enrollment_id": e.id}


# ---------- hooks of AdminVizuPayService (inside its locked transaction; they never commit) ----------

def _by_order(db: Session, order: SubscriptionOrder) -> tuple[TeacherCourse | None, TeacherCourseEnrollment | None]:
    course = db.get(TeacherCourse, order.teacher_course_id) if order.teacher_course_id else None
    e = db.scalar(select(TeacherCourseEnrollment).where(TeacherCourseEnrollment.order_id == order.id).with_for_update(of=TeacherCourseEnrollment))
    return course, e


def activate_for_order(db: Session, order: SubscriptionOrder) -> None:
    course, e = _by_order(db, order)
    if course is None:
        return
    if e is None:  # the place was given up meanwhile: a paid order is honoured anyway (the admin approved the payment)
        if _live_enrollment(db, course.id, order.user_id) is not None:
            return
        e = TeacherCourseEnrollment(course_id=course.id, student_id=order.user_id, status=EN_PENDING_PAYMENT, source="payment", order_id=order.id,
                                    price_snapshot=order.final_amount)
        e.student = db.get(User, order.user_id)
        db.add(e)
        db.flush()
    if e.status == EN_PENDING_PAYMENT:
        _activate(db, course, e)
        c.notify(db, course.teacher_id, "Yangi to'lov / Neue Zahlung", f"«{course.title}»: {order.final_amount} UZS tasdiqlandi.",
                 f"/teacher/meine-kurse?course={course.id}")


def release_for_order(db: Session, order: SubscriptionOrder, reason: str | None) -> None:
    course, e = _by_order(db, order)
    if e is not None and e.status == EN_PENDING_PAYMENT:
        e.status, e.ended_at = EN_REJECTED, c.now()
        c.notify(db, e.student_id, "To'lov rad etildi / Zahlung abgelehnt", f"«{course.title if course else 'Kurs'}»: {reason or '—'}",
                 "/my-teacher/meine-kurse", course=True)


def revoke_for_order(db: Session, order: SubscriptionOrder) -> None:
    course, e = _by_order(db, order)
    if e is not None and e.status in (EN_ACTIVE, EN_PENDING_PAYMENT):
        e.status, e.ended_at = EN_REFUNDED, c.now()
        if course is not None:
            courses_svc.leave_group(db, course, e.student_id)


# ---------- student ----------

def my_courses(db: Session, student: User) -> list[dict]:
    rows = db.execute(select(TeacherCourseEnrollment, TeacherCourse).join(TeacherCourse, TeacherCourse.id == TeacherCourseEnrollment.course_id)
                      .where(TeacherCourseEnrollment.student_id == student.id).order_by(TeacherCourseEnrollment.created_at.desc())).all()
    out = []
    for e, course in rows:
        order = db.get(SubscriptionOrder, e.order_id) if e.order_id else None
        out.append({"id": e.id, "status": e.status, "created_at": e.created_at, "activated_at": e.activated_at, "price": e.price_snapshot,
                    "order": {"id": order.id, "status": order.status, "rejection_reason": order.rejection_reason} if order else None,
                    "course": {"id": course.id, "title": course.title, "level": course.level, "start_date": course.start_date,
                               "status": courses_svc.effective_status(course, courses_svc.seats_taken(db, course.id)),
                               "teacher": {"id": course.teacher_id, "name": c.display_name(course.teacher)},
                               "group_id": course.group_id if e.status == EN_ACTIVE else None}})
    return out
