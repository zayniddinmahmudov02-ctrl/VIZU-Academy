"""Free special lessons ("Kostenlose Spezialstunde"): request → SUPER_ADMIN approval → live room in LiveKit.

* A teacher requests a one-off lesson (title, topic, description, language, level, start, 15–90 min, max participants ≤
  SPECIAL_LESSON_MAX_PARTICIPANTS, learning objectives). PENDING until a SUPER_ADMIN approves (may move the start time) or
  rejects with a reason. Nothing is visible to students and no room can exist before the approval.
* Approval: the teacher is notified, every active student gets "new special lesson", and a Global Chat announcement is posted
  in the teacher's name (pinned while the lesson is ahead or live, if a pin slot is free) — the "Live-Unterricht" strip of the
  Global Chat lists approved lessons with Join.
* Room: only the lesson's teacher (or a SUPER_ADMIN) opens it, and only from 15 minutes before the start until its end — the
  server clock decides (OPEN_WINDOW_NOT_REACHED / LESSON_OVER). The room is a video_rooms row with special_lesson_id and
  hard_end_at = start + duration (≤ 90 min); students join muted and without camera, the teacher grants microphone / camera /
  screen share per person. The server closes the room at hard_end_at (scheduler + every room access), the teacher may end
  earlier; then the lesson is ENDED (history and the chat message stay, the pin is removed).
* Every logged-in user may join an approved, live lesson while seats are free (tokens are made by the server for the caller
  only; knowing the room URL is not enough). A cancellation (teacher before the start, SUPER_ADMIN any time) ends a live room
  and tells everyone who signed up or joined."""

from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.config import settings
from app.core.security.roles import UserRole
from app.models.global_chat import MESSAGE_VISIBLE, GlobalChatMessage
from app.models.teacher_market import (
    SL_APPROVED,
    SL_CANCELLED,
    SL_ENDED,
    SL_PENDING,
    SL_REJECTED,
    SpecialLesson,
    SpecialLessonSignup,
)
from app.models.user import User
from app.models.video_room import ONLINE, ROOM_LIVE, VideoRoom, VideoRoomParticipant
from app.services.teacher_market import common as c

OPEN_BEFORE = timedelta(minutes=15)
REMIND_BEFORE = timedelta(minutes=30)
MIN_LEAD = timedelta(hours=1)
MAX_AHEAD = timedelta(days=90)
MAX_OPEN_PER_TEACHER = 10
MAX_PINS = 5


def end_of(lesson: SpecialLesson) -> datetime:
    return lesson.starts_at + timedelta(minutes=lesson.duration_minutes)


def _room(db: Session, lesson_id) -> VideoRoom | None:
    return db.scalar(select(VideoRoom).where(VideoRoom.special_lesson_id == lesson_id))


def _cap() -> int:
    return min(500, settings.SPECIAL_LESSON_MAX_PARTICIPANTS)


def _validate(data: dict, partial: bool) -> dict:
    out = {}
    if not partial or "title" in data:
        out["title"] = c.one_line(data.get("title"), "title", 200, min_len=3, required=True)
    if not partial or "topic" in data:
        out["topic"] = c.one_line(data.get("topic"), "topic", 200, min_len=2, required=True)
    if "description" in data:
        out["description"] = c.block(data.get("description"), 4000)
    if "objectives" in data:
        out["objectives"] = c.block(data.get("objectives"), 2000)
    if not partial or "language" in data:
        out["language"] = c.language(data.get("language") or "Deutsch")
    if not partial or "level" in data:
        out["level"] = c.level(data.get("level"))
    if not partial or "duration_minutes" in data:
        v = data.get("duration_minutes")
        if not isinstance(v, int) or isinstance(v, bool) or not 15 <= v <= 90:
            raise c.err(422, "DURATION_INVALID")
        out["duration_minutes"] = v
    if not partial or "max_participants" in data:
        v = data.get("max_participants")
        if not isinstance(v, int) or isinstance(v, bool) or not 2 <= v <= _cap():
            raise c.err(422, "MAX_PARTICIPANTS_INVALID")
        out["max_participants"] = v
    if not partial or "starts_at" in data:
        out["starts_at"] = check_start(data.get("starts_at"))
    return out


