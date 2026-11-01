"""Admin staff management (spec section 10): CRUD, service assignment,
weekly working-schedule editing, and schedule exceptions (leave/holiday)."""
from __future__ import annotations

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


async def _owner(db):
    biz = await make_business(db, slug="staff-biz")
    owner = await make_user(db, first_name="Owner")
    await make_membership(db, biz, owner, role=MembershipRole.BUSINESS_OWNER)
    await db.commit()
    return biz, owner


async def test_create_staff_with_services(client, db):
    biz, owner = await _owner(db)
    service = await make_service(db, biz)
    await db.commit()

    resp = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/staff",
        headers=auth_header(owner),
        json={"display_name": "Nail Tech", "service_ids": [str(service.id)]},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["display_name"] == "Nail Tech"
    assert body["service_ids"] == [str(service.id)]


async def test_update_staff_partial(client, db):
    biz, owner = await _owner(db)
    staff = await make_staff(db, biz, display_name="Old Name")
    await db.commit()

    resp = await client.patch(
        f"/api/v1/admin/businesses/{biz.id}/staff/{staff.id}",
        headers=auth_header(owner),
        json={"display_name": "New Name"},
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "New Name"


async def test_set_staff_services_replaces_links(client, db):
    biz, owner = await _owner(db)
    staff = await make_staff(db, biz)
    service_a = await make_service(db, biz, name="A")
    service_b = await make_service(db, biz, name="B")
    await db.commit()

    first = await client.put(
        f"/api/v1/admin/businesses/{biz.id}/staff/{staff.id}/services",
        headers=auth_header(owner),
        json={"service_ids": [str(service_a.id), str(service_b.id)]},
    )
    assert first.status_code == 200
    assert set(first.json()["service_ids"]) == {str(service_a.id), str(service_b.id)}

    second = await client.put(
        f"/api/v1/admin/businesses/{biz.id}/staff/{staff.id}/services",
        headers=auth_header(owner),
        json={"service_ids": [str(service_b.id)]},
    )
    assert second.status_code == 200
    assert second.json()["service_ids"] == [str(service_b.id)]


async def test_schedule_round_trip(client, db):
    biz, owner = await _owner(db)
    staff = await make_staff(db, biz)
    await db.commit()

    put_resp = await client.put(
        f"/api/v1/admin/businesses/{biz.id}/staff/{staff.id}/schedule",
        headers=auth_header(owner),
        json={
            "days": [
                {
                    "weekday": 1,
                    "start_time": "09:00",
                    "end_time": "17:00",
                    "breaks": [{"start_time": "12:00", "end_time": "13:00"}],
                }
            ]
        },
    )
    assert put_resp.status_code == 200, put_resp.text
    [day] = put_resp.json()
    assert day["weekday"] == 1
    assert day["start_time"] == "09:00"
    assert day["breaks"] == [{"start_time": "12:00", "end_time": "13:00"}]

    get_resp = await client.get(
        f"/api/v1/admin/businesses/{biz.id}/staff/{staff.id}/schedule", headers=auth_header(owner)
    )
    assert get_resp.status_code == 200
    assert get_resp.json() == put_resp.json()


async def test_schedule_replace_removes_old_days(client, db):
    biz, owner = await _owner(db)
    staff = await make_staff(db, biz)
    await db.commit()

    await client.put(
        f"/api/v1/admin/businesses/{biz.id}/staff/{staff.id}/schedule",
        headers=auth_header(owner),
        json={"days": [{"weekday": 0, "start_time": "09:00", "end_time": "17:00", "breaks": []}]},
    )
    second = await client.put(
        f"/api/v1/admin/businesses/{biz.id}/staff/{staff.id}/schedule",
        headers=auth_header(owner),
        json={"days": [{"weekday": 2, "start_time": "10:00", "end_time": "18:00", "breaks": []}]},
    )
    assert second.status_code == 200
    weekdays = {d["weekday"] for d in second.json()}
    assert weekdays == {2}  # Monday is gone, replaced entirely by Wednesday


async def test_staff_level_exception_create_list_delete(client, db):
    biz, owner = await _owner(db)
    staff = await make_staff(db, biz)
    await db.commit()

    create_resp = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/staff/exceptions",
        headers=auth_header(owner),
        json={"staff_id": str(staff.id), "date": "2026-12-25", "type": "holiday", "note": "Christmas"},
    )
    assert create_resp.status_code == 201, create_resp.text
    exception_id = create_resp.json()["id"]

    list_resp = await client.get(
        f"/api/v1/admin/businesses/{biz.id}/staff/exceptions", headers=auth_header(owner)
    )
    assert list_resp.status_code == 200
    assert [e["id"] for e in list_resp.json()] == [exception_id]

    delete_resp = await client.delete(
        f"/api/v1/admin/businesses/{biz.id}/staff/exceptions/{exception_id}", headers=auth_header(owner)
    )
    assert delete_resp.status_code == 204

    list_after = await client.get(
        f"/api/v1/admin/businesses/{biz.id}/staff/exceptions", headers=auth_header(owner)
    )
    assert list_after.json() == []


async def test_exception_for_mismatched_staff_404s(client, db):
    biz_a, owner_a = await _owner(db)
    biz_b = await make_business(db, slug="staff-biz-b")
    staff_b = await make_staff(db, biz_b)
    await db.commit()

    resp = await client.post(
        f"/api/v1/admin/businesses/{biz_a.id}/staff/exceptions",
        headers=auth_header(owner_a),
        json={"staff_id": str(staff_b.id), "date": "2026-12-25", "type": "leave"},
    )
    assert resp.status_code == 404
