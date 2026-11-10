# NEXT_STEPS.md — Exact Next Tasks

Ordered. Pick up at the first unchecked item.

## Phase 1 + Phase 2 — done, committed
Backend, frontend, and a Telegram bot skeleton are all built and verified —
see PROGRESS.md for exactly what was run and checked (27/27 backend
pytest, a real headless-browser click-through of the full booking flow
twice over, bot handlers import/register-verified).

1. [x] Frontend scaffold, design tokens, booking flow screens, My Appointments, Telegram SDK + demo-mode detection.
2. [x] Typed API client + TanStack Query hooks.
3. [x] End-to-end manual (headless-browser) run against the local API in demo mode.
4. [x] Telegram bot skeleton (`apps/bot`) — structural/documented, not run live (no token).
5. [x] Update PROGRESS.md/ROADMAP.md/CHANGELOG.md with what was actually verified.
6. [x] Commit and push this checkpoint to `Aydenxvi/bookflow`.

## Phase 3 — Admin backend + frontend done and verified, committed

1. [x] Admin schemas, auth extensions (`/auth/demo-admin`, `/auth/me`), and 5 new routers (services, staff, business profile/hours/policy, bookings/calendar, dashboard) — all role-gated via `RequireBusinessRole`, all writes audit-logged.
2. [x] 41 new pytest tests covering role enforcement, business isolation, CRUD/archive, schedule + exception management, manual booking through the real booking service (concurrency-safe path), status transitions incl. cancel-via-status, and dashboard aggregate math — all passing against real PostgreSQL (68/68 total with the existing 27).
3. [x] `ruff check` clean on all new/modified backend files (ignoring the same pre-existing, codebase-wide `B008`/`C408` stylistic noise already present before this session).
4. [x] Found and fixed one real backend bug during testing: `admin_staff.py::set_staff_services` returned a **stale cached `service_ids` list** immediately after a successful PUT (SQLAlchemy identity-map staleness — fixed with an explicit `db.refresh(..., attribute_names=["staff_services"])`).
5. [x] Admin frontend UI built: `/admin/*` route tree in `apps/web` (`AdminApp.tsx` + `pages/admin/`), its own demo sign-in via `POST /api/v1/auth/demo-admin` (`lib/admin-auth.tsx`), a typed API client + TanStack Query hooks mirroring every admin endpoint (`lib/admin-api-client.ts`, `admin-api-types.ts`, `admin-queries.ts`), and all 5 pages: **Dashboard** (stat cards, revenue, popular services, staff workload), **Services** (list incl. archived, create/edit, archive/unarchive), **Staff** (list, create/edit, service-assignment toggles, a shared `ScheduleEditor` component for weekly hours + breaks, leave/closure exceptions), **Calendar** (date-range + staff/service/status filters, manual booking form, status-change buttons, role-scoped visibility already enforced server-side), **Settings** (business profile, operating hours via the same `ScheduleEditor`, booking policy). `App.tsx` now splits into `CustomerApp`/`AdminApp` at `/admin/*` vs. everything else, each with its own independent auth context so a browser can hold a customer demo session and an admin demo session at the same time.
6. [x] Found and fixed a broken half-finished edit left in `main.tsx` before any of the above could even build: a leftover `AuthProvider` reference whose import had already been removed (the provider had been correctly moved into `CustomerApp`, but the old top-level wrapper and its usage in `main.tsx` weren't fully cleaned up) — `tsc -b` would have failed outright without this fix.
7. [x] `tsc -b` (strict) and `vite build` both clean; `oxlint` clean except the same two categories of pre-existing, documented harmless warnings (`new Date()`-in-render purity notices, `only-export-components` fast-refresh notices for files that intentionally export a helper alongside a component — same shadcn/ui-adjacent pattern as before).
8. [x] Verified the admin frontend end-to-end with a real headless browser (Playwright) against the live Vite dev server + FastAPI + real Postgres, not mocked: demo-admin sign-in → dashboard → created/edited/archived/unarchived a service → created a staff member with that service assigned → set their weekly schedule → added a leave exception → created a manual booking on the calendar → changed its status → edited the business profile and booking policy in Settings → revisited the dashboard. Zero application console/page errors — the only console noise was the same two sandbox-blocked requests (Google Fonts, the Telegram WebApp script) already documented for the customer flow in Phase 2, confirmed this time by inspecting the actual failed request URLs rather than assuming.
9. [x] Reseeded the demo ATELIER business to a clean state after both the backend manual-curl pass and the frontend E2E pass left test artifacts in it — confirmed clean via live HTTP both times (6 services, 3 staff, matching the original seed).
10. [x] Update PROGRESS.md/ROADMAP.md/NEXT_STEPS.md/CHANGELOG.md with everything actually verified above.
11. [x] Commit and push this Phase 3 frontend checkpoint.

## Phase 4 — Automation: done and verified, committed

1. [x] Notification enqueueing service (`app/services/notifications.py`) hooked into `booking.py`'s create/transition/cancel/reschedule paths (not into routers, so customer- and admin-created bookings both notify consistently); a new `suppress_notifications` keyword-only parameter on `create_booking`/`transition_status` prevents double-notifying on reschedule.
2. [x] 7 new pytest tests covering automatic vs. manual confirmation, guest customers with no Telegram identity, business-settings-flag respect, cancel-cancels-pending-reminders, reschedule-sends-one-combined-notification, and dedupe-key double-insert prevention — all passing against real PostgreSQL. One real bug (`_enqueue` omitting `dedupe_key`, a `NOT NULL` column) caught by the tests before they ever passed.
3. [x] New `apps/worker` package built from scratch: self-contained hand-kept Core-table schema mirror (documented, not importing `apps/api`'s ORM), `SELECT ... FOR UPDATE SKIP LOCKED` claim loop, exponential backoff with a terminal `FAILED` status, and no-persistent-state daily-summary scheduling via business-local `zoneinfo` bucketing + dedupe-key existence checks.
4. [x] 25 new pytest tests for the worker against a dedicated real Postgres database (`bookflow_worker_test`), plus a genuine cross-service smoke test proving the worker's hand-kept schema matches `apps/api`'s real Alembic-migrated schema.
5. [x] Booking status history exposed: `GET .../bookings/{id}/history` + a "History" dialog on the Calendar page (the underlying `BookingStatusHistory` rows already existed from an earlier checkpoint). 2 new pytest tests.
6. [x] Business analytics dashboard: `GET .../dashboard/analytics?days=N` (business-local-date bucketing via `zoneinfo`, revenue summing, status breakdown) + `AdminAnalyticsPage.tsx` using Recharts v3 (`ComposedChart` for bookings/revenue, `PieChart` for status breakdown). 2 new pytest tests.
7. [x] `apps/worker` added to `docker-compose.yml` (default `up`, not profile-gated like `bot`).
8. [x] Full backend suite: 79/79 passing against real PostgreSQL. `ruff check` clean on new/modified files bar the same pre-existing `B008`/`C408` noise from Phase 3.
9. [x] Frontend: `tsc -b` and `vite build` clean; `oxlint` clean bar the same pre-existing harmless categories. Bundle grew ~515KB → ~912KB with Recharts (see "Worth doing" below).
10. [x] Real headless-browser (Playwright) E2E pass against the live stack: manual booking → History dialog shows 1 entry → status change → History shows 2 entries → Analytics page renders both charts → date-range switch doesn't crash. Zero application console/page errors. One test-script bug (an ambiguous Playwright locator) found and fixed along the way — not an application bug.
11. [x] Demo data reseeded to a clean state afterward (duplicate test bookings from the locator-bug-affected first run, plus the final run's own test booking, both cleaned up via direct `psql` deletes).
12. [x] Update PROGRESS.md/ROADMAP.md/NEXT_STEPS.md/CHANGELOG.md with everything actually verified above.
13. [x] Commit and push this Phase 4 checkpoint (`9480ecc`).

**Explicitly flagged, not papered over**: actual delivery to Telegram's live Bot API was never exercised in this checkpoint either — no real bot token available in this sandbox. The worker's `httpx` POST to `api.telegram.org` is implemented and tested only against a mocked HTTP client.

## Phase 4.5 — Docker verified on a real machine, demo UX polish, VPS groundwork

See CHANGELOG.md's 2026-11-10 entry for full detail.

1. [x] `docker compose up` run for real for the first time (on the project owner's own machine, ports remapped via `.env` to avoid colliding with unrelated local projects) — found and fixed two real bugs: `apps/worker`'s `pyproject.toml` packaging (explicit `packages` list vs. Dockerfile layer order) and `apps/api`'s hardcoded CORS allowlist (now a dev-only regex, off in production).
2. [x] Demo-mode banners (customer + admin) made dismissible via a close button, remembered per-browser.
3. [x] Home page hero/cover placeholder shrunk (`h-40` → `h-24`) now that the banner above it can be dismissed.
4. [x] A real Telegram bot token obtained (via @BotFather) — still not yet exercised against live Telegram from any session working on this repo.
5. [x] VPS deployment groundwork: Caddy reverse proxy + automatic HTTPS added under a new `prod` Compose profile, `.env.example`/README updated with a full "Deploying to a real VPS" walkthrough (Oracle Cloud Free Tier + free `sslip.io`/DuckDNS hostname, no code rewrite).
6. [ ] **Actually provision the VPS and go live** — the one step that needs the project owner's own action (cloud account signup, is identity/payment verification, DNS): create the Oracle Cloud Free Tier instance, point a free hostname at its IP, copy `.env` with real `DOMAIN`/`TELEGRAM_BOT_TOKEN`/`ENVIRONMENT=production` values, run `docker compose --profile prod --profile bot up -d --build`, confirm Caddy's cert issuance and `/health`, then set the Mini App Menu Button URL in @BotFather. Not done yet — pick this up next.
7. [ ] Once live, verify the bot and worker against real Telegram for the first time (send a real message, confirm a real notification lands) — closes the oldest "known gap" in this file.
8. [ ] Update PROGRESS.md/ROADMAP.md with the above once the VPS is actually live and verified — don't check off "deployed" here until it's confirmed reachable from a real Telegram client, not just that the containers started.

## Worth doing in a future session, not blocking

- **Retry the `shadcn` CLI** if this project ever moves to an environment where `ui.shadcn.com` isn't blocked — not required (the hand-written primitives in `apps/web/src/components/ui/` are complete and working), but it's the more typical way to add further shadcn components later.
- Consider generating `apps/web/src/lib/api-types.ts`/`admin-api-types.ts` from the backend's OpenAPI schema instead of hand-maintaining them, now that there's real drift risk as the API surface has grown across three checkpoints.
- `services/booking.py::create_booking`'s docstring says an explicit `staff_id` is "re-validated" to confirm it offers the service and is active — the current implementation doesn't actually do that check (it only validates an explicit staff_id's *overlap*, not its service-capability or active status). Pre-existing, not touched this session; the admin manual-booking form is the first caller that could plausibly pass a staff_id that doesn't actually offer the chosen service — worth a look.
- The main bundle is a single JS chunk, now **~912KB** (`vite build` warns past 500KB) after adding Recharts for the analytics page — worth code-splitting the admin bundle from the customer bundle (they're never needed in the same page load), and/or lazy-loading Recharts specifically, if this grows further.
- **Admin UI polish not attempted**: no loading-skeleton-to-content transition animation, no optimistic updates on mutations (every save does a full refetch), no toast confirmation on successful saves (errors show inline, but a successful "Service created" currently has no explicit feedback beyond the dialog closing and the list updating). None of this blocks functionality; it's a polish pass, closer to Phase 5's scope.
- `apps/worker`'s `app/tables.py` is a **hand-kept mirror** of the relevant parts of `apps/api`'s real schema (deliberate, to avoid a shared-ORM dependency across a process boundary — see PROGRESS.md), which means a future migration touching `notification_jobs`, `bookings`, `business_settings`, `booking_policies`, or `business_memberships` must update both places by hand. The cross-service smoke test proves they match *today*; nothing currently guards against future drift automatically — worth a CI check or a shared schema-contract test if this becomes a recurring risk.
- The worker's claim loop holds a row lock for the full duration of the Telegram API call (a deliberate simplicity trade-off, documented in `app/claim.py`) — fine at this scale, but worth revisiting if job volume or `httpx` latency ever grows enough to make that lock duration matter for throughput.

## Known gaps to flag honestly, not paper over
- Rate limiting is in-process only (documented in `app/core/rate_limit.py` and CLAUDE.md) — fine for one API replica, not for a multi-replica deployment.
- The Telegram bot and the worker's notification delivery have still never been run against real Telegram servers — a real `BOT_TOKEN` now exists (see Phase 4.5), but it hasn't been exercised yet; both remain implemented and tested only against fakes/mocks until the VPS go-live happens.
- `docker compose up` (local profiles) has now actually been run and verified on a real machine (see Phase 4.5/CHANGELOG) — the previously-flagged "never run" gap is closed for local dev. The `prod`/Caddy profile, specifically, has NOT yet been run against a real VPS — don't mark deployment done until that happens.
- `apps/worker`'s schema is a hand-kept mirror of `apps/api`'s, not a shared import — proven to match today by a real cross-service smoke test, but with no automated guard against future drift (see "Worth doing" above).
