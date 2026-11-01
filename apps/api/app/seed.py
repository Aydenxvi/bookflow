"""Seed script: ATELIER — Modern Grooming Studio demo business (spec section 19).

Run with: python -m app.seed
Safe to re-run: it's idempotent on the business slug (deletes and recreates
that business's data rather than duplicating it).
"""
from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.booking import Booking
from app.models.business import Business, BusinessSettings
from app.models.enums import BookingConfirmationMode, BookingStatus, ScheduleExceptionType
from app.models.policy import BookingPolicy
from app.models.service import Service, StaffService
from app.models.staff import Staff
from app.models.user import User

DEMO_SLUG = "atelier"


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(Business).where(Business.slug == DEMO_SLUG))
        business = existing.scalar_one_or_none()
        if business is not None:
            print(f"Removing existing demo business '{DEMO_SLUG}' to reseed cleanly...")
            await db.delete(business)
            await db.commit()

        business = Business(
            slug=DEMO_SLUG,
            name="ATELIER — Modern Grooming Studio",
            description=(
                "A contemporary grooming studio for the modern gentleman — precision cuts, "
                "traditional hot-towel shaves, and beard sculpting in a calm, editorial space."
            ),
            logo_url=None,
            cover_image_url=None,
            address="14 Istiklal Caddesi, Beyoğlu, Istanbul",
            contact_phone="+90 212 555 0134",
            contact_email="hello@atelier.demo",
            timezone="Europe/Istanbul",
            currency="USD",
            is_active=True,
            is_demo=True,
        )
        db.add(business)
        await db.flush()

        db.add(
            BusinessSettings(
                business_id=business.id,
                primary_language="en",
                supported_languages=["en", "ru", "tr"],
                brand_color="#4B5D44",  # muted sage
                notify_business_on_new_booking=True,
                notify_business_on_cancellation=True,
                notify_business_daily_summary=True,
            )
        )
        db.add(
            BookingPolicy(
                business_id=business.id,
                confirmation_mode=BookingConfirmationMode.AUTOMATIC,
                slot_interval_minutes=15,
                buffer_minutes=5,
                min_lead_time_minutes=60,
                max_advance_days=30,
                cancellation_window_minutes=120,
                reschedule_window_minutes=120,
                reminder_offsets_minutes=[1440, 120, 30],
            )
        )

        # --- Business operating hours: Mon-Sat 09:00-19:00, closed Sunday ---
        from app.models.schedule import ScheduleException, WorkingSchedule, WorkingScheduleBreak

        for weekday in range(6):  # Monday(0) .. Saturday(5)
            db.add(
                WorkingSchedule(
                    business_id=business.id,
                    staff_id=None,
                    weekday=weekday,
                    start_time=time(9, 0),
                    end_time=time(19, 0),
                )
            )

        # --- Services ---
        services_data = [
            ("Classic Haircut", "Precision scissor or clipper cut, tailored to face shape.", "Hair", 30, 2500),
            ("Beard Sculpt", "Shape and define with straight-razor detailing.", "Beard", 20, 1800),
            ("Hot Towel Shave", "Traditional straight-razor shave with hot towel prep.", "Shave", 40, 3200),
            ("Haircut + Beard Combo", "Full haircut paired with a beard sculpt.", "Combo", 50, 4000),
            ("Kids Haircut", "A patient, quick cut for the younger gentlemen.", "Hair", 20, 1800),
            ("Scalp & Hair Treatment", "Deep-cleansing scalp massage and conditioning treatment.", "Treatment", 35, 3000),
        ]
        services: list[Service] = []
        for name, desc, category, duration, price in services_data:
            s = Service(
                business_id=business.id,
                name=name,
                description=desc,
                category=category,
                duration_minutes=duration,
                price_minor_units=price,
                currency="USD",
                is_active=True,
            )
            db.add(s)
            services.append(s)
        await db.flush()

        # --- Staff ---
        staff_data = [
            ("Eren Kaya", "Master Barber", "12 years sculpting classic and modern cuts across Istanbul's best studios."),
            ("Lara Demir", "Shave Specialist", "Trained in traditional hot-towel shaving technique; beard sculpting expert."),
            ("Mert Aydın", "Senior Barber", "Known for sharp fades and precise beard lines."),
        ]
        staff_members: list[Staff] = []
        for name, spec, bio in staff_data:
            st = Staff(
                business_id=business.id,
                display_name=name,
                specialization=spec,
                bio=bio,
                is_active=True,
            )
            db.add(st)
            staff_members.append(st)
        await db.flush()

        # Staff hours: same 09:00-19:00 Mon-Sat, with a 13:00-13:30 lunch break,
        # except Mert who works Tue-Sat (off Monday) and Lara who does shaves/beard only.
        for st in staff_members:
            days = range(6)
            if st.display_name == "Mert Aydın":
                days = range(1, 6)  # Tue-Sat
            for weekday in days:
                ws = WorkingSchedule(
                    business_id=business.id,
                    staff_id=st.id,
                    weekday=weekday,
                    start_time=time(9, 0),
                    end_time=time(19, 0),
                )
                db.add(ws)
                await db.flush()
                db.add(WorkingScheduleBreak(working_schedule_id=ws.id, start_time=time(13, 0), end_time=time(13, 30)))

        # Staff <-> service capability. Lara: shave/beard focus. Eren/Mert: everything but treatment is shared.
        service_by_name = {s.name: s for s in services}
        capability_map = {
            "Eren Kaya": ["Classic Haircut", "Beard Sculpt", "Hot Towel Shave", "Haircut + Beard Combo", "Kids Haircut"],
            "Lara Demir": ["Beard Sculpt", "Hot Towel Shave", "Scalp & Hair Treatment"],
            "Mert Aydın": ["Classic Haircut", "Beard Sculpt", "Haircut + Beard Combo", "Kids Haircut"],
        }
        for st in staff_members:
            for service_name in capability_map[st.display_name]:
                db.add(StaffService(staff_id=st.id, service_id=service_by_name[service_name].id))

        # A one-off holiday exception next month, business-wide (illustrates ScheduleException).
        next_month = date.today().replace(day=1) + timedelta(days=32)
        db.add(
            ScheduleException(
                business_id=business.id,
                staff_id=None,
                date=next_month.replace(day=1),
                start_time=None,
                end_time=None,
                type=ScheduleExceptionType.HOLIDAY,
                note="Studio closed for staff training day.",
            )
        )

        await db.flush()

        # --- A demo customer + a few historical bookings (completed/cancelled),
        # so "My Appointments" and the admin calendar have something to show. ---
        demo_customer = User(first_name="Alex", last_name="Demo", is_demo=True)
        db.add(demo_customer)
        await db.flush()

        now = datetime.now(UTC)
        past_completed_start = now - timedelta(days=10)
        completed_booking = Booking(
            business_id=business.id,
            staff_id=staff_members[0].id,
            service_id=service_by_name["Classic Haircut"].id,
            customer_user_id=demo_customer.id,
            starts_at=past_completed_start,
            ends_at=past_completed_start + timedelta(minutes=30),
            status=BookingStatus.COMPLETED,
            price_minor_units_snapshot=service_by_name["Classic Haircut"].price_minor_units,
            currency_snapshot="USD",
            duration_minutes_snapshot=30,
            is_demo=True,
        )
        db.add(completed_booking)

        past_cancelled_start = now - timedelta(days=5)
        cancelled_booking = Booking(
            business_id=business.id,
            staff_id=staff_members[1].id,
            service_id=service_by_name["Hot Towel Shave"].id,
            customer_user_id=demo_customer.id,
            starts_at=past_cancelled_start,
            ends_at=past_cancelled_start + timedelta(minutes=40),
            status=BookingStatus.CANCELLED,
            cancel_reason="Schedule conflict",
            price_minor_units_snapshot=service_by_name["Hot Towel Shave"].price_minor_units,
            currency_snapshot="USD",
            duration_minutes_snapshot=40,
            is_demo=True,
        )
        db.add(cancelled_booking)

        await db.commit()

        print(f"Seeded demo business '{business.name}' (slug={DEMO_SLUG}, id={business.id})")
        print(f"  {len(services)} services, {len(staff_members)} staff, 2 historical bookings.")


if __name__ == "__main__":
    asyncio.run(seed())
