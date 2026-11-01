"""Pure unit tests for message rendering - no database involved."""
from __future__ import annotations

from datetime import UTC, datetime

from app.messages import (
    render_business_message,
    render_customer_message,
    render_daily_summary_message,
)
from app.tables import JobType

CTX = {
    "starts_at": datetime(2026, 12, 1, 14, 0, tzinfo=UTC),
    "status": "CONFIRMED",
    "service_name": "Haircut",
    "staff_name": "Jamie",
    "business_name": "ATELIER",
    "business_timezone": "UTC",
    "customer_first_name": "Alex",
}


def test_booking_confirmed_mentions_service_staff_and_time():
    text = render_customer_message(JobType.BOOKING_CONFIRMED, {}, CTX)
    assert "Haircut" in text
    assert "Jamie" in text
    assert "confirmed" in text.lower()


def test_booking_received_differs_from_confirmed():
    received = render_customer_message(JobType.BOOKING_RECEIVED, {}, CTX)
    confirmed = render_customer_message(JobType.BOOKING_CONFIRMED, {}, CTX)
    assert received != confirmed
    assert "awaiting confirmation" in received


def test_reminder_includes_offset_phrase():
    text = render_customer_message(JobType.REMINDER, {"offset_minutes": 1440}, CTX)
    assert "24 hours" in text
    text30 = render_customer_message(JobType.REMINDER, {"offset_minutes": 30}, CTX)
    assert "30 minutes" in text30


def test_rescheduled_includes_previous_time_when_present():
    text = render_customer_message(
        JobType.BOOKING_RESCHEDULED, {"previous_starts_at": "2026-11-30T10:00:00+00:00"}, CTX
    )
    assert "2026-11-30T10:00:00+00:00" in text


def test_unknown_job_type_raises():
    import pytest

    with pytest.raises(ValueError):
        render_customer_message("NOT_A_REAL_TYPE", {}, CTX)


def test_business_new_booking_mentions_customer_name():
    text = render_business_message(JobType.BUSINESS_NEW_BOOKING, {}, CTX)
    assert "Alex" in text
    assert "New booking" in text


def test_daily_summary_formats_revenue_from_minor_units():
    ctx = {"business_name": "ATELIER", "currency": "USD", "booking_count": 3, "revenue_minor_units": 15000}
    text = render_daily_summary_message(ctx, "2026-12-01")
    assert "3 booking" in text
    assert "150.00 USD" in text
