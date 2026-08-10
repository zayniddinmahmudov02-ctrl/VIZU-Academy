import secrets
import string
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.config import settings
from app.core.exceptions import DomainError, NotFoundError
from app.core.pagination import clamp_page_params, paginated_response
from app.core.security import create_user_token, hash_password
from app.core.security.roles import UserRole
from app.models.audit_log import AuditLog
from app.models.certificate import Certificate
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.login_history import LoginHistory
from app.models.module import Module
from app.models.payment.payment import Payment
from app.models.student_progress import StudentProgress
from app.models.user import User
from app.models.user_tag import UserTag

APPROVED = "approved"

SORT_COLUMNS = {
    "created_at": User.created_at,
    "last_login": User.last_login,
    "username": User.username,
    "email": User.email,
    "role": User.role,
    "premium_until": User.premium_until,
}

# Sorting "alphabetically" (Nachname/Vorname) needs two columns in order,
# not one — handled as a special case in list_users() rather than through
# SORT_COLUMNS, which only supports a single column.
NAME_SORT_COLUMNS = (User.last_name, User.first_name, User.username)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AdminUsersService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _tags_by_user(self, user_ids: list[UUID]) -> dict[UUID, list[dict]]:
        if not user_ids:
            return {}

        rows = (
            self.db.query(UserTag)
            .filter(UserTag.user_id.in_(user_ids))
            .order_by(UserTag.label)
            .all()
        )

        grouped: dict[UUID, list[dict]] = {}
        for row in rows:
            grouped.setdefault(row.user_id, []).append(
                {"id": str(row.id), "label": row.label}
            )

        return grouped

    def _serialize_list_item(
        self,
        user: User,
        tags: list[dict],
        usage_minutes: int = 0,
    ) -> dict:
        now = _now()
        is_premium = bool(user.premium_until and user.premium_until > now)
        is_suspended = bool(user.suspended_until and user.suspended_until > now)

        # No real-time presence/heartbeat system exists in this codebase —
        # "online" is approximated from the last successful login staying
        # within one access-token lifetime, i.e. "their most recent session
        # token hasn't necessarily expired yet". A real presence system
        # (websocket heartbeat, last-seen-at pings) would be a separate,
        # larger addition; this is the honest signal derivable from data
        # that already exists (LoginHistory / User.last_login).
        is_online = bool(
            user.last_login
            and user.last_login > now - timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "profile_image": user.profile_image,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "is_banned": user.is_banned,
            "is_suspended": is_suspended,
            "is_premium": is_premium,
            "premium_until": user.premium_until,
            "last_login": user.last_login,
            "is_online": is_online,
            "usage_minutes": usage_minutes,
            "has_password": bool(user.password_hash),
            "created_at": user.created_at,
            "tags": tags,
        }

    def _get_user(self, user_id: str) -> User | None:
        return self.db.get(User, UUID(user_id))

    # ------------------------------------------------------------------
    # List / search / filter / sort / pagination
    # ------------------------------------------------------------------

    def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        role: str | None = None,
        status: str | None = None,
        tag: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        staff_only: bool = False,
    ) -> dict:
        query = self.db.query(User)

        if search:
            like = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.email.ilike(like),
                    User.username.ilike(like),
                    User.first_name.ilike(like),
                    User.last_name.ilike(like),
                )
            )

        if role:
            query = query.filter(User.role == role)
        elif staff_only:
            # Powers the "Admins" panel — every staff role (i.e. anyone
            # with admin-panel access), not one specific role.
            query = query.filter(User.role.in_(UserRole.ADMIN_PANEL_ROLES))

        if tag:
            query = query.join(UserTag, UserTag.user_id == User.id).filter(
                UserTag.label == tag
            )

        now = _now()

        if status == "banned":
            query = query.filter(User.is_banned.is_(True))
        elif status == "suspended":
            query = query.filter(
                User.suspended_until.isnot(None), User.suspended_until > now
            )
        elif status == "premium":
            query = query.filter(
                User.premium_until.isnot(None), User.premium_until > now
            )
        elif status == "trial":
            query = query.filter(
                or_(User.premium_until.is_(None), User.premium_until <= now)
            )
        elif status == "active":
            query = query.filter(
                User.is_active.is_(True), User.is_banned.is_(False)
            )
        elif status == "inactive":
            query = query.filter(User.is_active.is_(False))

        total = query.distinct().count()

        if sort_by == "name":
            # "Nachname / Vorname" alphabetical ordering — NULLS LAST so
            # users who haven't filled in a name yet don't dominate the
            # front of an ascending sort. Postgres's default collation
            # already handles Latin (incl. German umlaut) ordering
            # correctly; no custom collation needed.
            direction = (lambda c: c.desc()) if sort_dir == "desc" else (lambda c: c.asc())
            order = [direction(col).nullslast() for col in NAME_SORT_COLUMNS]
        else:
            column = SORT_COLUMNS.get(sort_by, User.created_at)
            order = [column.desc() if sort_dir == "desc" else column.asc()]

        page, page_size = clamp_page_params(page, page_size)

        users = (
            query.distinct()
            .order_by(*order)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        user_ids = [u.id for u in users]
        tags_map = self._tags_by_user(user_ids)
        usage_map = self._usage_minutes_by_user(user_ids)

        items = [
            self._serialize_list_item(u, tags_map.get(u.id, []), usage_map.get(u.id, 0))
            for u in users
        ]

        return paginated_response(items, total, page, page_size)

    def _usage_minutes_by_user(self, user_ids: list[UUID]) -> dict[UUID, int]:
        """One aggregate query for the current page's users — never loads
        every StudentProgress row into Python just to sum them."""

        if not user_ids:
            return {}

        rows = (
            self.db.query(
                StudentProgress.user_id,
                func.coalesce(func.sum(StudentProgress.study_minutes), 0),
            )
            .filter(StudentProgress.user_id.in_(user_ids))
            .group_by(StudentProgress.user_id)
            .all()
        )

        return {user_id: int(total) for user_id, total in rows}

    def list_all_for_export(
        self,
        search: str | None = None,
        role: str | None = None,
        status: str | None = None,
        tag: str | None = None,
    ) -> list[dict]:
        result = self.list_users(
            page=1,
            page_size=100000,
            search=search,
            role=role,
            status=status,
            tag=tag,
        )
        return result["items"]

    # ------------------------------------------------------------------
    # Detail
    # ------------------------------------------------------------------

    def get_detail(self, user_id: str) -> dict | None:
        user = self._get_user(user_id)
        if user is None:
            return None

        now = _now()
        is_premium = bool(user.premium_until and user.premium_until > now)
        is_suspended = bool(user.suspended_until and user.suspended_until > now)

        tags = self._tags_by_user([user.id]).get(user.id, [])

        enrollments_count = (
            self.db.query(Enrollment).filter(Enrollment.user_id == user.id).count()
        )
        certificates_count = (
            self.db.query(Certificate).filter(Certificate.user_id == user.id).count()
        )
        payments_total = (
            self.db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.user_id == user.id, Payment.status == APPROVED)
            .scalar()
            or 0
        )

        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "is_banned": user.is_banned,
            "ban_reason": user.ban_reason,
            "banned_at": user.banned_at,
            "is_suspended": is_suspended,
            "suspended_until": user.suspended_until,
            "suspend_reason": user.suspend_reason,
            "is_premium": is_premium,
            "premium_until": user.premium_until,
            "last_login": user.last_login,
            "created_at": user.created_at,
            "tags": tags,
            "enrollments_count": enrollments_count,
            "certificates_count": certificates_count,
            "payments_total": int(payments_total),
        }

    # ------------------------------------------------------------------
    # Progress
    # ------------------------------------------------------------------

    def get_progress(self, user_id: str) -> dict:
        rows = (
            self.db.query(StudentProgress, Lesson, Course)
            .join(Lesson, StudentProgress.lesson_id == Lesson.id)
            .join(Module, Lesson.module_id == Module.id)
            .join(Course, Module.course_id == Course.id)
            .filter(StudentProgress.user_id == UUID(user_id))
            .order_by(Course.title, Module.order_index, Lesson.number)
            .all()
        )

        lessons = [
            {
                "lesson_id": str(progress.lesson_id),
                "lesson_title": lesson.title,
                "course_title": course.title,
                "total_score": progress.total_score,
                "lesson_completed": progress.lesson_completed,
                "video_completed": progress.video_completed,
                "grammar_completed": progress.grammar_completed,
                "reading_completed": progress.reading_completed,
                "listening_completed": progress.listening_completed,
                "writing_completed": progress.writing_completed,
                "speaking_completed": progress.speaking_completed,
                "quiz_completed": progress.quiz_completed,
            }
            for progress, lesson, course in rows
        ]

        total_started = len(rows)
        total_completed = sum(1 for progress, _, _ in rows if progress.lesson_completed)
        total_experience = sum(progress.experience for progress, _, _ in rows)
        total_study_minutes = sum(progress.study_minutes for progress, _, _ in rows)
        longest_streak = max((progress.streak_days for progress, _, _ in rows), default=0)

        return {
            "total_lessons_started": total_started,
            "total_lessons_completed": total_completed,
            "total_experience": total_experience,
            "total_study_minutes": total_study_minutes,
            "longest_streak_days": longest_streak,
            "lessons": lessons,
        }

    # ------------------------------------------------------------------
    # Login / device history
    # ------------------------------------------------------------------

    def get_login_history(self, user_id: str, page: int = 1, page_size: int = 20) -> dict:
        query = (
            self.db.query(LoginHistory)
            .filter(LoginHistory.user_id == UUID(user_id))
            .order_by(LoginHistory.created_at.desc())
        )

        total = query.count()
        page, page_size = clamp_page_params(page, page_size)

        rows = query.offset((page - 1) * page_size).limit(page_size).all()

        items = [
            {
                "id": str(row.id),
                "ip_address": row.ip_address,
                "device": row.device,
                "os": row.os,
                "browser": row.browser,
                "success": row.success,
                "created_at": row.created_at,
            }
            for row in rows
        ]

        return paginated_response(items, total, page, page_size)

    def get_device_history(self, user_id: str) -> list[dict]:
        rows = (
            self.db.query(LoginHistory)
            .filter(LoginHistory.user_id == UUID(user_id), LoginHistory.success.is_(True))
            .order_by(LoginHistory.created_at.asc())
            .all()
        )

        devices: dict[tuple[str, str, str], dict] = {}

        for row in rows:
            key = (row.device, row.os, row.browser)
            if key not in devices:
                devices[key] = {
                    "device": row.device,
                    "os": row.os,
                    "browser": row.browser,
                    "ip_address": row.ip_address,
                    "first_seen": row.created_at,
                    "last_seen": row.created_at,
                    "login_count": 0,
                }

            entry = devices[key]
            entry["last_seen"] = row.created_at
            entry["ip_address"] = row.ip_address
            entry["login_count"] += 1

        return sorted(devices.values(), key=lambda d: d["last_seen"], reverse=True)

    # ------------------------------------------------------------------
    # Activity timeline / payments / subscription
    # ------------------------------------------------------------------

    def get_activity_timeline(self, user_id: str, limit: int = 30) -> list[dict]:
        uid = UUID(user_id)
        activities: list[dict] = []

        user = self._get_user(user_id)
        if user is not None:
            activities.append(
                {"type": "registration", "title": "Account registered", "timestamp": user.created_at}
            )

        for row in self.db.query(LoginHistory).filter(LoginHistory.user_id == uid, LoginHistory.success.is_(True)).order_by(LoginHistory.created_at.desc()).limit(limit).all():
            activities.append(
                {
                    "type": "login",
                    "title": f"Signed in from {row.device} ({row.browser} / {row.os})",
                    "timestamp": row.created_at,
                }
            )

        for row in self.db.query(Payment).filter(Payment.user_id == uid).order_by(Payment.created_at.desc()).limit(limit).all():
            activities.append(
                {
                    "type": "payment",
                    "title": f"Paid {row.amount} {row.currency} ({row.status})",
                    "timestamp": row.created_at,
                }
            )

        for row in self.db.query(Certificate).filter(Certificate.user_id == uid).order_by(Certificate.issued_at.desc()).limit(limit).all():
            activities.append(
                {"type": "certificate", "title": f"Earned a {row.level} certificate", "timestamp": row.issued_at}
            )

        for row in self.db.query(Enrollment).filter(Enrollment.user_id == uid).order_by(Enrollment.created_at.desc()).limit(limit).all():
            course_title = row.course.title if row.course else "a course"
            activities.append(
                {"type": "enrollment", "title": f"Enrolled in {course_title}", "timestamp": row.created_at}
            )

        activities.sort(key=lambda item: item["timestamp"], reverse=True)

        return activities[:limit]

    def get_payment_history(self, user_id: str) -> list[dict]:
        rows = (
            self.db.query(Payment)
            .filter(Payment.user_id == UUID(user_id))
            .order_by(Payment.created_at.desc())
            .all()
        )

        return [
            {
                "id": str(row.id),
                "course_title": row.course.title if row.course else "",
                "amount": row.amount,
                "currency": row.currency,
                "provider": row.provider,
                "status": row.status,
                "transaction_id": row.transaction_id,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    def get_subscription(self, user_id: str) -> dict:
        user = self._get_user(user_id)
        if user is None:
            raise NotFoundError("User not found")

        now = _now()
        is_premium = bool(user.premium_until and user.premium_until > now)

        totals = (
            self.db.query(
                func.coalesce(func.sum(Payment.amount), 0),
                func.count(Payment.id),
            )
            .filter(Payment.user_id == user.id, Payment.status == APPROVED)
            .first()
        )
        total_paid, payments_count = totals if totals else (0, 0)

        return {
            "is_premium": is_premium,
            "premium_until": user.premium_until,
            "is_trial": not is_premium,
            "total_paid": int(total_paid or 0),
            "payments_count": int(payments_count or 0),
        }

    # ------------------------------------------------------------------
    # Actions (all audited)
    # ------------------------------------------------------------------

    def grant_premium(self, user_id: str, days: int, actor: User, ip: str | None) -> dict:
        user = self._get_user(user_id)
        if user is None:
            raise NotFoundError("User not found")

        now = _now()
        base = user.premium_until if user.premium_until and user.premium_until > now else now
        user.premium_until = base + timedelta(days=days)

        self.db.commit()
        self.db.refresh(user)

        self._audit(actor, "grant_premium", user, f"+{days} days -> {user.premium_until.isoformat()}", ip)

        return self.get_detail(user_id)

    def extend_subscription(self, user_id: str, days: int, actor: User, ip: str | None) -> dict:
        return self.grant_premium(user_id, days, actor, ip)

    def ban(self, user_id: str, reason: str, actor: User, ip: str | None) -> dict:
        user = self._get_user(user_id)
        if user is None:
            raise NotFoundError("User not found")

        user.is_banned = True
        user.ban_reason = reason
        user.banned_at = _now()

        self.db.commit()

        self._audit(actor, "ban_user", user, reason, ip)

        return self.get_detail(user_id)

    def unban(self, user_id: str, actor: User, ip: str | None) -> dict:
        user = self._get_user(user_id)
        if user is None:
            raise NotFoundError("User not found")

        user.is_banned = False
        user.ban_reason = None
        user.banned_at = None

        self.db.commit()

        self._audit(actor, "unban_user", user, None, ip)

        return self.get_detail(user_id)

    def suspend(self, user_id: str, days: int, reason: str, actor: User, ip: str | None) -> dict:
        user = self._get_user(user_id)
        if user is None:
            raise NotFoundError("User not found")

        user.suspended_until = _now() + timedelta(days=days)
        user.suspend_reason = reason

        self.db.commit()

        self._audit(actor, "suspend_user", user, f"{days} days: {reason}", ip)

        return self.get_detail(user_id)

    def unsuspend(self, user_id: str, actor: User, ip: str | None) -> dict:
        user = self._get_user(user_id)
        if user is None:
            raise NotFoundError("User not found")

        user.suspended_until = None
        user.suspend_reason = None

        self.db.commit()

        self._audit(actor, "unsuspend_user", user, None, ip)

        return self.get_detail(user_id)

    def update_role(self, user_id: str, role: str, actor: User, ip: str | None) -> dict:
        user = self._get_user(user_id)
        if user is None:
            raise NotFoundError("User not found")

        previous_role = user.role
        user.role = role

        self.db.commit()

        self._audit(actor, "update_role", user, f"{previous_role} -> {role}", ip)

        return self.get_detail(user_id)

    def reset_password(self, user_id: str, actor: User, ip: str | None) -> str:
        user = self._get_user(user_id)
        if user is None:
            raise NotFoundError("User not found")

        alphabet = string.ascii_letters + string.digits
        temp_password = "".join(secrets.choice(alphabet) for _ in range(14))

        user.password_hash = hash_password(temp_password)

        self.db.commit()

        self._audit(actor, "reset_password", user, None, ip)

        return temp_password

    def add_tag(self, user_id: str, label: str, actor: User) -> list[dict]:
        label = label.strip()
        if not label:
            raise DomainError("Tag label cannot be empty")

        uid = UUID(user_id)

        existing = (
            self.db.query(UserTag)
            .filter(UserTag.user_id == uid, UserTag.label == label)
            .first()
        )

        if existing is None:
            tag = UserTag(user_id=uid, label=label, created_by_id=actor.id)
            self.db.add(tag)
            self.db.commit()

        return self._tags_by_user([uid]).get(uid, [])

    def remove_tag(self, user_id: str, tag_id: str, actor: User) -> list[dict]:
        uid = UUID(user_id)

        tag = (
            self.db.query(UserTag)
            .filter(UserTag.id == UUID(tag_id), UserTag.user_id == uid)
            .first()
        )

        if tag is not None:
            self.db.delete(tag)
            self.db.commit()

        return self._tags_by_user([uid]).get(uid, [])

    def impersonate(self, user_id: str, actor: User, ip: str | None) -> tuple[str, dict]:
        user = self._get_user(user_id)
        if user is None:
            raise NotFoundError("User not found")

        token = create_user_token(
            user,
            expires_minutes=30,
            extra_claims={"impersonated_by": str(actor.id)},
        )

        self._audit(actor, "impersonate_user", user, None, ip)

        tags = self._tags_by_user([user.id]).get(user.id, [])

        return token, self._serialize_list_item(user, tags)

    def _audit(self, actor: User, action: str, target: User | None, details: str | None, ip: str | None) -> None:
        write_audit(
            self.db,
            actor_id=actor.id,
            action=action,
            target_user_id=target.id if target else None,
            details=details,
            ip_address=ip,
        )

    # ------------------------------------------------------------------
    # Audit log
    # ------------------------------------------------------------------

    def get_audit_log(self, user_id: str | None = None, page: int = 1, page_size: int = 20) -> dict:
        query = self.db.query(AuditLog).order_by(AuditLog.created_at.desc())

        if user_id:
            query = query.filter(AuditLog.target_user_id == UUID(user_id))

        total = query.count()
        page, page_size = clamp_page_params(page, page_size)

        rows = query.offset((page - 1) * page_size).limit(page_size).all()

        items = [
            {
                "id": str(row.id),
                "actor_email": row.actor.email if row.actor else None,
                "action": row.action,
                "details": row.details,
                "ip_address": row.ip_address,
                "created_at": row.created_at,
            }
            for row in rows
        ]

        return paginated_response(items, total, page, page_size)
