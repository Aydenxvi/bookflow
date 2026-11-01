# CLAUDE.md — BookFlow Project Instructions

This file is the permanent reference for any Claude session (or human) resuming work on BookFlow. Read this, PROGRESS.md, ROADMAP.md, and NEXT_STEPS.md before touching code.

## What BookFlow Is

A premium Telegram-first appointment-booking platform. Customers book through a Telegram Mini App; business owners manage everything through a web admin dashboard. Multi-tenant: many independent businesses on one platform. Portfolio-quality, with a path to becoming a real SaaS product.

Reference spec: `docs/ORIGINAL_SPEC.md` (the full original brief, kept verbatim for traceability). This CLAUDE.md is the authoritative day-to-day guide; where they conflict, decisions recorded here win because they reflect what was actually built and why.

## Repository Layout

```
bookflow/
  apps/
    web/      # React + TS + Vite + Tailwind + shadcn/ui — Telegram Mini App (customer) + Admin Dashboard (business)
    api/      # FastAPI + SQLAlchemy 2.x async + PostgreSQL — the backend
    worker/   # Notification worker (PostgreSQL-backed job queue, idempotent)
    bot/      # aiogram 3.x Telegram bot
  packages/
    shared/   # Shared TypeScript types / constants used by web (and generated from API schemas where practical)
  docs/       # Architecture notes, ORIGINAL_SPEC.md, setup guides
  infrastructure/  # Docker/deploy-related config beyond docker-compose.yml
  docker-compose.yml
  .env.example
```

## Key Architectural Decisions

- **Backend**: FastAPI, async SQLAlchemy 2.x (asyncpg driver), Alembic migrations, Pydantic v2 schemas. Layered as `api/app/{models,schemas,routers,services,core}`.
- **Scheduling engine** (`apps/api/app/services/availability.py` + `booking.py`): slot generation considers business hours, staff working schedules, breaks/exceptions, existing bookings, service duration, buffer time, lead time, max advance window, business timezone (stored as IANA tz string, e.g. `Europe/Istanbul`). All appointment timestamps are stored in UTC in the DB; conversion to/from business-local time happens at the service layer.
- **Concurrency safety**: booking creation is guarded two ways — (1) a PostgreSQL `EXCLUDE` constraint using `btree_gist` on `(staff_id, during tstzrange)` prevents overlapping bookings at the database level regardless of application logic; (2) the booking service re-validates availability inside the same transaction immediately before insert, under `SELECT ... FOR UPDATE` on the staff's relevant rows, to fail fast with a clean error instead of relying solely on the constraint. Idempotency keys (`Idempotency-Key` header, stored on `Booking.idempotency_key`, unique per business) prevent duplicate bookings from client retries.
- **Money**: prices stored as integer minor units (e.g. cents/kopecks) — `price_minor_units: int` + `currency: str`. Never float.
- **Auth**: Telegram `initData` is verified server-side per the official HMAC-SHA256 protocol (bot token as key, checking `hash` and `auth_date` freshness). `initDataUnsafe` is never trusted. A separate **browser demo mode** issues a short-lived demo JWT scoped to the demo business, with all writes clearly flagged `is_demo=true` and isolated from real data — see "Demo Mode" below.
- **Multi-tenancy**: every tenant-scoped table carries `business_id`; a FastAPI dependency (`require_business_context`) enforces that the authenticated principal (customer or staff) only ever queries/mutates rows for businesses they belong to. Role enforcement (`platform_admin`, `business_owner`, `business_manager`, `staff`, `customer`) happens server-side in `app/core/authz.py`, never trusted from the client.
- **Notifications**: `NotificationJob` rows in Postgres, picked up by `apps/worker`, which claims jobs with `SELECT ... FOR UPDATE SKIP LOCKED`, is idempotent per `(job_type, booking_id, kind)`, and retries with backoff. No in-memory scheduler.

## Demo Mode

Because this is a portfolio project, anyone must be able to try the booking flow without a real Telegram account:
- A seeded business **ATELIER — Modern Grooming Studio** with services, staff, schedules.
- `apps/web` detects it's not running inside Telegram (`window.Telegram?.WebApp` absent) and switches to demo mode: calls `/api/v1/auth/demo` instead of `/api/v1/auth/telegram`, gets a demo-scoped token.
- Demo bookings are real rows in the same schema (so the booking engine is genuinely exercised) but flagged `is_demo=true` and excluded from any real analytics/exports. A periodic cleanup can purge demo bookings older than N days (not required for MVP).

## Status Enums

`BookingStatus`: `pending`, `confirmed`, `completed`, `cancelled`, `no_show`.
Valid transitions are enforced in `app/services/booking.py::transition_status` — see that file's `VALID_TRANSITIONS` map before changing status logic.

## Conventions

- Python: type-hinted, async everywhere in the API/worker, `ruff` for lint (config in `apps/api/pyproject.toml`).
- TypeScript: strict mode on, no `any` without a comment explaining why.
- Commits: small, meaningful, Conventional-Commits-ish (`feat:`, `fix:`, `chore:`) — not mandatory but preferred.
- Never fabricate "done": a feature is only checked off in ROADMAP.md once it has actually been run/tested, per PROGRESS.md's validation notes.

## Session Recovery Protocol

At the start of any new session continuing this project:
1. Read this file, `PROGRESS.md`, `ROADMAP.md`, `NEXT_STEPS.md`.
2. `git log --oneline -20` and `git status`.
3. Skim the actual code for anything NEXT_STEPS.md claims is in progress, to verify its real state.
4. Continue from the next unfinished task in NEXT_STEPS.md. Do not restart or rewrite completed modules without a documented reason (record it in CHANGELOG.md if you do).

No bot token, live Postgres server, or deployment target were available when this project was started — everything was built and tested against local Docker Compose services. Check NEXT_STEPS.md / PROGRESS.md for whether that has changed.
