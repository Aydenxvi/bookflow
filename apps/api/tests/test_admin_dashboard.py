"""Admin dashboard aggregate counts and revenue (spec section 8). Builds a
small set of bookings in different statuses through the real admin-bookings
endpoints (so the data is exactly what those endpoints would have produced
in practice), then checks the dashboard's math against it directly."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.models.enums import MembershipRole
from tests.factories import (
    auth_header,
    make_business,
    make_membership,
    make_service,
    make_staff,
    make_user,
)

pytestmark = pytest.mark.asyncio


def _future_iso(days: int) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).replace(microsecond=0).isoformat()


async def _create_booking(client, biz_id, owner, service, staff, days, name):
    resp = await client.post(
        f"/api/v1/admin/businesses/{biz_id}/bookings",
        headers=auth_header(owner),
        json={
            "service_id": str(service.id), "staff_id": str(staff.id),
            "starts_at": _future_iso(days), "customer_name": name,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _set_status(client, biz_id, owner, booking_id, status_value):
    resp = await client.post(
        f"/api/v1/admin/businesses/{biz_id}/bookings/{booking_id}/status",
        headers=auth_header(owner),
        json={"status": status_value},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_dashboard_counts_and_revenue(client, db):
    biz = await make_business(db, slug="dash-biz", currency="USD")
    owner = await make_user(db, first_name="Owner")
    await make_membership(db, biz, owner, role=MembershipRole.BUSINESS_OWNER)
    service_popular = await make_service(db, biz, name="Popular Cut", price_minor_units=2000, currency="USD")
    service_rare = await make_service(db, biz, name="Rare Treatment", price_minor_units=5000, currency="USD")
    staff_busy = await make_staff(db, biz, display_name="Busy Staff")
    staff_idle = await make_staff(db, biz, display_name="Idle Staff")
    await db.commit()

    # Two completed bookings for the popular service/busy staff -> revenue + popularity.
    b1 = await _create_booking(client, biz.id, owner, service_popular, staff_busy, 1, "C1")
    await _set_status(client, biz.id, owner, b1, "completed")
    b2 = await _create_booking(client, biz.id, owner, service_popular, staff_busy, 2, "C2")
    await _set_status(client, biz.id, owner, b2, "completed")

    # One completed booking for the rare service/idle staff.
    b3 = await _create_booking(client, biz.id, owner, service_rare, staff_idle, 3, "C3")
    await _set_status(client, biz.id, owner, b3, "completed")

    # One cancelled booking — must not count toward revenue or completed_count.
    b4 = await _create_booking(client, biz.id, owner, service_popular, staff_busy, 4, "Cancelled")
    await _set_status(client, biz.id, owner, b4, "cancelled")

    # One still-upcoming confirmed booking.
    await _create_booking(client, biz.id, owner, service_popular, staff_idle, 5, "Upcoming")

    resp = await client.get(f"/api/v1/admin/businesses/{biz.id}/dashboard", headers=auth_header(owner))
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["completed_count"] == 3
    assert body["cancelled_count"] == 1
    assert body["upcoming_count"] == 1  # only the still-confirmed one, not completed/cancelled
    assert body["revenue_minor_units"] == 2000 + 2000 + 5000
    assert body["revenue_currency"] == "USD"

    popular_by_name = {p["name"]: p["count"] for p in body["popular_services"]}
    # "Popular Cut" has 3 non-cancelled bookings (2 completed + 1 upcoming); the
    # cancelled one is excluded by the dashboard's own query.
    assert popular_by_name["Popular Cut"] == 3
    assert popular_by_name["Rare Treatment"] == 1

    workload_by_name = {w["display_name"]: w["count"] for w in body["staff_workload"]}
    # Workload only counts active (pending/confirmed) bookings, not completed —
    # so Busy Staff's two completed bookings don't show up here, only idle
    # staff's one still-upcoming booking does.
    assert workload_by_name.get("Idle Staff") == 1
    assert "Busy Staff" not in workload_by_name


async def test_manager_cannot_be_locked_out_of_dashboard(client, db):
    biz = await make_business(db, slug="dash-biz-2")
    manager = await make_user(db, first_name="Manager")
    await make_membership(db, biz, manager, role=MembershipRole.BUSINESS_MANAGER)
    await db.commit()

    resp = await client.get(f"/api/v1/admin/businesses/{biz.id}/dashboard", headers=auth_header(manager))
    assert resp.status_code == 200
    assert resp.json()["today_count"] == 0


async def test_staff_role_cannot_view_dashboard(client, db):
    biz = await make_business(db, slug="dash-biz-3")
    staff_user = await make_user(db, first_name="Staff")
    await make_membership(db, biz, staff_user, role=MembershipRole.STAFF)
    await db.commit()

    resp = await client.get(f"/api/v1/admin/businesses/{biz.id}/dashboard", headers=auth_header(staff_user))
    assert resp.status_code == 403
