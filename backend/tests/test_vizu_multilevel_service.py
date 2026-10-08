"""VIZU-Multilevel attempt lifecycle (app/services/vizu_multilevel/service.py):
owner scoping, the Lesen -> Hören -> Schreiben -> Sprechen order, the
server-authoritative 20-minute window, and the overall-level rules
(lowest competency wins; below A1 / missing data never invents a level)."""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.models.vizu_multilevel_attempt import STATUS_COMPLETED, STATUS_IN_PROGRESS, VizuMultilevelAttempt
from app.services.vizu_multilevel import service
from app.services.vizu_multilevel.service import SectionFlowError


def _attempt(**kwargs) -> VizuMultilevelAttempt:
    return VizuMultilevelAttempt(user_id="u1", status=kwargs.pop("status", STATUS_IN_PROGRESS), **kwargs)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TestCreateAttempt(unittest.TestCase):
    """Up to 3 attempts per student (was: one ever) — see also
    test_vizu_multilevel_attempts.py for the full limit / best-result rules."""

    def test_new_attempt_is_in_progress_with_no_levels(self):
        db = MagicMock()
        db.scalars.return_value = []  # the student has no attempt yet
        attempt = service.create_attempt(db, user_id="u1")
        self.assertEqual(attempt.status, STATUS_IN_PROGRESS)
        self.assertEqual(attempt.attempt_number, 1)
        self.assertIsNone(attempt.overall_level)
        db.add.assert_called_once_with(attempt)

    def test_no_second_attempt_while_one_is_in_progress(self):
        db = MagicMock()
        db.scalars.return_value = [_attempt(attempt_number=1)]
        with self.assertRaises(SectionFlowError) as ctx:
            service.create_attempt(db, user_id="u1")
        self.assertEqual(ctx.exception.code, "ATTEMPT_ALREADY_EXISTS")
        db.add.assert_not_called()

    def test_no_fourth_attempt_after_three_completed(self):
        db = MagicMock()
        db.scalars.return_value = [_attempt(status=STATUS_COMPLETED, attempt_number=n) for n in (1, 2, 3)]
        with self.assertRaises(SectionFlowError) as ctx:
            service.create_attempt(db, user_id="u1")
        self.assertEqual(ctx.exception.code, "MAX_ATTEMPTS_REACHED")
        db.add.assert_not_called()


class TestMinimumAnswers(unittest.TestCase):
    def test_min_is_five_or_all_if_fewer_items(self):
        self.assertEqual(service.min_answers_required(20), 5)
        self.assertEqual(service.min_answers_required(3), 3)
        self.assertEqual(service.min_answers_required(0), 0)

    def test_four_answers_rejected_five_accepted(self):
        attempt = _attempt(lesen_started_at=_now())
        with self.assertRaises(SectionFlowError) as ctx:
            service.check_min_answers(attempt, "lesen", 4, 20)
        self.assertEqual(ctx.exception.code, "MIN_ANSWERS_REQUIRED")
        service.check_min_answers(attempt, "lesen", 5, 20)  # no exception

    def test_time_up_allows_fewer_answers(self):
        attempt = _attempt(lesen_started_at=_now() - timedelta(seconds=service.SECTION_SECONDS + 1))
        service.check_min_answers(attempt, "lesen", 0, 20)  # no exception

    def test_finished_attempt_cannot_be_submitted_again(self):
        with self.assertRaises(SectionFlowError) as ctx:
            service.ensure_attempt_active(_attempt(status=STATUS_COMPLETED))
        self.assertEqual(ctx.exception.code, "ATTEMPT_ALREADY_COMPLETED")


class TestOwnerScoping(unittest.TestCase):
    def test_get_own_attempt_scopes_by_user_id(self):
        db = MagicMock()
        db.scalar.return_value = None
        self.assertIsNone(service.get_own_attempt(db, user_id="u1", attempt_id="a1"))
        db.scalar.assert_called_once()

    def test_complete_returns_none_for_someone_elses_attempt(self):
        db = MagicMock()
        db.scalar.return_value = None  # get_own_attempt finds nothing for this user
        self.assertIsNone(service.complete_attempt(db, user_id="attacker", attempt_id="victim-attempt"))
        db.commit.assert_not_called()

    def test_cannot_complete_before_every_competency_is_submitted(self):
        db = MagicMock()
        db.scalar.return_value = _attempt(lesen_submitted_at=_now())
        with self.assertRaises(SectionFlowError) as ctx:
            service.complete_attempt(db, user_id="u1", attempt_id="a1")
        self.assertEqual(ctx.exception.code, "SECTIONS_NOT_SUBMITTED")

    def test_completed_attempt_cannot_be_completed_again(self):
        db = MagicMock()
        db.scalar.return_value = _attempt(status=STATUS_COMPLETED)
        with self.assertRaises(SectionFlowError) as ctx:
            service.complete_attempt(db, user_id="u1", attempt_id="a1")
        self.assertEqual(ctx.exception.code, "ATTEMPT_ALREADY_COMPLETED")
        db.commit.assert_not_called()


