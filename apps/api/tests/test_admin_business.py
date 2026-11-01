"""Admin business profile, operating hours, and booking policy — and the
owner-vs-manager distinction (profile edits are owner-only; manager can
still view and manage hours/policy)."""
from __future__ import annotations

import pytest

from app.models.enums import MembershipRole
from tests.factories import auth_header, make_business, make_membership, make_user

pytestmark = pytest.mark.asyncio


async def _business_with_roles(db):
    biz = await make_business(db, slug="hours-biz", timezone="Europe/Istanbul")
    owner = await make_user(db, first_name="Owner")
    manager = await make_user(db, first_name="Manager")
    await make_membership(db, biz, owner, role=MembershipRole.BUSINESS_OWNER)
    await make_membership(db, biz, manager, role=MembershipRole.BUSINESS_MANAGER)
    await db.commit()
    return biz, owner, manager


async def test_update_profile_as_owner(client, db):
    biz, owner, _manager = await _business_with_roles(db)

    resp = await client.patch(
        f"/api/v1/admin/businesses/{biz.id}/profile",
        headers=auth_header(owner),
        json={"name": "Renamed Studio", "timezone": "America/New_York"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "Renamed Studio"
    assert resp.json()["timezone"] == "America/New_York"


async def test_update_profile_rejects_invalid_timezone(client, db):
    biz, owner, _manager = await _business_with_roles(db)

    resp = await client.patch(
        f"/api/v1/admin/businesses/{biz.id}/profile",
        headers=auth_header(owner),
        json={"timezone": "Not/ARealZone"},
    )
    assert resp.status_code == 422


async def test_manager_cannot_update_profile(client, db):
    biz, _owner, manager = await _business_with_roles(db)

    resp = await client.patch(
        f"/api/v1/admin/businesses/{biz.id}/profile",
        headers=auth_header(manager),
        json={"name": "Hostile Takeover"},
    )
    assert resp.status_code == 403


async def test_manager_can_view_profile(client, db):
    biz, _owner, manager = await _business_with_roles(db)

    resp = await client.get(f"/api/v1/admin/businesses/{biz.id}/profile", headers=auth_header(manager))
    assert resp.status_code == 200


async def test_set_and_get_business_hours(client, db):
    biz, owner, _manager = await _business_with_roles(db)

    put_resp = await client.put(
        f"/api/v1/admin/businesses/{biz.id}/hours",
        headers=auth_header(owner),
        json={"days": [{"weekday": 0, "start_time": "08:00", "end_time": "20:00", "breaks": []}]},
    )
    assert put_resp.status_code == 200, put_resp.text
    [day] = put_resp.json()
    assert day["start_time"] == "08:00"
    assert day["end_time"] == "20:00"

    get_resp = await client.get(f"/api/v1/admin/businesses/{biz.id}/hours", headers=auth_header(owner))
    assert get_resp.json() == put_resp.json()


async def test_manager_can_set_hours(client, db):
    biz, _owner, manager = await _business_with_roles(db)

    resp = await client.put(
        f"/api/v1/admin/businesses/{biz.id}/hours",
        headers=auth_header(manager),
        json={"days": [{"weekday": 0, "start_time": "09:00", "end_time": "18:00", "breaks": []}]},
    )
    assert resp.status_code == 200


async def test_policy_get_creates_default_then_update(client, db):
    biz, owner, _manager = await _business_with_roles(db)

    get_resp = await client.get(f"/api/v1/admin/businesses/{biz.id}/policy", headers=auth_header(owner))
    assert get_resp.status_code == 200
    default_body = get_resp.json()
    assert default_body["slot_interval_minutes"] > 0

    patch_resp = await client.patch(
        f"/api/v1/admin/businesses/{biz.id}/policy",
        headers=auth_header(owner),
        json={"min_lead_time_minutes": 30, "max_advance_days": 45},
    )
    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert body["min_lead_time_minutes"] == 30
    assert body["max_advance_days"] == 45


async def test_outsider_cannot_view_business_admin_endpoints(client, db):
    biz, _owner, _manager = await _business_with_roles(db)
    outsider = await make_user(db, first_name="Outsider")
    await db.commit()

    resp = await client.get(f"/api/v1/admin/businesses/{biz.id}/policy", headers=auth_header(outsider))
    assert resp.status_code == 403
