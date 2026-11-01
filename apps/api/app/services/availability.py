"""The booking availability engine (spec section 11 — "CRITICAL").

Computes real, bookable time slots for a (business, service, staff|any,
date range) combination, taking into account:

- business operating hours and staff working hours (intersected — staff can
  never be bookable outside business hours),
- staff breaks (recurring, from WorkingScheduleBreak) and one-off exceptions
  (ScheduleException: leave/break/holiday/closure, business-wide or per-staff),
- existing bookings (expanded by the business's buffer_minutes on each side),
- the service's duration,
- the business's configurable slot interval, minimum lead time, and maximum
  advance-booking window,
- the business's IANA timezone, DST-safe (all local-time arithmetic goes
  through `zoneinfo`; nothing assumes a fixed UTC offset).

This module only *computes* availability. Booking creation re-validates
immediately before insert (see services/booking.py) — this module is the
source of truth for "what can I show the customer", not the last line of
defense against a race.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking
from app.models.business import Business
from app.models.enums import BookingStatus
from app.models.policy import BookingPolicy
from app.models.schedule import ScheduleException, WorkingSchedule
from app.models.service import Service, StaffService
from app.models.staff import Staff

ACTIVE_BOOKING_STATUSES = (BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.COMPLETED)


@dataclass(frozen=True)
class Interval:
    """A half-open [start, end) interval in UTC."""

    start: datetime
    end: datetime

    def overlaps(self, other: Interval) -> bool:
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class Slot:
    staff_id: uuid.UUID
    starts_at: datetime  # UTC
    ends_at: datetime  # UTC


class AvailabilityError(Exception):
    pass


async def get_candidate_staff(
    db: AsyncSession, business_id: uuid.UUID, service_id: uuid.UUID, staff_id: uuid.UUID | None
) -> list[Staff]:
    """Staff who are active and offer this service. If staff_id is given,
    returns that one staff member (still validated for business+service+active)."""
    stmt = (
        select(Staff)
        .join(StaffService, StaffService.staff_id == Staff.id)
        .where(
            Staff.business_id == business_id,
            Staff.is_active.is_(True),
            StaffService.service_id == service_id,
        )
    )
    if staff_id is not None:
        stmt = stmt.where(Staff.id == staff_id)
    result = await db.execute(stmt.distinct())
    return list(result.scalars().all())


def _local_shift_windows(
    schedules: list[WorkingSchedule], weekday: int
) -> list[tuple[time, time, list[tuple[time, time]]]]:
    """Returns (start, end, breaks) tuples for every schedule row matching this weekday."""
    out = []
    for s in schedules:
        if s.weekday == weekday:
            breaks = [(b.start_time, b.end_time) for b in s.breaks]
            out.append((s.start_time, s.end_time, breaks))
    return out


def _combine_local(d: date, t: time, tz: ZoneInfo) -> datetime:
    return datetime.combine(d, t, tzinfo=tz)


def _intersect_business_and_staff_windows(
    business_windows: list[tuple[time, time]],
    staff_windows: list[tuple[time, time]],
) -> list[tuple[time, time]]:
    """A staff member is only bookable where their own hours AND the
    business's operating hours both say yes."""
    if not business_windows:
        # No business-hours rows configured at all => treat as "open", don't
        # artificially block staff who do have hours configured. (A business
        # that wants to restrict hours should configure WorkingSchedule rows
        # with staff_id IS NULL; an empty config is treated permissively
        # rather than accidentally closing the business every day.)
        return staff_windows
    out: list[tuple[time, time]] = []
    for bs, be in business_windows:
        for ss, se in staff_windows:
            start = max(bs, ss)
            end = min(be, se)
            if start < end:
                out.append((start, end))
    return out


def _subtract_interval(
    windows: list[tuple[time, time]], cut_start: time, cut_end: time
) -> list[tuple[time, time]]:
    out: list[tuple[time, time]] = []
    for ws, we in windows:
        if cut_end <= ws or cut_start >= we:
            out.append((ws, we))
            continue
        if cut_start > ws:
            out.append((ws, cut_start))
        if cut_end < we:
            out.append((cut_end, we))
    return out


async def _load_schedule_data(
    db: AsyncSession, business_id: uuid.UUID, staff_ids: list[uuid.UUID]
) -> tuple[list[WorkingSchedule], dict[uuid.UUID, list[WorkingSchedule]], list[ScheduleException]]:
    ws_result = await db.execute(
        select(WorkingSchedule)
        .where(WorkingSchedule.business_id == business_id)
        .options(selectinload(WorkingSchedule.breaks))
    )
    all_schedules = list(ws_result.scalars().unique().all())
    business_schedules = [s for s in all_schedules if s.staff_id is None]
    staff_schedules: dict[uuid.UUID, list[WorkingSchedule]] = {sid: [] for sid in staff_ids}
    for s in all_schedules:
        if s.staff_id in staff_schedules:
            staff_schedules[s.staff_id].append(s)

    exc_result = await db.execute(
        select(ScheduleException).where(ScheduleException.business_id == business_id)
    )
    exceptions = list(exc_result.scalars().all())
    return business_schedules, staff_schedules, exceptions


