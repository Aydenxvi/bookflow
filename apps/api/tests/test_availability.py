"""Tests the availability engine: real slot generation, business+staff hours
intersection, breaks/exceptions, lead time, and DST correctness."""
from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.models.enums import ScheduleExceptionType
from app.models.schedule import ScheduleException, WorkingSchedule, WorkingScheduleBreak
from app.services.availability import compute_availability
from tests.factories import (
    link_staff_service,
    make_all_week_schedule,
    make_business,
    make_policy,
    make_service,
    make_staff,
)

pytestmark = pytest.mark.asyncio


async def test_slots_respect_business_and_staff_hours_intersection(db):
    business = await make_business(db)
    policy = await make_policy(db, business, min_lead_time_minutes=0)
    service = await make_service(db, business, duration_minutes=30)
    staff = await make_staff(db, business)
    await link_staff_service(db, staff, service)

    # Business open 09:00-18:00, but staff only works 09:00-11:00 that day.
    await make_all_week_schedule(db, business, None, start=time(9, 0), end=time(18, 0))
    for weekday in range(7):
        db.add(
            WorkingSchedule(
                business_id=business.id, staff_id=staff.id, weekday=weekday,
                start_time=time(9, 0), end_time=time(11, 0),
            )
        )
    await db.flush()
    await db.commit()

    target_date = date.today() + timedelta(days=2)
    result = await compute_availability(
        db, business, service, policy, staff_id=None, date_from=target_date, date_to=target_date
    )
    slots = result[target_date]
    assert slots, "expected some slots"
    tz = ZoneInfo(business.timezone)
    for slot in slots:
        local_start = slot.starts_at.astimezone(tz).time()
        local_end = slot.ends_at.astimezone(tz).time()
        assert local_start >= time(9, 0)
        assert local_end <= time(11, 0)


async def test_breaks_remove_slots(db):
    business = await make_business(db)
    policy = await make_policy(db, business, min_lead_time_minutes=0, slot_interval_minutes=30)
    service = await make_service(db, business, duration_minutes=30)
    staff = await make_staff(db, business)
    await link_staff_service(db, staff, service)
    await make_all_week_schedule(db, business, None, start=time(9, 0), end=time(12, 0))

    target_date = date.today() + timedelta(days=2)
    for weekday in range(7):
        ws = WorkingSchedule(
            business_id=business.id, staff_id=staff.id, weekday=weekday,
            start_time=time(9, 0), end_time=time(12, 0),
        )
        db.add(ws)
        await db.flush()
        db.add(WorkingScheduleBreak(working_schedule_id=ws.id, start_time=time(10, 0), end_time=time(10, 30)))
    await db.commit()

    result = await compute_availability(
        db, business, service, policy, staff_id=staff.id, date_from=target_date, date_to=target_date
    )
    tz = ZoneInfo(business.timezone)
    local_starts = {s.starts_at.astimezone(tz).time() for s in result[target_date]}
    assert time(10, 0) not in local_starts  # break removed this slot
    assert time(9, 0) in local_starts


async def test_schedule_exception_closes_whole_day(db):
    business = await make_business(db)
    policy = await make_policy(db, business, min_lead_time_minutes=0)
    service = await make_service(db, business, duration_minutes=30)
    staff = await make_staff(db, business)
    await link_staff_service(db, staff, service)
    await make_all_week_schedule(db, business, None)
    await make_all_week_schedule(db, business, staff)

    target_date = date.today() + timedelta(days=2)
    db.add(
        ScheduleException(
            business_id=business.id, staff_id=staff.id, date=target_date,
            start_time=None, end_time=None, type=ScheduleExceptionType.LEAVE, note="On leave",
        )
    )
    await db.commit()

    result = await compute_availability(
        db, business, service, policy, staff_id=staff.id, date_from=target_date, date_to=target_date
    )
    assert result[target_date] == []


async def test_min_lead_time_excludes_near_term_slots(db):
    business = await make_business(db)
    policy = await make_policy(db, business, min_lead_time_minutes=24 * 60)  # 24h lead time
    service = await make_service(db, business, duration_minutes=30)
    staff = await make_staff(db, business)
    await link_staff_service(db, staff, service)
    await make_all_week_schedule(db, business, None)
    await make_all_week_schedule(db, business, staff)
    await db.commit()

    today = date.today()
    result = await compute_availability(
        db, business, service, policy, staff_id=staff.id, date_from=today, date_to=today
    )
    # With a 24h lead time, today should have no bookable slots left (any
    # slot earlier today or in the very near future is excluded).
    now_utc = datetime.now(UTC)
    for slot in result[today]:
        assert slot.starts_at >= now_utc + timedelta(hours=24) - timedelta(minutes=1)


async def test_dst_spring_forward_handled_correctly(db):
    """Europe/Istanbul no longer observes DST (fixed UTC+3 since 2016), so use
    a timezone that still does — Europe/Berlin — to prove slot generation
    stays correct across a spring-forward transition (02:00 -> 03:00)."""
    business = await make_business(db, timezone="Europe/Berlin", slug="dst-biz")
    # max_advance_days is generous here because this test needs a *fixed,
    # known* DST-transition date rather than one computed relative to
    # "today" (whose distance from the next transition varies depending on
    # when the suite runs); the booking-window policy itself is covered by
    # test_min_lead_time_excludes_near_term_slots instead.
    policy = await make_policy(db, business, min_lead_time_minutes=0, slot_interval_minutes=60, max_advance_days=400)
    service = await make_service(db, business, duration_minutes=60)
    staff = await make_staff(db, business)
    await link_staff_service(db, staff, service)
    await make_all_week_schedule(db, business, None, start=time(1, 0), end=time(6, 0))
    await make_all_week_schedule(db, business, staff, start=time(1, 0), end=time(6, 0))
    await db.commit()

    # EU spring-forward is the last Sunday of March; use the next upcoming
    # one as a fixed, known date so the test doesn't depend on "today".
    dst_date = date(2027, 3, 28)
    result = await compute_availability(
        db, business, service, policy, staff_id=staff.id, date_from=dst_date, date_to=dst_date
    )
    slots = result[dst_date]
    assert slots, "expected slots even across the DST transition"

    # No two slots should represent the exact same real UTC instant. On a
    # spring-forward day, two *nominal* local times either side of the gap
    # (e.g. 02:00 and 03:00) can resolve to the same real instant — the
    # engine must deduplicate that, never offer the same bookable moment
    # twice.
    starts_utc = [s.starts_at for s in slots]
    assert len(set(starts_utc)) == len(starts_utc)

    # And every slot's local wall-clock start must fall within the
    # configured window, proving the UTC offset shift was applied correctly
    # (a naive "always add a fixed offset" bug would push some slots outside
    # 01:00-06:00 local once the UTC offset itself changes mid-window).
    tz = ZoneInfo("Europe/Berlin")
    for s in slots:
        local_t = s.starts_at.astimezone(tz).time()
        assert time(1, 0) <= local_t < time(6, 0)

    # The transition itself must actually be exercised by this window,
    # otherwise the test would pass trivially without ever having tested a
    # gap: before 02:00 local is UTC+1, from 03:00 local onward is UTC+2.
    offsets = {s.starts_at.astimezone(tz).utcoffset() for s in slots}
    assert len(offsets) == 2, f"expected slots on both sides of the UTC offset change, got {offsets}"