def check_start(at) -> datetime:
    if not isinstance(at, datetime):
        raise c.err(422, "STARTS_AT_REQUIRED")
    if at.tzinfo is None:
        raise c.err(422, "STARTS_AT_TIMEZONE_REQUIRED")
    t = c.now()
    if at < t + MIN_LEAD:
        raise c.err(422, "STARTS_AT_TOO_SOON")
    if at > t + MAX_AHEAD:
        raise c.err(422, "STARTS_AT_TOO_FAR")
    return at


def _room_part(db: Session, room: VideoRoom | None) -> dict | None:
    if room is None:
        return None
    online = 0
    if room.status == ROOM_LIVE:
        online = int(db.scalar(select(func.count()).select_from(VideoRoomParticipant).where(
            VideoRoomParticipant.room_id == room.id, VideoRoomParticipant.connection_status.in_(ONLINE))) or 0)
    return {"id": room.id, "status": room.status, "started_at": room.started_at, "ended_at": room.ended_at, "hard_end_at": room.hard_end_at,
            "online": online, "end_reason": room.end_reason}


def _out(db: Session, lesson: SpecialLesson, viewer: User | None = None, full: bool = False) -> dict:
    from app.services.teacher_market.profiles import card

    room = _room(db, lesson.id)
    t = c.now()
    signups = int(db.scalar(select(func.count()).select_from(SpecialLessonSignup).where(SpecialLessonSignup.lesson_id == lesson.id)) or 0)
    teacher_card = card(lesson.teacher, c.profile_of(db, lesson.teacher_id))
    manager = viewer is not None and (viewer.id == lesson.teacher_id or viewer.role == UserRole.SUPER_ADMIN)
    out = {
        "id": lesson.id, "title": lesson.title, "topic": lesson.topic, "description": lesson.description, "objectives": lesson.objectives,
        "language": lesson.language, "level": lesson.level, "starts_at": lesson.starts_at, "ends_at": end_of(lesson),
        "duration_minutes": lesson.duration_minutes, "max_participants": lesson.max_participants, "status": lesson.status,
        "teacher": teacher_card, "signups": signups, "room": _room_part(db, room), "server_time": t,
        "opens_at": lesson.starts_at - OPEN_BEFORE,
        "can_open": manager and lesson.status == SL_APPROVED and lesson.starts_at - OPEN_BEFORE <= t < end_of(lesson)
        and (room is None or room.status == ROOM_LIVE),
        "can_join": lesson.status == SL_APPROVED and room is not None and room.status == ROOM_LIVE,
    }
    if viewer is not None:
        out["signed_up"] = db.scalar(select(SpecialLessonSignup.id).where(SpecialLessonSignup.lesson_id == lesson.id,
                                                                          SpecialLessonSignup.user_id == viewer.id)) is not None
    if full or manager:
        out.update({"reject_reason": lesson.reject_reason, "cancel_reason": lesson.cancel_reason, "reviewed_at": lesson.reviewed_at,
                    "cancelled_at": lesson.cancelled_at, "created_at": lesson.created_at})
    return out


def _visible(lesson: SpecialLesson, viewer: User) -> bool:
    return lesson.status in (SL_APPROVED, SL_ENDED) or viewer.id == lesson.teacher_id or viewer.role in (UserRole.SUPER_ADMIN, UserRole.ADMIN)


def _get(db: Session, lesson_id, lock: bool = False) -> SpecialLesson:
    q = select(SpecialLesson).where(SpecialLesson.id == c.parse_uuid(lesson_id))
    if lock:
        q = q.with_for_update(of=SpecialLesson)
    lesson = db.scalar(q)
    if lesson is None:
        raise c.err(404, "SPECIAL_LESSON_NOT_FOUND")
    return lesson


# ---------- teacher ----------

