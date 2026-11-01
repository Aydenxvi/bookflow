"""Admin appointment calendar, manual booking creation, and status changes
(spec section 8) — including the staff-can-only-touch-their-own-bookings
visibility/authorization rule, which is the one piece of real business logic
in this router beyond plain role gating."""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

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


async def _setup(db):
    biz = await make_business(db, slug="booking-biz")
    owner = await make_user(db, first_name="Owner")
    await make_membership(db, biz, owner, role=MembershipRole.BUSINESS_OWNER)
    service = await make_service(db, biz, duration_minutes=30)
    staff = await make_staff(db, biz, display_name="Staff One")
    await db.commit()
    return biz, owner, service, staff


def _future_iso(days: int = 2) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).replace(microsecond=0).isoformat()


async def test_create_manual_booking_as_owner(client, db):
    biz, owner, service, staff = await _setup(db)

    resp = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(owner),
        json={
            "service_id": str(service.id),
            "staff_id": str(staff.id),
            "starts_at": _future_iso(),
            "customer_name": "Walk-in Sam",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["service"]["id"] == str(service.id)
    assert body["staff"]["id"] == str(staff.id)
    assert body["customer"]["display_name"] == "Walk-in Sam"
    assert body["status"] == "confirmed"  # default policy is AUTOMATIC confirmation


async def test_staff_role_cannot_create_manual_booking(client, db):
    biz, _owner, service, staff = await _setup(db)
    staff_user = await make_user(db, first_name="Just Staff")
    await make_membership(db, biz, staff_user, role=MembershipRole.STAFF)
    await db.commit()

    resp = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(staff_user),
        json={
            "service_id": str(service.id),
            "staff_id": str(staff.id),
            "starts_at": _future_iso(),
            "customer_name": "Nope",
        },
    )
    assert resp.status_code == 403


async def test_overlapping_manual_booking_conflicts(client, db):
    biz, owner, service, staff = await _setup(db)
    starts_at = _future_iso()

    first = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(owner),
        json={"service_id": str(service.id), "staff_id": str(staff.id), "starts_at": starts_at, "customer_name": "A"},
    )
    assert first.status_code == 201

    second = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(owner),
        json={"service_id": str(service.id), "staff_id": str(staff.id), "starts_at": starts_at, "customer_name": "B"},
    )
    assert second.status_code == 409


async def test_calendar_filters_by_date_range(client, db):
    biz, owner, service, staff = await _setup(db)
    await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(owner),
        json={
            "service_id": str(service.id), "staff_id": str(staff.id),
            "starts_at": _future_iso(2), "customer_name": "Soon",
        },
    )

    today = date.today()
    in_range = await client.get(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(owner),
        params={"date_from": today.isoformat(), "date_to": (today + timedelta(days=5)).isoformat()},
    )
    assert in_range.status_code == 200
    assert len(in_range.json()) == 1

    out_of_range = await client.get(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(owner),
        params={
            "date_from": (today + timedelta(days=30)).isoformat(),
            "date_to": (today + timedelta(days=35)).isoformat(),
        },
    )
    assert out_of_range.status_code == 200
    assert out_of_range.json() == []


async def test_calendar_range_over_92_days_rejected(client, db):
    biz, owner, _service, _staff = await _setup(db)
    today = date.today()

    resp = await client.get(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(owner),
        params={"date_from": today.isoformat(), "date_to": (today + timedelta(days=200)).isoformat()},
    )
    assert resp.status_code == 400


async def test_staff_sees_only_their_own_bookings(client, db):
    biz, owner, service, staff_a = await _setup(db)
    staff_b = await make_staff(db, biz, display_name="Staff Two")
    staff_a_user = await make_user(db, first_name="Staff A User")
    await make_membership(db, biz, staff_a_user, role=MembershipRole.STAFF)
    staff_a.user_id = staff_a_user.id
    await db.commit()

    today = date.today()
    await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(owner),
        json={"service_id": str(service.id), "staff_id": str(staff_a.id), "starts_at": _future_iso(1), "customer_name": "For A"},
    )
    await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(owner),
        json={"service_id": str(service.id), "staff_id": str(staff_b.id), "starts_at": _future_iso(1), "customer_name": "For B"},
    )

    resp = await client.get(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(staff_a_user),
        params={"date_from": today.isoformat(), "date_to": (today + timedelta(days=5)).isoformat()},
    )
    assert resp.status_code == 200
    bookings = resp.json()
    assert len(bookings) == 1
    assert bookings[0]["staff"]["id"] == str(staff_a.id)


