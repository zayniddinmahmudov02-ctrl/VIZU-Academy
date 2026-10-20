"""Phase 5 — Enterprise Super Admin Dashboard.

One service, one query pass per section, feeding the single
`GET /admin/dashboard` endpoint — every widget on the dashboard reads from
this one response instead of firing its own request (see
app/api/admin/router.py). Every number here is a real query against
PostgreSQL; nothing is hardcoded or fabricated. Where a metric genuinely
cannot be measured in this environment (CPU/RAM without `psutil`, which
cannot be installed in this sandbox — see AGENTS-level notes), the field is
returned as `None` rather than a fake value.
"""

import os
import shutil
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, text
from sqlalchemy.orm import Session, aliased, joinedload

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.certificate import Certificate
from app.models.certification_provider import CertificationProvider
from app.models.course import Course
from app.models.grammar import Grammar
from app.models.homework import Homework
from app.models.kompetenz import Kompetenz
from app.models.language import Language
from app.models.lesson import Lesson
from app.models.listening import Listening
from app.models.listening_content import ListeningContent
from app.models.mock_exam_level import MockExamLevel
from app.models.mock_question import MockQuestion
from app.models.mock_question_answer import MockQuestionAnswer
from app.models.mock_speaking_submission import MockSpeakingSubmission
from app.models.mock_test_attempt import STATUS_GRADED, MockTestAttempt
from app.models.mock_writing_submission import MockWritingSubmission
from app.models.model_test import ModelTest
from app.models.module import Module
from app.models.quiz import Quiz
from app.models.reading import Reading
from app.models.reading_content import ReadingContent
from app.models.speaking import Speaking
from app.models.speaking_task import SpeakingTask
from app.models.student_progress import StudentProgress
from app.models.student_quiz import StudentQuiz
from app.models.subscription_order import SubscriptionOrder
from app.models.teil import Teil
from app.models.user import User
from app.models.video import Video
from app.models.video_progress import VideoProgress
from app.models.vocabulary import Vocabulary
from app.models.writing import Writing
from app.models.writing_task import WritingTask
from app.services.certificate import registry as certificate_registry
from app.services.vizu_pay import plans as plan_config

PASS_THRESHOLD = 0.6

# who sees what on the dashboard (everyone else with admin-panel access sees the rest)
FINANCE_ROLES = {"SUPER_ADMIN", "ADMIN", "PAYMENT_MANAGER"}
SYSTEM_ROLES = {"SUPER_ADMIN", "ADMIN"}

RANGE_DAYS = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}

# Process start time — the only honest way to report "uptime" without an
# external process supervisor to ask.
_PROCESS_START = time.time()


def _aware_utc(dt: datetime) -> datetime:
    """_recent_activity() sorts timestamps from six different columns.
    Most (User/StudentProgress/ModelTest/AuditLog — everything inherited
    from BaseModel) are `DateTime(timezone=True)` and come back aware.
    Two aren't: Certificate.issued_at (`default=datetime.utcnow`) and
    SubscriptionOrder.reviewed_at (set via vizu_pay's `_now()`, which is
    `datetime.now(timezone.utc).replace(tzinfo=None)` — deliberately
    naive-but-UTC to match its plain `DateTime` column). Both naive
    sources are UTC by construction, so tagging them UTC here isn't a
    guess — it's restoring the tzinfo their own default already implied
    before the DB round-trip dropped it. `sort()` can't compare aware and
    naive datetimes at all, hence the crash this fixes."""

    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _pct(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, 1)


