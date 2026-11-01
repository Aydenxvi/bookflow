"""WorkingSchedule (+ breaks) and ScheduleException models.

WorkingSchedule rows are weekly-recurring. When `staff_id` is NULL the row
describes the *business's* operating hours for that weekday; when set it
describes that specific staff member's hours. The availability engine
intersects staff hours with business hours (a staff member can never be
bookable outside business operating hours even if their own schedule says
otherwise — see app/services/availability.py).

`start_time`/`end_time` are naive local times (no tz), always interpreted in
the owning Business's `timezone` field. This keeps "9am–5pm every Monday"
simple to store and correct across DST, since DST is resolved at the point
we combine a concrete date with these naive times (see availability.py).

ScheduleException covers one-off deviations: a holiday/closure for the whole
business (staff_id NULL) or leave/an extra break for one staff member
(staff_id set), optionally scoped to a sub-range of the day via
start_time/end_time (NULL+NULL means "all day").
"""
from __future__ import annotations

import uuid
from datetime import date as date_
from datetime import time as time_
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import ScheduleExceptionType
from app.models.mixins import TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.business import Business
    from app.models.staff import Staff


class WorkingSchedule(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "working_schedules"
    __table_args__ = (
        UniqueConstraint(
            "business_id", "staff_id", "weekday", "start_time", name="uq_schedule_business_staff_weekday_start"
        ),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    staff_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("staff.id", ondelete="CASCADE"), nullable=True, index=True
    )

    weekday: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday .. 6=Sunday (ISO)
    start_time: Mapped[time_] = mapped_column(Time, nullable=False)
    end_time: Mapped[time_] = mapped_column(Time, nullable=False)

    business: Mapped[Business] = relationship(back_populates="working_schedules")
    staff: Mapped[Staff | None] = relationship(back_populates="working_schedules")
    breaks: Mapped[list[WorkingScheduleBreak]] = relationship(
        back_populates="working_schedule", cascade="all, delete-orphan"
    )


class WorkingScheduleBreak(UUIDPkMixin, TimestampMixin, Base):
    """A recurring break (e.g. lunch) within a WorkingSchedule shift."""

    __tablename__ = "working_schedule_breaks"

    working_schedule_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("working_schedules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_time: Mapped[time_] = mapped_column(Time, nullable=False)
    end_time: Mapped[time_] = mapped_column(Time, nullable=False)

    working_schedule: Mapped[WorkingSchedule] = relationship(back_populates="breaks")


class ScheduleException(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "schedule_exceptions"

    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    staff_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("staff.id", ondelete="CASCADE"), nullable=True, index=True
    )

    date: Mapped[date_] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time_ | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time_ | None] = mapped_column(Time, nullable=True)
    type: Mapped[ScheduleExceptionType] = mapped_column(
        Enum(ScheduleExceptionType, native_enum=False, length=16), nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)

    business: Mapped[Business] = relationship(back_populates="schedule_exceptions")
    staff: Mapped[Staff | None] = relationship(back_populates="schedule_exceptions")