def teacher_create(db: Session, teacher: User, data: dict) -> dict:
    if not c.bookable(teacher, c.profile_of(db, teacher.id)) and teacher.role != UserRole.SUPER_ADMIN:
        raise c.err(409, "PROFILE_DISABLED")
    open_ = db.scalar(select(func.count()).select_from(SpecialLesson).where(SpecialLesson.teacher_id == teacher.id,
                                                                            SpecialLesson.status.in_((SL_PENDING, SL_APPROVED)))) or 0
    if open_ >= MAX_OPEN_PER_TEACHER:
        raise c.err(409, "TOO_MANY_SPECIAL_LESSONS")
    fields = _validate(data, partial=False)
    lesson = SpecialLesson(teacher_id=teacher.id, status=SL_PENDING, **fields)
    lesson.teacher = teacher
    db.add(lesson)
    db.flush()
    c.notify_admins(db, "Maxsus dars so'rovi / Spezialstunde beantragt", f"{c.display_name(teacher)}: «{lesson.title}» — {c.when(lesson.starts_at)}.",
                    "/admin/lehrer-marktplatz?tab=spezialstunden")
    db.commit()
    return _out(db, lesson, teacher)


def teacher_update(db: Session, teacher: User, lesson_id, data: dict) -> dict:
    lesson = _get(db, lesson_id, lock=True)
    if lesson.teacher_id != teacher.id:
        raise c.err(404, "SPECIAL_LESSON_NOT_FOUND")
    if lesson.status != SL_PENDING:
        raise c.err(409, "SPECIAL_LESSON_NOT_PENDING")
    for k, v in _validate(data, partial=True).items():
        setattr(lesson, k, v)
    db.commit()
    return _out(db, lesson, teacher)


def teacher_list(db: Session, teacher: User) -> list[dict]:
    rows = db.scalars(select(SpecialLesson).where(SpecialLesson.teacher_id == teacher.id).order_by(SpecialLesson.starts_at.desc()).limit(200))
    return [_out(db, r, teacher) for r in rows]


def cancel(db: Session, actor: User, lesson_id, reason: str | None, ip: str | None) -> dict:
    lesson = _get(db, lesson_id, lock=True)
    admin = actor.role == UserRole.SUPER_ADMIN
    if lesson.teacher_id != actor.id and not admin:
        raise c.err(404, "SPECIAL_LESSON_NOT_FOUND")
    if lesson.status not in (SL_PENDING, SL_APPROVED):
        raise c.err(409, "SPECIAL_LESSON_CLOSED")
    room = _room(db, lesson.id)
    if not admin and room is not None and room.status == ROOM_LIVE:
        raise c.err(409, "END_THE_LIVE_LESSON_FIRST")
    text = c.one_line(reason, "reason", 500, min_len=3, required=admin)
    was_approved = lesson.status == SL_APPROVED
    lesson.status, lesson.cancelled_by, lesson.cancelled_at, lesson.cancel_reason = SL_CANCELLED, actor.id, c.now(), text
    if room is not None and room.status == ROOM_LIVE:
        from app.services.video_rooms.service import event, finish

        finish(db, room, actor.id, "cancelled")
        event(db, room, actor.id, "ended", {"reason": "cancelled"})
    _unpin(db, lesson)
    if was_approved:
        people = set(db.scalars(select(SpecialLessonSignup.user_id).where(SpecialLessonSignup.lesson_id == lesson.id)))
        if room is not None:
            people.update(db.scalars(select(VideoRoomParticipant.user_id).where(VideoRoomParticipant.room_id == room.id)))
        people.discard(lesson.teacher_id)
        for uid in people:
            c.notify(db, uid, "Maxsus dars bekor qilindi / Spezialstunde abgesagt", f"«{lesson.title}» ({c.when(lesson.starts_at)}) bo'lmaydi."
                     + (f" {text}" if text else ""), "/my-teacher/live")
    if admin and actor.id != lesson.teacher_id:
        c.notify(db, lesson.teacher_id, "Maxsus dars bekor qilindi / Spezialstunde abgesagt", f"«{lesson.title}»: {text}", "/teacher/spezialstunden")
    db.commit()
    write_audit(db, actor_id=actor.id, action="special_lesson_cancelled", target_user_id=lesson.teacher_id,
                details=f"lesson={lesson.id} {lesson.title}" + (f", reason={text}" if text else ""), ip_address=ip)
    return _out(db, lesson, actor, full=True)