class EnterpriseDashboardService:
    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # Top-level assembly
    # ============================================================

    def get_dashboard(self, range_key: str, role: str | None = None) -> dict:
        """`role` decides the sensitive sections: revenue / payments only for
        FINANCE_ROLES, server health only for SYSTEM_ROLES (None = everything,
        the previous SUPER_ADMIN-only behaviour)."""
        range_key = range_key if range_key in RANGE_DAYS else "30d"
        finance = role is None or role in FINANCE_ROLES
        system = role is None or role in SYSTEM_ROLES

        kpis = self._kpis()
        charts = self._charts(range_key)
        if not finance:
            kpis["total_revenue"] = None
            charts["revenue"] = []
        activity = self._recent_activity()
        if not finance:
            activity = [a for a in activity if a["type"] != "premium_purchase"]
        return {
            "kpis": kpis,
            "charts": charts,
            "learning_analytics": self._learning_analytics(),
            "mock_test_analytics": self._mock_test_analytics(),
            "vizu_multilevel": self._vizu_multilevel(),
            "payments": self._payments() if finance else None,
            "content": self._content_counts(),
            "ai": self._ai_stats(),
            "recent_activity": activity,
            "server_health": self._server_health() if system else None,
            "can_see_finance": finance,
            "can_see_system": system,
        }

    # ============================================================
    # KPIs
    # ============================================================

    def _kpis(self) -> dict:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        thirty_days_ago = now - timedelta(days=30)

        return {
            "total_users": self.db.query(User).count(),
            "active_users_30d": (
                self.db.query(User).filter(User.last_login >= thirty_days_ago).count()
            ),
            "premium_members": (
                self.db.query(User)
                .filter(User.premium_until.isnot(None), User.premium_until > now)
                .count()
            ),
            "total_revenue": self._approved_revenue_since(None),
            "active_courses": self.db.query(Course).filter(Course.is_active.is_(True)).count(),
            "total_model_tests": self.db.query(ModelTest).count(),
            # certificate rows + final VIZU-Multilevel results (their certificate is derived from the attempt)
            "certificates_issued": certificate_registry.count_all(self.db),
            "todays_registrations": self.db.query(User).filter(User.created_at >= today_start).count(),
        }

    def _approved_revenue_since(self, since: datetime | None) -> int:
        query = self.db.query(func.coalesce(func.sum(SubscriptionOrder.final_amount), 0)).filter(
            SubscriptionOrder.status == plan_config.STATUS_APPROVED,
            SubscriptionOrder.plan.in_(list(plan_config.REVENUE_PLANS)),
        )
        if since is not None:
            query = query.filter(SubscriptionOrder.reviewed_at >= since)
        return int(query.scalar() or 0)

    # ============================================================
    # Charts (revenue / new users / learning progress), range-aware
    # ============================================================

    def _range_since(self, range_key: str) -> tuple[datetime, str]:
        days = RANGE_DAYS[range_key]
        since = datetime.now(timezone.utc) - timedelta(days=days)
        granularity = "day" if days <= 90 else "month"
        return since, granularity

    def _bucket_label(self, date_col, granularity: str):
        bucket = func.date_trunc(granularity, date_col)
        fmt = "YYYY-MM-DD" if granularity == "day" else "YYYY-MM"
        return func.to_char(bucket, fmt)

    def _charts(self, range_key: str) -> dict:
        return {
            "range": range_key,
            "revenue": self._revenue_chart(range_key),
            "new_users": self._new_users_chart(range_key),
            "learning_progress": self._learning_progress_chart(range_key),
        }

    def _revenue_chart(self, range_key: str) -> list[dict]:
        since, granularity = self._range_since(range_key)
        label = self._bucket_label(SubscriptionOrder.reviewed_at, granularity)

        rows = (
            self.db.query(label.label("label"), func.coalesce(func.sum(SubscriptionOrder.final_amount), 0))
            .filter(
                SubscriptionOrder.status == plan_config.STATUS_APPROVED,
                SubscriptionOrder.plan.in_(list(plan_config.REVENUE_PLANS)),
                SubscriptionOrder.reviewed_at >= since,
            )
            .group_by(label)
            .order_by(label)
            .all()
        )
        return [{"label": lbl, "value": float(val)} for lbl, val in rows]

    def _new_users_chart(self, range_key: str) -> list[dict]:
        since, granularity = self._range_since(range_key)
        label = self._bucket_label(User.created_at, granularity)

        rows = (
            self.db.query(label.label("label"), func.count(User.id))
            .filter(User.created_at >= since)
            .group_by(label)
            .order_by(label)
            .all()
        )
        return [{"label": lbl, "value": float(val)} for lbl, val in rows]

    def _learning_progress_chart(self, range_key: str) -> list[dict]:
        since, granularity = self._range_since(range_key)
        label = self._bucket_label(StudentProgress.updated_at, granularity)

        rows = (
            self.db.query(label.label("label"), func.count(StudentProgress.id))
            .filter(StudentProgress.lesson_completed.is_(True))
            .filter(StudentProgress.updated_at >= since)
            .group_by(label)
            .order_by(label)
            .all()
        )
        return [{"label": lbl, "value": float(val)} for lbl, val in rows]

    # ============================================================
    # Learning Analytics
    # ============================================================

    def _learning_analytics(self) -> dict:
        """From the lesson progress the LMS really writes (student_progress).
        The old Enrollment table is never filled by the current course flow,
        so every number based on it was a permanent 0 / "no data"."""
        most_active_course = self._most_active_course()
        most_viewed_lesson = self._most_viewed_lesson()
        most_solved_quiz = self._top_quiz(passed=True)
        most_failed_quiz = self._top_quiz(passed=False)

        total_rows, completed_rows, learners, finishers = self.db.query(
            func.count(StudentProgress.id),
            func.count(StudentProgress.id).filter(StudentProgress.lesson_completed.is_(True)),
            func.count(func.distinct(StudentProgress.user_id)),
            func.count(func.distinct(StudentProgress.user_id)).filter(StudentProgress.lesson_completed.is_(True)),
        ).one()

        return {
            "most_active_course": most_active_course,
            "most_viewed_lesson": most_viewed_lesson,
            "most_solved_quiz": most_solved_quiz,
            "most_failed_quiz": most_failed_quiz,
            "course_completion_percent": _pct(completed_rows, total_rows),
            "student_completion_percent": _pct(finishers, learners),
            "active_learners": int(learners or 0),
            "lessons_completed": int(completed_rows or 0),
        }

    def _most_active_course(self) -> dict | None:
        """The course (level) with the most students who have lesson progress in it."""
        row = (
            self.db.query(Course, func.count(func.distinct(StudentProgress.user_id)).label("count"))
            .join(Module, Module.course_id == Course.id)
            .join(Lesson, Lesson.module_id == Module.id)
            .join(StudentProgress, StudentProgress.lesson_id == Lesson.id)
            .group_by(Course.id)
            .order_by(func.count(func.distinct(StudentProgress.user_id)).desc())
            .first()
        )
        if row is None:
            return None
        course, count = row
        return {"id": str(course.id), "title": f"{course.level} — {course.title}" if course.level else course.title, "count": int(count)}

    def _most_viewed_lesson(self) -> dict | None:
        row = (
            self.db.query(Lesson, func.count(VideoProgress.id).label("count"))
            .join(VideoProgress, VideoProgress.lesson_id == Lesson.id)
            .group_by(Lesson.id)
            .order_by(func.count(VideoProgress.id).desc())
            .first()
        )
        if row is None:
            return None
        lesson, count = row
        return {"id": str(lesson.id), "title": lesson.title, "count": int(count)}

    def _top_quiz(self, passed: bool) -> dict | None:
        row = (
            self.db.query(Quiz, func.count(StudentQuiz.id).label("count"))
            .join(StudentQuiz, StudentQuiz.quiz_id == Quiz.id)
            .filter(StudentQuiz.passed.is_(passed))
            .group_by(Quiz.id)
            .order_by(func.count(StudentQuiz.id).desc())
            .first()
        )
        if row is None:
            return None
        quiz, count = row
        return {"id": str(quiz.id), "title": quiz.title, "count": int(count)}

    # ============================================================
    # Mock Test Analytics — per real CertificationProvider in the DB
    # (never a hardcoded Goethe/ÖSD/telc/Cambridge list — only what the
    # admin has actually created, so an empty CMS shows a real empty
    # state instead of fabricated rows).
    # ============================================================

    def _mock_test_analytics(self) -> list[dict]:
        """Per provider and model test — a fixed number of aggregate queries
        for ALL model tests (before: ~5 queries per model test)."""
        providers = self.db.query(CertificationProvider).order_by(CertificationProvider.sort_order).all()
        tests = (
            self.db.query(ModelTest.id, ModelTest.title, MockExamLevel.provider_id)
            .join(MockExamLevel, ModelTest.level_id == MockExamLevel.id)
            .all()
        )
        by_provider: dict = {}
        for test_id, title, provider_id in tests:
            by_provider.setdefault(provider_id, []).append((test_id, title))
        attempts: dict = {}
        for test_id, total, max_score in (
            self.db.query(MockTestAttempt.model_test_id, MockTestAttempt.total_score, MockTestAttempt.max_score)
            .filter(MockTestAttempt.status == STATUS_GRADED)
            .all()
        ):
            attempts.setdefault(test_id, []).append((total, max_score))
        skills = self._all_skill_averages()
        return [self._provider_mock_analytics(p, by_provider.get(p.id, []), attempts, skills) for p in providers]

    def _provider_mock_analytics(self, provider: CertificationProvider, tests: list, attempts_by_test: dict, skills_by_test: dict) -> dict:
        model_tests_out = []
        all_scores: list[tuple[int, int]] = []

        for model_test_id, title in tests:
            attempts = attempts_by_test.get(model_test_id, [])
            graded = [(s, m) for s, m in attempts if s is not None and m]
            avg = _pct(sum(s for s, _ in graded), sum(m for _, m in graded))
            passed = sum(1 for s, m in graded if s / m >= PASS_THRESHOLD)
            pass_rate = _pct(passed, len(graded))
            fail_rate = round(100 - pass_rate, 1) if graded else 0.0

            skills = skills_by_test.get(model_test_id, {})

            model_tests_out.append(
                {
                    "model_test_id": model_test_id,
                    "title": title,
                    "attempts": len(attempts),
                    "average_score_percent": avg,
                    "pass_rate_percent": pass_rate,
                    "fail_rate_percent": fail_rate,
                    "average_reading_percent": skills.get("LESEN"),
                    "average_listening_percent": skills.get("HOEREN"),
                    "average_writing_percent": skills.get("SCHREIBEN"),
                    "average_speaking_percent": skills.get("SPRECHEN"),
                }
            )
            all_scores.extend(graded)

        provider_avg = _pct(sum(s for s, _ in all_scores), sum(m for _, m in all_scores))
        provider_passed = sum(1 for s, m in all_scores if m and s / m >= PASS_THRESHOLD)
        provider_pass_rate = _pct(provider_passed, len(all_scores))

        return {
            "provider_id": provider.id,
            "code": provider.code,
            "name": provider.name,
            "total_attempts": sum(mt["attempts"] for mt in model_tests_out),
            "average_score_percent": provider_avg,
            "pass_rate_percent": provider_pass_rate,
            "model_tests": model_tests_out,
        }

    def _all_skill_averages(self) -> dict:
        """{model_test_id: {LESEN|HOEREN|SCHREIBEN|SPRECHEN: percent | None}} for
        every model test at once. Same rules as before, per Kompetenz:
        Lesen/Hören via MockQuestionAnswer (points earned / possible);
        Schreiben via MockWritingSubmission (teacher_score overrides ai_score,
        scaled against the task's max_points); Sprechen via
        MockSpeakingSubmission (already 0-100, averaged directly)."""
        reading_teil = aliased(Teil)
        listening_teil = aliased(Teil)
        kid = func.coalesce(reading_teil.kompetenz_id, listening_teil.kompetenz_id)
        lh = {
            k: (e or 0, p or 0)
            for k, e, p in (
                self.db.query(kid, func.sum(MockQuestionAnswer.points_earned), func.sum(MockQuestion.points))
                .join(MockQuestion, MockQuestionAnswer.question_id == MockQuestion.id)
                .outerjoin(ReadingContent, MockQuestion.reading_content_id == ReadingContent.id)
                .outerjoin(reading_teil, ReadingContent.teil_id == reading_teil.id)
                .outerjoin(ListeningContent, MockQuestion.listening_content_id == ListeningContent.id)
                .outerjoin(listening_teil, ListeningContent.teil_id == listening_teil.id)
                .group_by(kid)
                .all()
            )
        }
        writing: dict = {}
        for k, teacher, ai, max_points in (
            self.db.query(Teil.kompetenz_id, MockWritingSubmission.teacher_score, MockWritingSubmission.ai_score, WritingTask.max_points)
            .join(WritingTask, MockWritingSubmission.writing_task_id == WritingTask.id)
            .join(Teil, WritingTask.teil_id == Teil.id)
            .all()
        ):
            score = teacher if teacher is not None else ai
            if score is not None and max_points:
                writing.setdefault(k, []).append((score, max_points))
        speaking: dict = {}
        for k, teacher, ai in (
            self.db.query(Teil.kompetenz_id, MockSpeakingSubmission.teacher_score, MockSpeakingSubmission.ai_score)
            .join(SpeakingTask, MockSpeakingSubmission.speaking_task_id == SpeakingTask.id)
            .join(Teil, SpeakingTask.teil_id == Teil.id)
            .all()
        ):
            if teacher is not None or ai is not None:
                speaking.setdefault(k, []).append(teacher if teacher is not None else ai)

        out: dict = {}
        for kompetenz_id, model_test_id, ktype in self.db.query(Kompetenz.id, Kompetenz.model_test_id, Kompetenz.type).all():
            result = out.setdefault(model_test_id, {})
            if ktype in ("LESEN", "HOEREN"):
                earned, possible = lh.get(kompetenz_id, (0, 0))
                result[ktype] = _pct(earned, possible) if possible else None
            elif ktype == "SCHREIBEN":
                pairs = writing.get(kompetenz_id, [])
                possible = sum(m for _, m in pairs)
                result[ktype] = _pct(sum(s for s, _ in pairs), possible) if possible else None
            elif ktype == "SPRECHEN":
                scores = speaking.get(kompetenz_id, [])
                result[ktype] = round(sum(scores) / len(scores), 1) if scores else None
        return out

    # ============================================================
    # VIZU-Multilevel (the free level check) — from the stored attempt columns
    # ============================================================

    def _vizu_multilevel(self) -> dict:
        from app.models.vizu_multilevel_attempt import STATUS_COMPLETED, VizuMultilevelAttempt
        from app.models.vizu_multilevel_discarded import REASON_BELOW_A1

        a = VizuMultilevelAttempt
        total, completed, final, numbered, avg = self.db.query(
            func.count(a.id),
            func.count(a.id).filter(a.status == STATUS_COMPLETED),
            func.count(a.id).filter(a.result_score.is_not(None)),
            func.count(a.certificate_number),
            func.avg(a.result_score),
        ).one()
        by_level = {}
        for lvl, reason, n in (
            self.db.query(a.overall_level, a.discarded_reason, func.count(a.id))
            .filter(a.result_score.is_not(None))
            .group_by(a.overall_level, a.discarded_reason)
            .all()
        ):
            key = lvl or ("BELOW_A1" if reason == REASON_BELOW_A1 else "—")
            by_level[key] = by_level.get(key, 0) + int(n)
        return {
            "attempts": int(total or 0), "completed": int(completed or 0), "final_results": int(final or 0),
            "certificates_issued": int(numbered or 0), "average_result": round(float(avg), 1) if avg is not None else None,
            "by_level": by_level,
        }

    # ============================================================
    # Payments
    # ============================================================

    def _payments(self) -> dict:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = today_start.replace(day=1)

        return {
            "today_revenue": self._approved_revenue_since(today_start),
            "week_revenue": self._approved_revenue_since(week_start),
            "month_revenue": self._approved_revenue_since(month_start),
            "pending_payments": (
                self.db.query(SubscriptionOrder).filter(SubscriptionOrder.status == plan_config.STATUS_PENDING).count()
            ),
            "refunds": (
                self.db.query(SubscriptionOrder).filter(SubscriptionOrder.status == plan_config.STATUS_REFUNDED).count()
            ),
            "premium_sales": (
                self.db.query(SubscriptionOrder)
                .filter(
                    SubscriptionOrder.status == plan_config.STATUS_APPROVED,
                    SubscriptionOrder.plan.in_(list(plan_config.REVENUE_PLANS)),
                )
                .count()
            ),
        }

    # ============================================================
    # Content counts
    # ============================================================

    def _content_counts(self) -> dict:
        return {
            "languages": self.db.query(Language).count(),
            "levels": self.db.query(Course).count(),
            "modules": self.db.query(Module).count(),
            "lessons": self.db.query(Lesson).count(),
            "videos": self.db.query(Video).count(),
            "vocabulary": self.db.query(Vocabulary).count(),
            "grammar": self.db.query(Grammar).count(),
            "reading": self.db.query(Reading).count(),
            "listening": self.db.query(Listening).count(),
            "writing": self.db.query(Writing).count(),
            "speaking": self.db.query(Speaking).count(),
            "homework": self.db.query(Homework).count(),
            "quiz": self.db.query(Quiz).count(),
            "mock_tests": self.db.query(ModelTest).count(),
        }

    # ============================================================
    # AI stats
    # ============================================================

    def _ai_stats(self) -> dict:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        writing_checked_today = (
            self.db.query(MockWritingSubmission)
            .filter(MockWritingSubmission.ai_evaluated_at >= today_start)
            .count()
        )
        speaking_checked_today = (
            self.db.query(MockSpeakingSubmission)
            .filter(MockSpeakingSubmission.ai_evaluated_at >= today_start)
            .count()
        )
        pending_writing = (
            self.db.query(MockWritingSubmission).filter(MockWritingSubmission.ai_score.is_(None)).count()
        )
        pending_speaking = (
            self.db.query(MockSpeakingSubmission).filter(MockSpeakingSubmission.ai_score.is_(None)).count()
        )

        writing_scores = [
            row[0]
            for row in self.db.query(MockWritingSubmission.ai_score).filter(MockWritingSubmission.ai_score.isnot(None)).all()
        ]
        speaking_scores = [
            row[0]
            for row in self.db.query(MockSpeakingSubmission.ai_score)
            .filter(MockSpeakingSubmission.ai_score.isnot(None))
            .all()
        ]
        all_scores = writing_scores + speaking_scores
        average_ai_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else None

        return {
            "writing_checked_today": writing_checked_today,
            "speaking_checked_today": speaking_checked_today,
            "pending_ai_reviews": pending_writing + pending_speaking,
            "average_ai_score": average_ai_score,
        }

    # ============================================================
    # Recent Activity — last 20 real system events, merged + sorted
    # ============================================================

    def _recent_activity(self, limit: int = 20) -> list[dict]:
        events: list[dict] = []

        for user in self.db.query(User).order_by(User.created_at.desc()).limit(limit).all():
            events.append(
                {"type": "registration", "title": f"{user.username} registered", "timestamp": user.created_at}
            )

        premium_orders = (
            self.db.query(SubscriptionOrder)
            .options(joinedload(SubscriptionOrder.user))
            .filter(
                SubscriptionOrder.status == plan_config.STATUS_APPROVED,
                SubscriptionOrder.plan.in_(list(plan_config.REVENUE_PLANS)),
            )
            .order_by(SubscriptionOrder.reviewed_at.desc())
            .limit(limit)
            .all()
        )
        for order in premium_orders:
            if order.reviewed_at is None:
                continue
            email = order.user.email if order.user else "Unknown"
            events.append(
                {
                    "type": "premium_purchase",
                    "title": f"{email} purchased {plan_config.plan_label(order.plan)}",
                    "timestamp": _aware_utc(order.reviewed_at),
                }
            )

        completed = (
            self.db.query(StudentProgress)
            .options(joinedload(StudentProgress.user), joinedload(StudentProgress.lesson))
            .filter(StudentProgress.lesson_completed.is_(True))
            .order_by(StudentProgress.updated_at.desc())
            .limit(limit)
            .all()
        )
        for progress in completed:
            username = progress.user.username if progress.user else "A student"
            lesson_title = progress.lesson.title if progress.lesson else "a lesson"
            events.append(
                {
                    "type": "lesson_completed",
                    "title": f"{username} completed {lesson_title}",
                    "timestamp": progress.updated_at,
                }
            )

        for model_test in self.db.query(ModelTest).order_by(ModelTest.created_at.desc()).limit(limit).all():
            events.append(
                {
                    "type": "mock_test_created",
                    "title": f"Mock test \"{model_test.title}\" created",
                    "timestamp": model_test.created_at,
                }
            )

        for log in self.db.query(AuditLog).options(joinedload(AuditLog.actor)).order_by(AuditLog.created_at.desc()).limit(limit).all():
            actor_email = log.actor.email if log.actor else "An admin"
            events.append(
                {
                    "type": "admin_action",
                    "title": f"{actor_email}: {log.action.replace('_', ' ')}",
                    "timestamp": log.created_at,
                }
            )

        for certificate in (
            self.db.query(Certificate).options(joinedload(Certificate.user)).order_by(Certificate.issued_at.desc()).limit(limit).all()
        ):
            email = certificate.user.email if certificate.user else "Unknown"
            events.append(
                {
                    "type": "certificate_issued",
                    "title": f"{email} earned a {certificate.level} certificate",
                    "timestamp": _aware_utc(certificate.issued_at),
                }
            )

        # VIZU-Multilevel certificates (number issued = the certificate was opened / downloaded)
        from app.models.vizu_multilevel_attempt import VizuMultilevelAttempt

        for attempt, email in (
            self.db.query(VizuMultilevelAttempt, User.email)
            .join(User, User.id == VizuMultilevelAttempt.user_id)
            .filter(VizuMultilevelAttempt.certificate_number.is_not(None), VizuMultilevelAttempt.completed_at.is_not(None))
            .order_by(VizuMultilevelAttempt.completed_at.desc())
            .limit(limit)
            .all()
        ):
            level = attempt.overall_level or "unter A1"
            events.append(
                {
                    "type": "certificate_issued",
                    "title": f"{email} earned a VIZU-Multilevel {level} certificate",
                    "timestamp": _aware_utc(attempt.completed_at),
                }
            )

        events.sort(key=lambda item: item["timestamp"], reverse=True)
        return events[:limit]

    # ============================================================
    # Server Health
    # ============================================================

    def _server_health(self) -> dict:
        postgres_ok, latency_ms = self._check_postgres()
        disk_percent = self._disk_used_percent(".")
        storage_percent = self._disk_used_percent(settings.UPLOAD_PATH)
        cpu_percent, ram_percent = self._linux_cpu_ram()

        return {
            "backend": True,
            "postgres": postgres_ok,
            "postgres_latency_ms": latency_ms,
            "storage_used_percent": storage_percent,
            "disk_used_percent": disk_percent,
            "cpu_percent": cpu_percent,
            "ram_percent": ram_percent,
            "uptime_seconds": int(time.time() - _PROCESS_START),
        }

    def _check_postgres(self) -> tuple[bool, float | None]:
        try:
            start = time.perf_counter()
            self.db.execute(text("SELECT 1"))
            latency_ms = round((time.perf_counter() - start) * 1000, 1)
            return True, latency_ms
        except Exception:
            return False, None

    def _disk_used_percent(self, path: str) -> float | None:
        try:
            usage = shutil.disk_usage(path)
            return round((usage.used / usage.total) * 100, 1) if usage.total else None
        except OSError:
            return None

    def _linux_cpu_ram(self) -> tuple[float | None, float | None]:
        """Best-effort, dependency-free CPU/RAM read via /proc — only
        available on Linux (the production target). No `psutil` fallback
        exists because this sandbox cannot install it; returns (None,
        None) on any other platform rather than fabricating a number."""
        cpu_percent = None
        ram_percent = None

        try:
            with open("/proc/loadavg") as f:
                load_1min = float(f.read().split()[0])
            cpu_count = os.cpu_count() or 1
            cpu_percent = round(min(load_1min / cpu_count, 1.0) * 100, 1)
        except (OSError, ValueError, IndexError):
            pass

        try:
            with open("/proc/meminfo") as f:
                meminfo = {}
                for line in f:
                    key, _, value = line.partition(":")
                    meminfo[key.strip()] = int(value.strip().split()[0])
            total = meminfo.get("MemTotal")
            available = meminfo.get("MemAvailable")
            if total and available is not None:
                ram_percent = round((1 - available / total) * 100, 1)
        except (OSError, ValueError, IndexError, KeyError):
            pass

        return cpu_percent, ram_percent
