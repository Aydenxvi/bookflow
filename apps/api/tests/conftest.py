"""Test fixtures. Runs against a real PostgreSQL database (bookflow_test),
not SQLite — the booking engine depends on Postgres-only features (the
btree_gist EXCLUDE constraint, tstzrange), so a SQLite-backed test suite
would not actually exercise the thing that matters most here.

Each test gets a clean schema: we drop/recreate all tables once per test
function via SQLAlchemy metadata (fast enough at this table count) rather
than wrapping in a rolled-back transaction, since the code under test opens
its own transactions/commits deliberately (advisory locks, etc.) and nested
transactions would mask exactly the behavior we're testing.
"""
from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import httpx
import pytest_asyncio
from httpx import ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://bookflow:bookflow@localhost:5432/bookflow_test"
)
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-bot-token-for-signing")

import app.models  # noqa: F401
from app.db.session import Base, get_db
from app.main import app as fastapi_app

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

def _make_engine():
    # NullPool: each checkout opens a fresh asyncpg connection and closes it
    # on release, rather than keeping one bound to whichever event loop
    # happened to create it. pytest-asyncio gives each test function its own
    # event loop by default, and a pooled asyncpg connection from a previous
    # loop breaks with "another operation is in progress" — NullPool avoids
    # that cross-loop reuse entirely.
    return create_async_engine(TEST_DATABASE_URL, future=True, poolclass=NullPool)


engine = _make_engine()
TestSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture(autouse=True)
async def _reset_schema() -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        await conn.run_sync(Base.metadata.create_all)
        # The generated column + EXCLUDE constraint are hand-written in the
        # Alembic migration, not part of the ORM metadata (see booking.py's
        # module docstring) — recreate them here too so tests exercise the
        # exact same database-level guarantee production migrations create.
        await conn.execute(
            text(
                """
                ALTER TABLE bookings
                ADD COLUMN during tstzrange
                GENERATED ALWAYS AS (tstzrange(starts_at, ends_at, '[)')) STORED
                """
            )
        )
        await conn.execute(
            text(
                """
                ALTER TABLE bookings
                ADD CONSTRAINT excl_bookings_staff_overlap
                EXCLUDE USING gist (staff_id WITH =, during WITH &&)
                WHERE (status IN ('PENDING', 'CONFIRMED', 'COMPLETED'))
                """
            )
        )
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def db_factory():
    """For concurrency tests that need multiple independent sessions/connections."""

    def _make() -> AsyncSession:
        return TestSessionLocal()

    return _make


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    """An HTTP client for the real FastAPI app, used to test admin router
    behavior end-to-end (role enforcement, status codes, response shapes) —
    things that can't be verified by calling an endpoint function directly.

    `get_db` is overridden to hand out the *same* session the test itself
    uses, so factory-created rows (flushed, not necessarily committed) are
    visible to the request without any cross-connection visibility games.
    """

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    fastapi_app.dependency_overrides.pop(get_db, None)
