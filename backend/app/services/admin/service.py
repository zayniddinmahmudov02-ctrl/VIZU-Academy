from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.language import Language
from app.models.course import Course
from app.models.module import Module
from app.models.lesson import Lesson
from app.models.enrollment import Enrollment
from app.models.certificate import Certificate
from app.models.payment import Payment


APPROVED = "approved"


class AdminService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def dashboard(self):
        """Legacy summary shape — kept for backward compatibility."""

        return {

            "users": self.db.query(User).count(),

            "teachers": (
                self.db.query(User)
                .filter(User.role == "TEACHER")
                .count()
            ),

            "students": (
                self.db.query(User)
                .filter(User.role == "STUDENT")
                .count()
            ),

            "languages": self.db.query(Language).count(),

            "courses": self.db.query(Course).count(),

            "modules": self.db.query(Module).count(),

            "lessons": self.db.query(Lesson).count(),

            "enrollments": self.db.query(Enrollment).count(),

            "certificates": self.db.query(Certificate).count(),

            "payments": self.db.query(Payment).count(),
        }

    def dashboard_overview(self):

        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = today_start.replace(day=1)
        year_start = today_start.replace(month=1, day=1)

        total_users = self.db.query(User).count()

        premium_user_ids = (
            self.db.query(Payment.user_id)
            .filter(Payment.status == APPROVED)
            .distinct()
        )
        premium_users = premium_user_ids.count()
        trial_users = max(total_users - premium_users, 0)

        revenue_today = self._revenue_since(today_start)
        revenue_month = self._revenue_since(month_start)
        revenue_year = self._revenue_since(year_start)

        stats = {
            "total_users": total_users,
            "premium_users": premium_users,
            "trial_users": trial_users,
            "revenue_today": revenue_today,
            "revenue_month": revenue_month,
            "revenue_year": revenue_year,
            "certificates": self.db.query(Certificate).count(),
            "courses": self.db.query(Course).count(),
            "lessons": self.db.query(Lesson).count(),
        }

        return {
            "server_status": "operational",
            "stats": stats,
            "revenue_chart": self._monthly_revenue_series(),
            "user_growth_chart": self._monthly_registration_series(),
            "popular_courses": self._popular_courses(),
            "active_users": self._active_users(),
            "recent_registrations": self._recent_registrations(),
            "recent_payments": self._recent_payments(),
            "recent_certificates": self._recent_certificates(),
            "recent_activities": self._recent_activities(),
        }

    def _revenue_since(self, since: datetime) -> int:
        total = (
            self.db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.status == APPROVED)
            .filter(Payment.created_at >= since)
            .scalar()
        )
        return int(total or 0)

    def _monthly_revenue_series(self, months: int = 12):
        bucket = func.to_char(Payment.created_at, "YYYY-MM")

        rows = (
            self.db.query(bucket.label("label"), func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.status == APPROVED)
            .group_by(bucket)
            .order_by(bucket)
            .all()
        )

        return [{"label": label, "value": int(value)} for label, value in rows][-months:]

    def _monthly_registration_series(self, months: int = 12):
        bucket = func.to_char(User.created_at, "YYYY-MM")

        rows = (
            self.db.query(bucket.label("label"), func.count(User.id))
            .group_by(bucket)
            .order_by(bucket)
            .all()
        )

        return [{"label": label, "value": int(value)} for label, value in rows][-months:]

    def _popular_courses(self, limit: int = 5):
        rows = (
            self.db.query(Course, func.count(Enrollment.id).label("enrollment_count"))
            .outerjoin(Enrollment, Enrollment.course_id == Course.id)
            .group_by(Course.id)
            .order_by(func.count(Enrollment.id).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": str(course.id),
                "title": course.title,
                "level": course.level,
                "enrollments": int(count),
            }
            for course, count in rows
        ]

    def _active_users(self, limit: int = 8):
        users = (
            self.db.query(User)
            .filter(User.last_login.isnot(None))
            .order_by(User.last_login.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "last_login": u.last_login,
            }
            for u in users
        ]

    def _recent_registrations(self, limit: int = 8):
        users = (
            self.db.query(User)
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "created_at": u.created_at,
            }
            for u in users
        ]

    def _recent_payments(self, limit: int = 8):
        payments = (
            self.db.query(Payment)
            .order_by(Payment.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": str(p.id),
                "user_email": p.user.email if p.user else "",
                "course_title": p.course.title if p.course else "",
                "amount": p.amount,
                "currency": p.currency,
                "status": p.status,
                "created_at": p.created_at,
            }
            for p in payments
        ]

    def _recent_certificates(self, limit: int = 8):
        certificates = (
            self.db.query(Certificate)
            .order_by(Certificate.issued_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": str(c.id),
                "user_email": c.user.email if c.user else "",
                "course_title": c.course.title if c.course else "",
                "level": c.level,
                "issued_at": c.issued_at,
            }
            for c in certificates
        ]

    def _recent_activities(self, limit: int = 10):
        activities = []

        for u in self.db.query(User).order_by(User.created_at.desc()).limit(limit).all():
            activities.append(
                {
                    "type": "registration",
                    "title": f"{u.username} registered",
                    "timestamp": u.created_at,
                }
            )

        for p in self.db.query(Payment).order_by(Payment.created_at.desc()).limit(limit).all():
            email = p.user.email if p.user else "Unknown"
            activities.append(
                {
                    "type": "payment",
                    "title": f"{email} paid {p.amount} {p.currency} ({p.status})",
                    "timestamp": p.created_at,
                }
            )

        for c in self.db.query(Certificate).order_by(Certificate.issued_at.desc()).limit(limit).all():
            email = c.user.email if c.user else "Unknown"
            activities.append(
                {
                    "type": "certificate",
                    "title": f"{email} earned a {c.level} certificate",
                    "timestamp": c.issued_at,
                }
            )

        activities.sort(key=lambda item: item["timestamp"], reverse=True)

        return activities[:limit]
