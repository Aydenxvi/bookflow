# ROADMAP.md — BookFlow Development Phases

Checkboxes are only ticked once the item has actually been built AND verified (ran, tested, or visually checked) — see PROGRESS.md for validation notes. Do not tick from intention; this file is updated at the end of each work session, not drafted in advance.

## Phase 1 — Foundation
- [x] Initialize repository (monorepo structure: apps/web, apps/bot, apps/api, apps/worker, packages/shared, docs/, infrastructure/)
- [x] Persistent progress files (CLAUDE.md, PROGRESS.md, ROADMAP.md, NEXT_STEPS.md, CHANGELOG.md, README.md, docs/ORIGINAL_SPEC.md)
- [ ] Configure backend (FastAPI app skeleton, settings, structured logging)
- [ ] Configure PostgreSQL + async SQLAlchemy 2.x engine/session
- [ ] Database models for all core entities
- [ ] Alembic migrations (initial schema, incl. overlap-exclusion constraint)
- [ ] Configure frontend (Vite + React + TS + Tailwind + shadcn/ui)
- [ ] Establish design system (tokens, fonts, base layout)
- [ ] Configure Telegram bot project (aiogram 3.x skeleton)
- [ ] Implement Telegram `initData` authentication verification (backend)
- [ ] Demo mode foundation (demo auth endpoint + frontend detection)

## Phase 2 — Booking MVP
- [ ] Business profile endpoint + screen
- [ ] Service selection (list + cards)
- [ ] Staff/specialist selection ("any available" included)
- [ ] Availability engine: real slot computation (hours, breaks, exceptions, buffer, lead time, advance window, timezone)
- [ ] Booking creation with DB-enforced overlap prevention + transactional revalidation + idempotency key
- [ ] Booking confirmation step + success screen
- [ ] My Appointments (upcoming/completed/cancelled tabs)
- [ ] Cancellation (policy-aware)
- [ ] Reschedule (reuses availability + overlap safety)
- [ ] Real Postgres persistence end-to-end (no mocked data on the booking path)
- [ ] Seed demo data: ATELIER — Modern Grooming Studio

**Phase 2 exit criterion**: a user can open the Mini App (or browser demo mode), pick a service, pick a specialist, pick a real available slot, confirm, see success, see it in My Appointments, and cancel it — all against the real database with overlap protection, with this actually run and checked, not just coded.

## Phase 3 — Administration (not started, out of scope for this session)
- [ ] Owner dashboard overview
- [ ] Service management (CRUD, archive)
- [ ] Staff management (CRUD, schedules, breaks, leave)
- [ ] Appointment calendar (daily/weekly, filters, manual booking, status changes)
- [ ] Booking policies configuration UI

## Phase 4 — Automation (not started, out of scope for this session)
- [ ] Telegram notifications (confirmations, cancellations, reschedules)
- [ ] Scheduled reminder jobs (24h/2h/30m, configurable) via worker
- [ ] Booking status history surfaced in UI
- [ ] Business analytics dashboard (Recharts)

## Phase 5 — Commercial Readiness (not started, out of scope for this session)
- [ ] Multi-business onboarding flow
- [ ] Advanced settings (branding, policies, notification prefs)
- [ ] Internationalization (en/ru/tr)
- [ ] Responsive polish pass
- [ ] UI animation pass (Motion/Framer)
- [ ] Demo enhancements
- [ ] Security test pass (rate limiting, audit log review)
- [ ] Deployment configuration validated against a real host
- [ ] Full documentation pass

See NEXT_STEPS.md for the exact next task.
