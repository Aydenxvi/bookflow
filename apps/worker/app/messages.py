"""Renders the Telegram message text for a notification job, in English
(i18n is Phase 5 scope — see ROADMAP.md)."""
from __future__ import annotations

from app.context import local_time_str
from app.tables import JobType


def _offset_phrase(offset_minutes: int) -> str:
    if offset_minutes % 60 == 0 and offset_minutes >= 60:
        hours = offset_minutes // 60
        return f"{hours} hour{'s' if hours != 1 else ''}"
    return f"{offset_minutes} minutes"


def render_customer_message(job_type: str, payload: dict, ctx: dict) -> str:
    when = local_time_str(ctx["starts_at"], ctx["business_timezone"])
    service, staff_name, business = ctx["service_name"], ctx["staff_name"], ctx["business_name"]

    if job_type == JobType.BOOKING_RECEIVED:
        return (
            f"Thanks! Your request for <b>{service}</b> with {staff_name} at {business} "
            f"on {when} has been received and is awaiting confirmation."
        )
    if job_type == JobType.BOOKING_CONFIRMED:
        return f"Your booking for <b>{service}</b> with {staff_name} at {business} on {when} is confirmed. See you then!"
    if job_type == JobType.BOOKING_REJECTED:
        return f"Unfortunately your request for <b>{service}</b> at {business} on {when} couldn't be confirmed."
    if job_type == JobType.BOOKING_CANCELLED:
        return f"Your booking for <b>{service}</b> with {staff_name} at {business} on {when} has been cancelled."
    if job_type == JobType.BOOKING_RESCHEDULED:
        previous = payload.get("previous_starts_at")
        previous_str = f" (previously {previous})" if previous else ""
        return f"Your booking with {staff_name} at {business} has been moved to {when}{previous_str}."
    if job_type == JobType.REMINDER:
        phrase = _offset_phrase(int(payload.get("offset_minutes", 0)))
        return f"Reminder: your <b>{service}</b> appointment with {staff_name} at {business} is in {phrase} ({when})."
    raise ValueError(f"No customer-facing template for job_type={job_type!r}")


def render_business_message(job_type: str, payload: dict, ctx: dict) -> str:
    when = local_time_str(ctx["starts_at"], ctx["business_timezone"])
    service, staff_name = ctx["service_name"], ctx["staff_name"]
    customer = ctx.get("customer_first_name", "A customer")

    if job_type == JobType.BUSINESS_NEW_BOOKING:
        return f"New booking: <b>{service}</b> with {staff_name} on {when} — {customer}."
    if job_type == JobType.BUSINESS_CANCELLATION:
        return f"Cancelled: <b>{service}</b> with {staff_name} on {when} — {customer}."
    if job_type == JobType.BUSINESS_RESCHEDULE:
        previous = payload.get("previous_starts_at")
        previous_str = f" (was {previous})" if previous else ""
        return f"Rescheduled: <b>{service}</b> with {staff_name} now {when}{previous_str} — {customer}."
    raise ValueError(f"No business-facing booking template for job_type={job_type!r}")


def render_daily_summary_message(ctx: dict, summary_date_str: str) -> str:
    revenue = ctx["revenue_minor_units"] / 100
    return (
        f"<b>{ctx['business_name']}</b> — daily summary for {summary_date_str}: "
        f"{ctx['booking_count']} booking(s), {revenue:.2f} {ctx['currency']} in confirmed/completed revenue."
    )