async def _load_busy_intervals(
    db: AsyncSession, staff_ids: list[uuid.UUID], day_start_utc: datetime, day_end_utc: datetime
) -> dict[uuid.UUID, list[Interval]]:
    if not staff_ids:
        return {}
    result = await db.execute(
        select(Booking).where(
            Booking.staff_id.in_(staff_ids),
            Booking.status.in_(ACTIVE_BOOKING_STATUSES),
            Booking.starts_at < day_end_utc,
            Booking.ends_at > day_start_utc,
        )
    )
    busy: dict[uuid.UUID, list[Interval]] = {sid: [] for sid in staff_ids}
    for booking in result.scalars().all():
        busy[booking.staff_id].append(Interval(booking.starts_at, booking.ends_at))
    return busy


async def compute_availability(
    db: AsyncSession,
    business: Business,
    service: Service,
    policy: BookingPolicy,
    staff_id: uuid.UUID | None,
    date_from: date,
    date_to: date,
) -> dict[date, list[Slot]]:
    if date_from > date_to:
        raise AvailabilityError("date_from must be <= date_to")

    tz = ZoneInfo(business.timezone)
    now_utc = datetime.now(UTC)
    earliest_bookable_utc = now_utc + timedelta(minutes=policy.min_lead_time_minutes)
    latest_bookable_date = (now_utc.astimezone(tz)).date() + timedelta(days=policy.max_advance_days)

    candidates = await get_candidate_staff(db, business.id, service.id, staff_id)
    if not candidates:
        return {}
    staff_ids = [s.id for s in candidates]

    business_schedules, staff_schedules_by_id, exceptions = await _load_schedule_data(
        db, business.id, staff_ids
    )

    results: dict[date, list[Slot]] = {}

    current = date_from
    while current <= date_to:
        results[current] = []
        # A spring-forward DST transition can make two distinct *nominal*
        # local slot times (e.g. 02:00 and 03:00, either side of a gap like
        # Europe's 02:00->03:00 jump) resolve to the exact same real UTC
        # instant. Without this, the engine would offer the same bookable
        # moment to the customer twice on transition day.
        seen_instants: set[tuple[uuid.UUID, datetime]] = set()
        if current > latest_bookable_date:
            current += timedelta(days=1)
            continue

        weekday = current.weekday()  # Monday=0 .. Sunday=6, matches our stored convention

        day_business_windows = [(s, e) for (s, e, _) in _local_shift_windows(business_schedules, weekday)]

        # Business-wide exceptions (holiday/closure) for this date.
        business_day_exceptions = [
            e for e in exceptions if e.staff_id is None and e.date == current
        ]
        for exc in business_day_exceptions:
            if exc.start_time is None and exc.end_time is None:
                day_business_windows = []  # whole business closed
            else:
                day_business_windows = _subtract_interval(
                    day_business_windows, exc.start_time, exc.end_time
                )

        if not day_business_windows and business_schedules:
            # Business has hours configured for other weekdays but none (or
            # none left after exceptions) for this one => closed today.
            current += timedelta(days=1)
            continue

        day_start_local = _combine_local(current, time.min, tz)
        day_end_local = _combine_local(current, time.max, tz) + timedelta(microseconds=1)

        day_start_utc = day_start_local.astimezone(UTC)
        day_end_utc = day_end_local.astimezone(UTC)
        busy_by_staff = await _load_busy_intervals(db, staff_ids, day_start_utc, day_end_utc)

        for staff in candidates:
            staff_shifts = _local_shift_windows(staff_schedules_by_id.get(staff.id, []), weekday)
            if not staff_shifts:
                continue  # staff doesn't work this weekday at all

            busy = busy_by_staff.get(staff.id, [])
            buffered_busy = [
                Interval(
                    b.start - timedelta(minutes=policy.buffer_minutes),
                    b.end + timedelta(minutes=policy.buffer_minutes),
                )
                for b in busy
            ]

            for shift_start, shift_end, breaks in staff_shifts:
                windows = _intersect_business_and_staff_windows(
                    day_business_windows, [(shift_start, shift_end)]
                )
                for bs, be in breaks:
                    windows = _subtract_interval(windows, bs, be)

                staff_day_exceptions = [
                    e for e in exceptions if e.staff_id == staff.id and e.date == current
                ]
                for exc in staff_day_exceptions:
                    if exc.start_time is None and exc.end_time is None:
                        windows = []
                    else:
                        windows = _subtract_interval(windows, exc.start_time, exc.end_time)

                if not windows:
                    continue

                for ws, we in windows:
                    window_start_local = _combine_local(current, ws, tz)
                    window_end_local = _combine_local(current, we, tz)

                    slot_start_local = window_start_local
                    step = timedelta(minutes=policy.slot_interval_minutes)
                    duration = timedelta(minutes=service.duration_minutes)

                    while slot_start_local + duration <= window_end_local:
                        slot_start_utc = slot_start_local.astimezone(UTC)
                        slot_end_utc = slot_start_utc + duration
                        candidate_interval = Interval(slot_start_utc, slot_end_utc)

                        instant_key = (staff.id, slot_start_utc)
                        if (
                            slot_start_utc >= earliest_bookable_utc
                            and instant_key not in seen_instants
                            and not any(candidate_interval.overlaps(b) for b in buffered_busy)
                        ):
                            seen_instants.add(instant_key)
                            results[current].append(
                                Slot(staff_id=staff.id, starts_at=slot_start_utc, ends_at=slot_end_utc)
                            )

                        slot_start_local += step

        results[current].sort(key=lambda s: (s.starts_at, str(s.staff_id)))
        current += timedelta(days=1)

    return results