def open_room(db: Session, actor: User, lesson_id) -> dict:
    """The teacher opens the live room (15 min before the start … end). Idempotent while the room is live."""
    from app.services.video_rooms import livekit_service as lk
    from app.services.video_rooms.service import HOST_SEATS, event, room_metadata

    lesson = _get(db, lesson_id, lock=True)
    if lesson.teacher_id != actor.id and actor.role != UserRole.SUPER_ADMIN:
        raise c.err(404, "SPECIAL_LESSON_NOT_FOUND")
    if lesson.status != SL_APPROVED:
        raise c.err(409, "SPECIAL_LESSON_NOT_APPROVED")
    t = c.now()
    if t < lesson.starts_at - OPEN_BEFORE:
        raise c.err(409, "OPEN_WINDOW_NOT_REACHED")
    if t >= end_of(lesson):
        raise c.err(409, "LESSON_OVER")
    room = _room(db, lesson.id)
    if room is not None and room.status == ROOM_LIVE:
        return {"room_id": room.id, "hard_end_at": room.hard_end_at}
    if room is not None:
        raise c.err(409, "LESSON_ROOM_ENDED")
    if not lk.configured():
        raise c.err(503, "VIDEO_SERVICE_NOT_CONFIGURED")
    rid = uuid4()
    room = VideoRoom(id=rid, group_id=None, special_lesson_id=lesson.id, created_by=actor.id, room_name=f"vizu-{rid.hex}", title=lesson.title,
                     description=lesson.topic, status=ROOM_LIVE, scheduled_at=lesson.starts_at, started_at=t, hard_end_at=end_of(lesson),
                     max_participants=lesson.max_participants, chat_enabled=True, students_can_share_screen=False, students_mic_allowed=False,
                     students_camera_allowed=False)
    db.add(room)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise c.err(409, "LESSON_ROOM_EXISTS") from None
    try:
        lk.gateway.ensure_room(room.room_name, room.max_participants + HOST_SEATS, room_metadata(room))
    except lk.LiveKitUnavailable:
        db.rollback()
        raise c.err(503, "VIDEO_SERVICE_UNAVAILABLE") from None
    event(db, room, actor.id, "started", {"special_lesson": str(lesson.id)})
    for uid in db.scalars(select(SpecialLessonSignup.user_id).where(SpecialLessonSignup.lesson_id == lesson.id)):
        c.notify(db, uid, "Maxsus dars boshlandi / Spezialstunde live", f"«{lesson.title}» — hozir qo'shiling.", f"/video-room/{room.id}")
    db.commit()
    return {"room_id": room.id, "hard_end_at": room.hard_end_at}


# ---------- everyone ----------

def board(db: Session, viewer: User) -> dict:
    t = c.now()
    ahead = list(db.scalars(select(SpecialLesson).where(SpecialLesson.status == SL_APPROVED, SpecialLesson.starts_at <= t + MAX_AHEAD)
                            .order_by(SpecialLesson.starts_at.asc()).limit(50)))
    ahead = [x for x in ahead if end_of(x) > t]
    past = list(db.scalars(select(SpecialLesson).where(SpecialLesson.status == SL_ENDED).order_by(SpecialLesson.starts_at.desc()).limit(10)))
    items = [_out(db, x, viewer) for x in ahead]
    return {"live": [x for x in items if x["room"] and x["room"]["status"] == ROOM_LIVE],
            "upcoming": [x for x in items if not (x["room"] and x["room"]["status"] == ROOM_LIVE)],
            "past": [_out(db, x, viewer) for x in past], "server_time": t}


def get(db: Session, viewer: User, lesson_id) -> dict:
    lesson = _get(db, lesson_id)
    if not _visible(lesson, viewer):
        raise c.err(404, "SPECIAL_LESSON_NOT_FOUND")
    return _out(db, lesson, viewer)