async def test_staff_cannot_change_status_of_anothers_booking(client, db):
    biz, owner, service, staff_a = await _setup(db)
    staff_b = await make_staff(db, biz, display_name="Staff Two")
    staff_a_user = await make_user(db, first_name="Staff A User")
    await make_membership(db, biz, staff_a_user, role=MembershipRole.STAFF)
    staff_a.user_id = staff_a_user.id
    await db.commit()

    created = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(owner),
        json={"service_id": str(service.id), "staff_id": str(staff_b.id), "starts_at": _future_iso(1), "customer_name": "For B"},
    )
    booking_id = created.json()["id"]

    resp = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings/{booking_id}/status",
        headers=auth_header(staff_a_user),
        json={"status": "completed"},
    )
    assert resp.status_code == 403


async def test_staff_can_change_status_of_own_booking(client, db):
    biz, owner, service, staff_a = await _setup(db)
    staff_a_user = await make_user(db, first_name="Staff A User")
    await make_membership(db, biz, staff_a_user, role=MembershipRole.STAFF)
    staff_a.user_id = staff_a_user.id
    await db.commit()

    created = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(owner),
        json={"service_id": str(service.id), "staff_id": str(staff_a.id), "starts_at": _future_iso(1), "customer_name": "For A"},
    )
    booking_id = created.json()["id"]
    assert created.json()["status"] == "confirmed"

    resp = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings/{booking_id}/status",
        headers=auth_header(staff_a_user),
        json={"status": "completed"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


async def test_invalid_status_transition_rejected(client, db):
    biz, owner, service, staff = await _setup(db)
    created = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(owner),
        json={"service_id": str(service.id), "staff_id": str(staff.id), "starts_at": _future_iso(1), "customer_name": "X"},
    )
    booking_id = created.json()["id"]

    completed = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings/{booking_id}/status",
        headers=auth_header(owner),
        json={"status": "completed"},
    )
    assert completed.status_code == 200

    # completed -> confirmed is not a valid transition
    resp = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings/{booking_id}/status",
        headers=auth_header(owner),
        json={"status": "confirmed"},
    )
    assert resp.status_code == 400


async def test_cancel_via_status_endpoint_bypasses_cancellation_window(client, db):
    biz, owner, service, staff = await _setup(db)
    # Deliberately close to "now" — a customer-initiated cancel would be
    # blocked by the policy's cancellation window, but a staff/owner
    # override via this endpoint should not be.
    created = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(owner),
        json={
            "service_id": str(service.id), "staff_id": str(staff.id),
            "starts_at": _future_iso(1), "customer_name": "X",
        },
    )
    booking_id = created.json()["id"]

    resp = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings/{booking_id}/status",
        headers=auth_header(owner),
        json={"status": "cancelled", "note": "Owner override"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


async def test_status_history_records_creation_and_transitions(client, db):
    biz, owner, service, staff = await _setup(db)
    created = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(owner),
        json={
            "service_id": str(service.id), "staff_id": str(staff.id),
            "starts_at": _future_iso(2), "customer_name": "History Test",
        },
    )
    booking_id = created.json()["id"]

    await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings/{booking_id}/status",
        headers=auth_header(owner),
        json={"status": "cancelled", "note": "changed my mind"},
    )

    resp = await client.get(
        f"/api/v1/admin/businesses/{biz.id}/bookings/{booking_id}/history",
        headers=auth_header(owner),
    )
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) == 2
    assert entries[0]["from_status"] is None
    assert entries[0]["to_status"] == "confirmed"
    assert entries[1]["from_status"] == "confirmed"
    assert entries[1]["to_status"] == "cancelled"
    assert entries[1]["note"] == "changed my mind"
    assert entries[1]["changed_by_name"] == "Owner"


async def test_staff_cannot_view_history_of_another_staffs_booking(client, db):
    biz, owner, service, staff = await _setup(db)
    other_staff_user = await make_user(db, first_name="Other Staff")
    await make_membership(db, biz, other_staff_user, role=MembershipRole.STAFF)
    await db.commit()

    created = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/bookings",
        headers=auth_header(owner),
        json={
            "service_id": str(service.id), "staff_id": str(staff.id),
            "starts_at": _future_iso(2), "customer_name": "X",
        },
    )
    booking_id = created.json()["id"]

    resp = await client.get(
        f"/api/v1/admin/businesses/{biz.id}/bookings/{booking_id}/history",
        headers=auth_header(other_staff_user),
    )
    assert resp.status_code == 403