class TestServerAuthoritativeTimer(unittest.TestCase):
    def test_start_stamps_once_and_keeps_the_same_deadline(self):
        db = MagicMock()
        attempt = _attempt()
        first = service.start_section(db, attempt, "lesen")
        second = service.start_section(db, attempt, "lesen")
        self.assertIsNotNone(first["started_at"])
        self.assertEqual(first["deadline_at"], second["deadline_at"])
        self.assertEqual(db.commit.call_count, 1)  # the second call stamps nothing
        self.assertLessEqual(first["seconds_remaining"], service.SECTION_SECONDS)
        self.assertGreater(first["seconds_remaining"], service.SECTION_SECONDS - 5)

    def test_section_is_open_within_deadline_and_grace_then_closed(self):
        db = MagicMock()
        within = _attempt(lesen_started_at=_now() - timedelta(seconds=service.SECTION_SECONDS + service.GRACE_SECONDS - 5))
        self.assertTrue(service.ensure_section_open(db, within, "lesen"))
        late = _attempt(lesen_started_at=_now() - timedelta(seconds=service.SECTION_SECONDS + service.GRACE_SECONDS + 5))
        self.assertFalse(service.ensure_section_open(db, late, "lesen"))

    def test_remaining_time_never_negative(self):
        attempt = _attempt(lesen_started_at=_now() - timedelta(hours=2))
        self.assertEqual(service.section_timing(attempt, "lesen")["seconds_remaining"], 0)


class TestFlowOrder(unittest.TestCase):
    def test_cannot_start_a_competency_before_the_previous_one_is_submitted(self):
        db = MagicMock()
        for skill in ("hoeren", "schreiben", "sprechen"):
            with self.assertRaises(SectionFlowError) as ctx:
                service.start_section(db, _attempt(), skill)
            self.assertEqual(ctx.exception.code, "PREVIOUS_SECTION_NOT_SUBMITTED")

    def test_next_competency_unlocks_after_submit(self):
        db = MagicMock()
        attempt = _attempt(lesen_submitted_at=_now())
        self.assertIsNotNone(service.start_section(db, attempt, "hoeren")["started_at"])

    def test_unknown_skill_and_finished_attempt_are_rejected(self):
        db = MagicMock()
        with self.assertRaises(SectionFlowError):
            service.start_section(db, _attempt(), "grammatik")
        with self.assertRaises(SectionFlowError):
            service.start_section(db, _attempt(status=STATUS_COMPLETED), "lesen")

    def test_cannot_write_into_a_submitted_competency(self):
        db = MagicMock()
        attempt = _attempt(lesen_started_at=_now(), lesen_submitted_at=_now())
        with self.assertRaises(SectionFlowError) as ctx:
            service.ensure_section_open(db, attempt, "lesen")
        self.assertEqual(ctx.exception.code, "SECTION_ALREADY_SUBMITTED")

    def test_state_marks_running_available_and_locked(self):
        attempt = _attempt(lesen_started_at=_now())
        statuses = [s["status"] for s in service.get_state(attempt)["sections"]]
        self.assertEqual(statuses, [service.RUNNING, service.LOCKED, service.LOCKED, service.LOCKED])
        attempt = _attempt(lesen_started_at=_now(), lesen_submitted_at=_now())
        statuses = [s["status"] for s in service.get_state(attempt)["sections"]]
        self.assertEqual(statuses, [service.SUBMITTED, service.AVAILABLE, service.LOCKED, service.LOCKED])


def _comp(skill, status, level=None):
    return {"skill": skill, "status": status, "raw_score": None, "max_score": None, "percentage": None, "level": level}


class TestOverallResult(unittest.TestCase):
    def test_no_content_anywhere_is_no_content_never_a_level(self):
        comps = [_comp(s, service.R_NO_CONTENT) for s in service.SKILLS]
        self.assertEqual(service.overall_result(comps), {"status": service.O_NO_CONTENT, "level": None})

    def test_overall_is_the_lowest_competency_level(self):
        comps = [
            _comp("lesen", service.R_GRADED, "C1"),
            _comp("hoeren", service.R_GRADED, "B1"),
            _comp("schreiben", service.R_GRADED, "B2"),
            _comp("sprechen", service.R_GRADED, "A2"),
        ]
        self.assertEqual(service.overall_result(comps), {"status": service.O_FINAL, "level": "A2"})

    def test_a_graded_competency_without_a_level_means_below_a1(self):
        comps = [
            _comp("lesen", service.R_GRADED, "B2"),
            _comp("hoeren", service.R_GRADED, None),
            _comp("schreiben", service.R_PENDING_REVIEW),
            _comp("sprechen", service.R_NOT_SUBMITTED),
        ]
        self.assertEqual(service.overall_result(comps), {"status": service.O_BELOW_A1, "level": None})

    def test_pending_teacher_review_does_not_fabricate_a_level(self):
        comps = [
            _comp("lesen", service.R_GRADED, "B2"),
            _comp("hoeren", service.R_GRADED, "B1"),
            _comp("schreiben", service.R_PENDING_REVIEW),
            _comp("sprechen", service.R_NO_CONTENT),
        ]
        self.assertEqual(service.overall_result(comps), {"status": service.O_PENDING_REVIEW, "level": None})

    def test_unsubmitted_competency_keeps_the_result_in_progress(self):
        comps = [_comp("lesen", service.R_GRADED, "B2"), _comp("hoeren", service.R_NOT_SUBMITTED)]
        self.assertEqual(service.overall_result(comps)["status"], service.O_IN_PROGRESS)

    def test_competencies_without_content_are_ignored(self):
        comps = [_comp("lesen", service.R_GRADED, "B1"), _comp("hoeren", service.R_NO_CONTENT)]
        self.assertEqual(service.overall_result(comps), {"status": service.O_FINAL, "level": "B1"})


class TestPercentage(unittest.TestCase):
    def test_percentage_needs_a_positive_maximum(self):
        self.assertEqual(service._percentage(5, 10), 50.0)
        self.assertIsNone(service._percentage(5, 0))
        self.assertIsNone(service._percentage(None, 10))


if __name__ == "__main__":
    unittest.main()