def signup(db: Session, user: User, lesson_id, on: bool) -> dict:
    lesson = _get(db, lesson_id)
    if lesson.status != SL_APPROVED or end_of(lesson) <= c.now():
        raise c.err(409, "SPECIAL_LESSON_CLOSED")
    row = db.scalar(select(SpecialLessonSignup).where(SpecialLessonSignup.lesson_id == lesson.id, SpecialLessonSignup.user_id == user.id))
    if on and row is None:
        db.add(SpecialLessonSignup(lesson_id=lesson.id, user_id=user.id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
    elif not on and row is not None:
        db.delete(row)
        db.commit()
    return {"signed_up": on}


# ---------- admin ----------

def admin_list(db: Session, status: str | None) -> list[dict]:
    q = select(SpecialLesson)
    if status:
        q = q.where(SpecialLesson.status == status)
    rows = db.scalars(q.order_by(SpecialLesson.status != SL_PENDING, SpecialLesson.starts_at.desc()).limit(300))
    out = []
    for r in rows:
        item = _out(db, r, None, full=True)
        room = _room(db, r.id)
        item["participants_total"] = int(db.scalar(select(func.count()).select_from(VideoRoomParticipant).where(
            VideoRoomParticipant.room_id == room.id, VideoRoomParticipant.joined_at.is_not(None))) or 0) if room else 0
        out.append(item)
    return out


def _announce(db: Session, lesson: SpecialLesson, admin: User) -> None:
    body = (f"Kostenlose Spezialstunde / Bepul maxsus dars: {lesson.title}\n"
            f"Lehrkraft: {c.display_name(lesson.teacher)} · {lesson.level} · {lesson.language}\n"
            f"Start: {c.when(lesson.starts_at)} (Toshkent) · {lesson.duration_minutes} Min. · max. {lesson.max_participants}\n"
            f"Thema: {lesson.topic}\n"
            "Teilnehmen / Qo'shilish: Global Chat → Live-Unterricht")
    pins = db.scalar(select(func.count()).select_from(GlobalChatMessage).where(GlobalChatMessage.pinned_at.is_not(None),
                                                                               GlobalChatMessage.status == MESSAGE_VISIBLE)) or 0
    t = c.now()
    msg = GlobalChatMessage(sender_id=lesson.teacher_id, body=body[:2000], status=MESSAGE_VISIBLE,
                            pinned_at=t if pins < MAX_PINS else None, pinned_by=admin.id if pins < MAX_PINS else None)
    db.add(msg)
    db.flush()
    lesson.announcement_message_id = msg.id


def _unpin(db: Session, lesson: SpecialLesson) -> None:
    if lesson.announcement_message_id:
        msg = db.get(GlobalChatMessage, lesson.announcement_message_id)
        if msg is not None and msg.pinned_at is not None:
            msg.pinned_at, msg.pinned_by = None, None


def admin_review(db: Session, admin: User, lesson_id, decision: str, reason: str | None, starts_at, ip: str | None) -> dict:
    lesson = _get(db, lesson_id, lock=True)
    if lesson.status != SL_PENDING:
        raise c.err(409, "SPECIAL_LESSON_NOT_PENDING")
    if decision == "approve":
        if starts_at is not None:
            lesson.starts_at = check_start(starts_at)
        elif lesson.starts_at < c.now() + timedelta(minutes=5):
            raise c.err(409, "STARTS_AT_PASSED")
        lesson.status, lesson.reviewed_by, lesson.reviewed_at, lesson.reject_reason = SL_APPROVED, admin.id, c.now(), None
        _announce(db, lesson, admin)
        c.notify(db, lesson.teacher_id, "Maxsus dars tasdiqlandi / Spezialstunde genehmigt",
                 f"«{lesson.title}» — {c.when(lesson.starts_at)}. Xonani boshlanishidan 15 daqiqa oldin ochishingiz mumkin.", "/teacher/spezialstunden")
        for uid in db.scalars(select(User.id).where(User.role == UserRole.STUDENT, User.is_active.is_(True), User.is_banned.is_(False))):
            c.notify(db, uid, "Yangi bepul dars / Neue Spezialstunde", f"{c.display_name(lesson.teacher)}: «{lesson.title}» — {c.when(lesson.starts_at)}.",
                     "/my-teacher/live")
    elif decision == "reject":
        text = c.one_line(reason, "reason", 500, min_len=3, required=True)
        lesson.status, lesson.reviewed_by, lesson.reviewed_at, lesson.reject_reason = SL_REJECTED, admin.id, c.now(), text
        c.notify(db, lesson.teacher_id, "Maxsus dars rad etildi / Spezialstunde abgelehnt", f"«{lesson.title}»: {text}", "/teacher/spezialstunden")
    else:
        raise c.err(422, "DECISION_INVALID")
    db.commit()
    write_audit(db, actor_id=admin.id, action=f"special_lesson_{decision}", target_user_id=lesson.teacher_id,
                details=f"lesson={lesson.id} {lesson.title} start={lesson.starts_at.isoformat()}"
                        + (f", reason={lesson.reject_reason}" if decision == "reject" else ""), ip_address=ip)
    return _out(db, lesson, admin, full=True)


def admin_counts(db: Session) -> dict:
    rows = dict(db.execute(select(SpecialLesson.status, func.count()).group_by(SpecialLesson.status)).all())
    live = db.scalar(select(func.count()).select_from(VideoRoom).where(VideoRoom.special_lesson_id.is_not(None), VideoRoom.status == ROOM_LIVE)) or 0
    return {**{k.lower(): int(v) for k, v in rows.items()}, "live": int(live)}


# ---------- room hook + scheduler ----------

def on_room_finished(db: Session, room: VideoRoom) -> None:
    """Called by video_rooms.service.finish for a special-lesson room: the lesson is over (history stays, the pin goes)."""
    lesson = db.get(SpecialLesson, room.special_lesson_id) if room.special_lesson_id else None
    if lesson is not None and lesson.status == SL_APPROVED:
        lesson.status = SL_ENDED
        _unpin(db, lesson)


def tick(db: Session) -> dict:
    """One scheduler round (also safe to call from tests): close rooms past hard_end_at, end lessons past their end,
    tell the teacher when the room can be opened, remind sign-ups 30 min before."""
    from app.services.video_rooms.service import event, finish

    t = c.now()
    closed = ended = notified = reminded = 0
    for room in db.scalars(select(VideoRoom).where(VideoRoom.status == ROOM_LIVE, VideoRoom.hard_end_at.is_not(None), VideoRoom.hard_end_at <= t)):
        finish(db, room, None, "time_limit")
        event(db, room, None, "ended", {"reason": "time_limit"})
        closed += 1
    for lesson in db.scalars(select(SpecialLesson).where(SpecialLesson.status == SL_APPROVED, SpecialLesson.starts_at <= t + REMIND_BEFORE)):
        room = _room(db, lesson.id)
        if end_of(lesson) <= t and (room is None or room.status != ROOM_LIVE):
            lesson.status = SL_ENDED
            _unpin(db, lesson)
            ended += 1
            continue
        if lesson.teacher_notified_at is None and lesson.starts_at - OPEN_BEFORE <= t:
            lesson.teacher_notified_at = t
            c.notify(db, lesson.teacher_id, "Xonani ochish vaqti / Raum kann geöffnet werden",
                     f"«{lesson.title}» — {c.when(lesson.starts_at)}. Videodarsni hozir ochishingiz mumkin.", "/teacher/spezialstunden")
            notified += 1
        if lesson.reminder_sent_at is None and lesson.starts_at - REMIND_BEFORE <= t < lesson.starts_at:
            lesson.reminder_sent_at = t
            for uid in db.scalars(select(SpecialLessonSignup.user_id).where(SpecialLessonSignup.lesson_id == lesson.id)):
                c.notify(db, uid, "Dars tez orada / Spezialstunde beginnt bald", f"«{lesson.title}» — {c.when(lesson.starts_at)}.", "/my-teacher/live")
            reminded += 1
    db.commit()
    return {"closed_rooms": closed, "ended_lessons": ended, "teacher_notified": notified, "reminders": reminded}
