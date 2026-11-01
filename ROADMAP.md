# ROADMAP.md — BookFlow Development Phases

Checkboxes are only ticked once the item has actually been built AND verified (ran, tested, or visually checked) — see PROGRESS.md for what was actually verified and how.

## Phase 1 — Foundation
- [x] Initialize repository (monorepo structure)
- [x] Persistent progress files
- [x] Configure backend (FastAPI app skeleton, settings, structured logging)
- [x] Configure PostgreSQL + async SQLAlchemy 2.x engine/session
- [x] Database models for all core entities
- [x] Alembic migrations (initial schema, incl. overlap-exclusion constraint) — applied and verified against a real database
- [x] Configure frontend (Vite + React + TS + Tailwind + shadcn/ui) — shadcn/ui's CLI registry is blocked in this sandbox, so the primitives were hand-written in the same pattern against Radix UI; see PROGRESS.md
- [x] Establish design system (tokens, fonts, base layout) — `src/index.css` `@theme`, `AppShell` + bottom nav
- [x] Configure Telegram bot project (aiogram 3.x skeleton) — handlers import/register verified; never run live (no token)
- [x] Implement Telegram `initData` authentication verification (backend) — unit tested
- [x] Demo mode foundation (demo auth endpoint) — exercised end-to-end over HTTP

## Phase 2 — Booking MVP
- [x] Business profile **screen** — `HomePage`, driven by the real backend endpoint
- [x] Service selection **screen** — `HomePage`, grouped by category
- [x] Staff/specialist selection **screen** — `SpecialistPage`, incl. "any available"
- [x] Availability engine: real slot computation — tested incl. DST, breaks, exceptions, lead time
- [x] Booking creation with DB-enforced overlap prevention + transactional revalidation + idempotency key — tested incl. a real concurrent-race test, and a real browser booking through the UI
- [x] Booking confirmation step + success **screen** — `ConfirmPage` (notes, 409-conflict handling) + `SuccessPage`
- [x] My Appointments **screen** — `AppointmentsPage`, upcoming/completed/cancelled tabs
- [x] Cancellation (policy-aware) — backend done and tested; UI confirm-dialog driven, verified in a real browser
- [x] Reschedule — backend done and tested; UI in-dialog slot picker, verified in a real browser
- [x] Real Postgres persistence end-to-end — proven via direct HTTP calls *and* a real headless-browser click-through, not just unit tests
- [x] Seed demo data: ATELIER — Modern Grooming Studio

**Phase 2 exit criterion**: a user can open the Mini App (or browser demo mode), pick a service, pick a specialist, pick a real available slot, confirm, see success, see it in My Appointments, and cancel it. **Done, and verified exactly that way with a real headless browser against the real running stack — see PROGRESS.md for the two full runs (one via "any available", one via a named specialist including a reschedule).**

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
