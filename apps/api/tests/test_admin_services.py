"""Admin service CRUD + archive/unarchive (spec section 9), plus the role
and business-isolation checks that gate every admin router: owner/manager
can manage services for their own business only; staff and unauthenticated
callers are rejected; a service never leaks across businesses."""
from __future__ import annotations

import pytest

from app.models.enums import MembershipRole
from tests.factories import auth_header, make_business, make_membership, make_service, make_user

pytestmark = pytest.mark.asyncio


async def _owner(db):
    biz = await make_business(db, slug="svc-biz")
    owner = await make_user(db, first_name="Owner")
    await make_membership(db, biz, owner, role=MembershipRole.BUSINESS_OWNER)
    await db.commit()
    return biz, owner


async def test_list_services_includes_inactive(client, db):
    biz, owner = await _owner(db)
    await make_service(db, biz, name="Active One", is_active=True)
    await make_service(db, biz, name="Archived One", is_active=False)
    await db.commit()

    resp = await client.get(f"/api/v1/admin/businesses/{biz.id}/services", headers=auth_header(owner))
    assert resp.status_code == 200
    names = {s["name"] for s in resp.json()}
    assert names == {"Active One", "Archived One"}


async def test_create_service(client, db):
    biz, owner = await _owner(db)

    resp = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/services",
        headers=auth_header(owner),
        json={
            "name": "Haircut",
            "duration_minutes": 30,
            "price_minor_units": 1500,
            "currency": "USD",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "Haircut"
    assert body["is_active"] is True


async def test_update_service_partial(client, db):
    biz, owner = await _owner(db)
    service = await make_service(db, biz, name="Original", price_minor_units=1000)
    await db.commit()

    resp = await client.patch(
        f"/api/v1/admin/businesses/{biz.id}/services/{service.id}",
        headers=auth_header(owner),
        json={"price_minor_units": 2000},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["price_minor_units"] == 2000
    assert body["name"] == "Original"  # untouched field preserved


async def test_archive_then_unarchive_service(client, db):
    biz, owner = await _owner(db)
    service = await make_service(db, biz, is_active=True)
    await db.commit()

    archived = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/services/{service.id}/archive", headers=auth_header(owner)
    )
    assert archived.status_code == 200
    assert archived.json()["is_active"] is False

    unarchived = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/services/{service.id}/unarchive", headers=auth_header(owner)
    )
    assert unarchived.status_code == 200
    assert unarchived.json()["is_active"] is True


async def test_service_not_found_in_wrong_business(client, db):
    biz_a, owner_a = await _owner(db)
    biz_b = await make_business(db, slug="svc-biz-b")
    service_b = await make_service(db, biz_b)
    await db.commit()

    resp = await client.patch(
        f"/api/v1/admin/businesses/{biz_a.id}/services/{service_b.id}",
        headers=auth_header(owner_a),
        json={"name": "Hijacked"},
    )
    assert resp.status_code == 404


async def test_staff_role_cannot_write_services(client, db):
    biz, _owner_user = await _owner(db)
    staff_user = await make_user(db, first_name="Just Staff")
    await make_membership(db, biz, staff_user, role=MembershipRole.STAFF)
    await db.commit()

    resp = await client.post(
        f"/api/v1/admin/businesses/{biz.id}/services",
        headers=auth_header(staff_user),
        json={"name": "X", "duration_minutes": 30, "price_minor_units": 100, "currency": "USD"},
    )
    assert resp.status_code == 403


async def test_unauthenticated_request_rejected(client, db):
    biz, _ = await _owner(db)
    resp = await client.get(f"/api/v1/admin/businesses/{biz.id}/services")
    assert resp.status_code == 401


async def test_non_member_rejected(client, db):
    biz, _ = await _owner(db)
    outsider = await make_user(db, first_name="Outsider")
    await db.commit()

    resp = await client.get(f"/api/v1/admin/businesses/{biz.id}/services", headers=auth_header(outsider))
    assert resp.status_code == 403
