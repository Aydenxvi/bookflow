"""Test fixtures for the worker's own, self-contained test database
(bookflow_worker_test — see README.md to create it once). Deliberately not
the same database as apps/api's tests: the worker is a separate deployable
package (own pyproject.toml, own top-level `app` module) and does not import
apps/api's ORM models (see app/tables.py's docstring), so its tests build
the schema from its OWN Core `metadata` object instead of borrowing apps/api's
Alembic migration or ORM Base. That schema is a hand-kept subset (exactly the
columns app/tables.py declares) — enough to exercise claim/retry/render
logic for real against real PostgreSQL, not a claim that it's the full
production schema.
"""
from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://bookflow:bookflow@localhost:5432/bookflow_worker_test"
)

from app.tables import metadata

TEST_DATABASE_URL = os.environ["DATABASE_URL"]


def _make_engine() -> AsyncEngine:
    return create_async_engine(TEST_DATABASE_URL, future=True, poolclass=NullPool)


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    eng = _make_engine()
    async with eng.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(metadata.drop_all)
    await eng.dispose()
