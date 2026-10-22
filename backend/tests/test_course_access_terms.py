from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.core.security.jwt import (
    create_resource_token,
    create_video_stream_token,
    decode_resource_token_claims,
    decode_video_stream_claims,
)
from app.models.user import User
from app.services.vizu_pay import access
from app.services.vizu_pay.offers import OFFER_ACCESS_MONTHS, access_duration_months
from app.services.vizu_pay.purchases import (
    activate_course_access,
    add_calendar_months,
    course_access_is_active,
    extend_course_access,
)
from app.schemas.vizu_pay.schema import ExtendOrderAccessRequest


UTC = timezone.utc


@pytest.mark.parametrize(
    ("start", "months", "expected"),
    [
        (datetime(2024, 1, 31, 12, 30, tzinfo=UTC), 1, datetime(2024, 2, 29, 12, 30, tzinfo=UTC)),
        (datetime(2023, 1, 31, 12, 30, tzinfo=UTC), 1, datetime(2023, 2, 28, 12, 30, tzinfo=UTC)),
        (datetime(2024, 2, 29, 12, 30, tzinfo=UTC), 12, datetime(2025, 2, 28, 12, 30, tzinfo=UTC)),
        (datetime(2026, 11, 30, 12, 30, tzinfo=UTC), 4, datetime(2027, 3, 30, 12, 30, tzinfo=UTC)),
        (datetime(2026, 12, 31, 12, 30, tzinfo=UTC), 9, datetime(2027, 9, 30, 12, 30, tzinfo=UTC)),
    ],
)
def test_calendar_month_addition_clamps_month_end(start, months, expected):
    assert add_calendar_months(start, months) == expected


def test_course_and_package_durations_are_centrally_configured():
    assert OFFER_ACCESS_MONTHS == {
        "A1": 1,
        "A2": 1,
        "B1": 2,
        "B2": 3,
        "C1": 2,
        "A1_B1": 4,
        "A1_C1": 9,
    }
    assert access_duration_months("A1_B1") == 4
    with pytest.raises(ValueError):
        access_duration_months("UNKNOWN")


def test_successful_activation_sets_order_specific_utc_window():
    activated = datetime(2024, 1, 31, 9, 15, tzinfo=UTC)
    first = SimpleNamespace(plan="A1", purchase_date=None, access_start_date=None, access_end_date=None)
    second = SimpleNamespace(plan="A1_B1", purchase_date=None, access_start_date=None, access_end_date=None)

    activate_course_access(first, activated)
    activate_course_access(second, activated)

    assert first.purchase_date == first.access_start_date == activated
    assert first.access_end_date == datetime(2024, 2, 29, 9, 15, tzinfo=UTC)
    assert second.purchase_date == second.access_start_date == activated
    assert second.access_end_date == datetime(2024, 5, 31, 9, 15, tzinfo=UTC)


def test_access_requires_approved_status_and_uses_exclusive_end():
    start = datetime(2026, 1, 31, 10, tzinfo=UTC)
    end = datetime(2026, 2, 28, 10, tzinfo=UTC)
    order = SimpleNamespace(
        status="APPROVED",
        access_start_date=start,
        access_end_date=end,
    )

    assert not course_access_is_active(order, start - timedelta(seconds=1))
    assert course_access_is_active(order, start)
    assert course_access_is_active(order, end - timedelta(seconds=1))
    assert not course_access_is_active(order, end)
    order.status = "REJECTED"
    assert not course_access_is_active(order, start)
    order.status = "REFUNDED"
    assert not course_access_is_active(order, start)


def test_repurchase_and_admin_extension_keep_each_order_independent():
    now = datetime(2026, 4, 30, 10, tzinfo=UTC)
    first = SimpleNamespace(
        plan="A1",
        status="APPROVED",
        purchase_date=now,
        access_start_date=now,
        access_end_date=datetime(2026, 5, 30, 10, tzinfo=UTC),
    )
    second = SimpleNamespace(plan="A1", purchase_date=None, access_start_date=None, access_end_date=None)

    activate_course_access(second, now)
    extend_course_access(first, 1, now)

    assert first.access_end_date == datetime(2026, 6, 30, 10, tzinfo=UTC)
    assert second.access_end_date == datetime(2026, 5, 30, 10, tzinfo=UTC)
    first.access_end_date = datetime(2026, 4, 1, 10, tzinfo=UTC)
    extend_course_access(first, 1, now)
    assert first.access_end_date == datetime(2026, 5, 30, 10, tzinfo=UTC)


def test_unapproved_order_cannot_be_extended():
    order = SimpleNamespace(
        status="PENDING",
        purchase_date=None,
        access_start_date=None,
        access_end_date=None,
    )
    with pytest.raises(ValueError):
        extend_course_access(order, 1, datetime(2026, 1, 1, tzinfo=UTC))


def test_admin_extension_requires_a_nonblank_audit_reason():
    assert ExtendOrderAccessRequest(months=2, reason=" Staff correction ").reason == "Staff correction"
    with pytest.raises(ValueError):
        ExtendOrderAccessRequest(months=2, reason="   ")


def test_owned_levels_query_requires_an_active_approved_access_window(monkeypatch):
    with Session() as db:
        user = User(id=uuid4())
        db.add(user)
        rows = SimpleNamespace(all=lambda: ["A1"])
        captured = []

        def scalars(query):
            captured.append(query)
            return rows

        monkeypatch.setattr(db, "scalars", scalars)
        assert access.owned_levels(user) == {"A1"}
        sql = str(captured[0].compile(dialect=postgresql.dialect()))
        assert "access_start_date <=" in sql
        assert "access_end_date >" in sql
        assert "subscription_orders.status =" in sql


def test_signed_media_tokens_are_user_scoped_for_access_rechecks():
    video_token = create_video_stream_token("video-id", "student-id")
    resource_token = create_resource_token("resource-id", "student-id")

    assert decode_video_stream_claims(video_token) == ("video-id", "student-id")
    assert decode_resource_token_claims(resource_token) == ("resource-id", "student-id")
    with pytest.raises(ValueError):
        decode_video_stream_claims(create_video_stream_token("video-id"))


def test_naive_timestamp_inputs_are_considered_utc():
    naive = datetime(2026, 4, 1, 10)
    assert add_calendar_months(naive, 1) == datetime(2026, 5, 1, 10)
    order = SimpleNamespace(
        status="APPROVED",
        access_start_date=naive.replace(tzinfo=UTC),
        access_end_date=datetime(2026, 5, 1, 10, tzinfo=UTC),
    )
    assert course_access_is_active(order, naive)
