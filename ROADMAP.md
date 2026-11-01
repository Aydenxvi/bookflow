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

## Phase 3 — Administration (backend + frontend done and verified this session)
- [x] Owner dashboard overview — stat cards (today/upcoming/completed/cancelled), revenue, popular services, staff workload
- [x] Service management (CRUD, archive/unarchive)
- [x] Staff management (CRUD, service assignment, weekly schedules + breaks, leave/exception management)
- [x] Appointment calendar (date-range + staff/service/status filters, manual booking, status changes, role-scoped visibility)
- [x] Booking policies configuration (business profile, operating hours, booking policy)
- [x] Admin frontend UI (`/admin/*`: Dashboard, Calendar, Services, Staff, Settings pages, demo-admin sign-in) — `apps/web/src/AdminApp.tsx` + `pages/admin/`
- [x] Verified the admin frontend end-to-end with a real headless browser (Playwright) against the live backend — same rigor as Phase 2's customer flow

Backend verification: 41 pytest tests (role enforcement for owner/manager/staff/unauthenticated/non-member, business isolation, CRUD + archive/unarchive, schedule + exception CRUD, manual booking through the real concurrency-safe booking service, status transitions incl. cancel-via-status, dashboard aggregate correctness) — all passing against real PostgreSQL (68/68 total), plus a full manual curl pass against the live seeded ATELIER business before the automated tests existed.

Frontend verification: a real headless-browser (Playwright) run against the live Vite dev server + FastAPI + Postgres — demo-admin sign-in, full service create/edit/archive/unarchive, staff create + service assignment + weekly schedule + leave exception, a manual booking through the calendar + a status change, and business profile/policy edits through Settings — zero application console/page errors (the only console noise was the same two sandbox-blocked requests — Google Fonts and the Telegram WebApp script — already documented for the customer flow, confirmed by inspecting the failed request URLs directly, not application bugs). See PROGRESS.md for details, including one real bug found and fixed in this checkpoint (`admin_staff.py::set_staff_services` returning a stale cached `service_ids` list immediately after a successful update) and a broken half-finished edit found and fixed in `main.tsx` (a leftover `AuthProvider` reference with its import already removed) before any of this verification could even run.

## Phase 4 — Automation (done and verified this session)
- [x] Telegram notifications (confirmations, cancellations, reschedules) — `app/services/notifications.py`, hooked into `booking.py`'s create/transition/reschedule paths
- [x] Scheduled reminder jobs (24h/2h/30m, configurable) via worker — new `apps/worker` service, `SELECT ... FOR UPDATE SKIP LOCKED` claim loop, exponential backoff, no in-memory scheduler
- [x] Booking status history surfaced in UI — `GET /admin/.../bookings/{id}/history` + a timeline dialog on the Calendar page
- [x] Business analytics dashboard (Recharts) — `GET /admin/.../dashboard/analytics` + `AdminAnalyticsPage.tsx`

Backend verification: 7 new notification tests (automatic vs. manual confirmation, guest customers with no Telegram identity, business-setting flags respected, cancellation cancels pending reminders, reschedule sends exactly one combined notification and moves the reminders, dedupe-key double-insert prevention) + 2 history tests + 2 analytics tests, all passing against real PostgreSQL (79/79 total). A new, fully self-contained `apps/worker` package (no shared imports from `apps/api` — a deliberate, documented, hand-kept Core-table schema mirror) has its own 25 tests against a dedicated real Postgres database (`bookflow_worker_test`), covering message rendering, job claiming/backoff/terminal-failure, daily-summary scheduling with no persistent state, and a full integration pass — plus a genuine cross-service smoke test proving the worker's hand-kept schema actually matches what `apps/api`'s real Alembic-migrated database looks like, not just the worker's own test schema.

Frontend verification: `tsc -b` and `vite build` clean (bundle grew from ~515KB to ~912KB with Recharts added — noted in NEXT_STEPS.md as a code-splitting candidate); `oxlint` clean except the same pre-existing harmless categories already documented in Phase 3. A real headless-browser (Playwright) run against the live Vite dev server + FastAPI + Postgres: created a manual booking, opened its status-history dialog (1 entry), changed its status, reopened the dialog (2 entries), navigated to the new Analytics page and confirmed both charts rendered, switched the date-range selector with no crash. Zero application console/page errors — only the same two sandbox-blocked requests (Google Fonts, `telegram.org`) already documented in every prior checkpoint.

**Known, explicitly-flagged gap**: actual delivery to Telegram's live Bot API was never exercised — no real bot token is available in this sandbox, the same honest limitation as the Phase 2 bot skeleton. The worker's `httpx` POST to `api.telegram.org` is implemented and unit-tested with a mocked client, not run against the real API.

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
