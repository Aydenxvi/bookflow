"""Admin-facing auth endpoints: /auth/demo-admin (browser demo mode for the
admin dashboard, spec section 19) and /auth/me (who am I / what can I
administer, used by the admin frontend right after login)."""
from __future__ import annotations

import pytest

from app.models.enums import MembershipRole
from tests.factories import auth_header, make_business, make_membership, make_user

pytestmark = pytest.mark.asyncio


async def test_demo_admin_issues_token_with_owner_membership(client, db):
    await make_business(db, slug="atelier", name="ATELIER", is_demo=True)
    await db.commit()

    resp = await client.post("/api/v1/auth/demo-admin", json={"business_slug": "atelier"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["is_demo"] is True
    assert body["access_token"]


async def test_demo_admin_unknown_business_404s(client, db):
    resp = await client.post("/api/v1/auth/demo-admin", json={"business_slug": "does-not-exist"})
    assert resp.status_code == 404


async def test_demo_admin_token_grants_owner_access(client, db):
    biz = await make_business(db, slug="atelier2", name="ATELIER 2", is_demo=True)
    await db.commit()

    token_resp = await client.post("/api/v1/auth/demo-admin", json={"business_slug": "atelier2"})
    token = token_resp.json()["access_token"]

    resp = await client.get(
        f"/api/v1/admin/businesses/{biz.id}/services", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200


async def test_me_lists_memberships(client, db):
    biz_a = await make_business(db, slug="me-biz-a", name="Biz A")
    biz_b = await make_business(db, slug="me-biz-b", name="Biz B")
    user = await make_user(db, first_name="Multi", last_name="Role")
    await make_membership(db, biz_a, user, role=MembershipRole.BUSINESS_OWNER)
    await make_membership(db, biz_b, user, role=MembershipRole.STAFF)
    await db.commit()

    resp = await client.get("/api/v1/auth/me", headers=auth_header(user))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["first_name"] == "Multi"
    roles_by_slug = {m["business_slug"]: m["role"] for m in body["memberships"]}
    assert roles_by_slug == {"me-biz-a": "business_owner", "me-biz-b": "staff"}


async def test_me_requires_authentication(client, db):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
