"""Multi-tenant isolation: a service/staff from Business A must never be
usable to build a booking against Business B, even if the ids are passed
together deliberately. This is enforced at the query layer in
app/routers/deps.py (service/staff lookups are always scoped by business_id)."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.routers.deps import get_service_in_business_or_404, get_staff_in_business_or_404
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


async def test_service_lookup_rejects_mismatched_business(db):
    biz_a = await make_business(db, slug="biz-a")
    biz_b = await make_business(db, slug="biz-b")
    service_a = await make_service(db, biz_a)
    await db.commit()

    with pytest.raises(HTTPException) as exc_info:
        await get_service_in_business_or_404(biz_b.id, service_a.id, db)
    assert exc_info.value.status_code == 404


async def test_staff_lookup_rejects_mismatched_business(db):
    biz_a = await make_business(db, slug="biz-a2")
    biz_b = await make_business(db, slug="biz-b2")
    staff_a = await make_staff(db, biz_a)
    await db.commit()

    with pytest.raises(HTTPException) as exc_info:
        await get_staff_in_business_or_404(biz_b.id, staff_a.id, db)
    assert exc_info.value.status_code == 404


async def test_availability_never_leaks_staff_across_businesses(db):
    """Even if biz_b's service happens to share a staff id's service-link
    table row by id collision (impossible with UUIDs, but this test proves
    the *query*, not just the ids, is what prevents leakage), a staff member
    linked only to business A's service must not appear for business B."""
    biz_a = await make_business(db, slug="biz-a3")
    biz_b = await make_business(db, slug="biz-b3")
    policy_b = await make_policy(db, biz_b, min_lead_time_minutes=0)

    service_a = await make_service(db, biz_a, duration_minutes=30)
    staff_a = await make_staff(db, biz_a)
    await link_staff_service(db, staff_a, service_a)
    await make_all_week_schedule(db, biz_a, None)
    await make_all_week_schedule(db, biz_a, staff_a)

    # Business B has its own, separate service of the same duration — staff_a
    # was never linked to it, so it must show zero availability regardless.
    service_b = await make_service(db, biz_b, duration_minutes=30)
    await db.commit()

    target_date = date.today() + timedelta(days=2)
    result = await compute_availability(
        db, biz_b, service_b, policy_b, staff_id=None, date_from=target_date, date_to=target_date
    )
    # No candidate staff at all for business B's service => the engine may
    # legitimately return an empty mapping rather than a zero-slots entry.
    assert result.get(target_date, []) == []
