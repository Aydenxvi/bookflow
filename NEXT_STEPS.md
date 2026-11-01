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

## Phase 3 — Admin backend done + tested this session; admin frontend not started

1. [x] Admin schemas, auth extensions (`/auth/demo-admin`, `/auth/me`), and 5 new routers (services, staff, business profile/hours/policy, bookings/calendar, dashboard) — all role-gated via `RequireBusinessRole`, all writes audit-logged.
2. [x] 41 new pytest tests covering role enforcement, business isolation, CRUD/archive, schedule + exception management, manual booking through the real booking service (concurrency-safe path), status transitions incl. cancel-via-status, and dashboard aggregate math — all passing against real PostgreSQL (68/68 total with the existing 27).
3. [x] `ruff check` clean on all new/modified backend files (ignoring the same pre-existing, codebase-wide `B008`/`C408` stylistic noise that was already present before this session — FastAPI's `Depends()`-in-defaults idiom and a few `dict(...)` calls in `tests/factories.py`; not something this session introduced or was asked to clean up project-wide).
4. [x] Found and fixed one real bug during testing: `admin_staff.py::set_staff_services` returned a **stale cached `service_ids` list** immediately after a successful PUT, because the `Staff.staff_services` collection had already been loaded into the session's identity map earlier in the same request and SQLAlchemy doesn't auto-refresh an already-loaded collection on a second query. Fixed with an explicit `db.refresh(staff, attribute_names=["staff_services"])` after the commit. Would have shown business owners an out-of-date "which services does this staff member do" list for one request cycle (next page load would've been correct) — worth knowing if a similar "write then immediately re-read the same object in one request" pattern shows up elsewhere.
5. [x] Reseeded the demo ATELIER business to a clean state (manual curl-testing during development had left a "Test Pedicure" archived service, a "Test Barber" staff member, and a completed "Walk-in Joe" booking in it) — confirmed clean via live HTTP afterward (6 services, 3 staff, matching the original seed).
6. [ ] **Admin frontend UI** — not started. Needs, in order:
   - A `/admin` route tree in `apps/web` (or a dedicated app) with its own login via `POST /api/v1/auth/demo-admin` (mirrors how the customer flow already does `/api/v1/auth/demo`), following the spec's "a sample admin dashboard, explorable without a real Telegram account" requirement (section 19).
   - Dashboard overview page (today/upcoming/completed/cancelled counts, revenue, popular services, staff workload) — `GET /dashboard` is ready.
   - Service management page (list incl. archived, create, edit, archive/unarchive) — all 4 endpoints ready.
   - Staff management page (list, create, edit, service assignment, weekly schedule editor incl. breaks, exception/leave management) — all endpoints ready.
   - Appointment calendar (date-range + staff/service/status filters, manual booking form, status-change controls, staff-role sees only their own) — all endpoints ready.
   - Business profile/hours/policy settings page — all endpoints ready.
   - Typed API client additions in `apps/web/src/lib/` mirroring `app/schemas/admin.py` (the same hand-maintained pattern already used for the customer-facing schemas).
7. [ ] Verify the admin frontend end-to-end with a real headless browser (Playwright) against the live backend — same rigor as the Phase 2 customer-flow verification (not just `tsc`/build success).
8. [ ] Update PROGRESS.md/ROADMAP.md/NEXT_STEPS.md/CHANGELOG.md once the admin frontend exists and is verified.
9. [ ] Commit and push the Phase 3 frontend checkpoint.

## Worth doing in a future session, not blocking

- **Exercise `docker compose up` for real** on a machine/CI with a Docker daemon (none is available in this sandbox — Postgres was run natively and the frontend with `npm run dev`/`vite build` directly). The compose file and all three Dockerfiles (`api`, `web`, `bot`) are written to the same standard as the rest of the code but have never themselves been built/run.
- **Get a real Telegram bot token** (via @BotFather — see `apps/bot/README.md`) to actually verify the bot against live Telegram: the reply keyboard, the WebApp Menu Button, and real `initData` flowing into the already-tested backend verification code.
- **Retry the `shadcn` CLI** if this project ever moves to an environment where `ui.shadcn.com` isn't blocked — not required (the hand-written primitives in `apps/web/src/components/ui/` are complete and working), but it's the more typical way to add further shadcn components later.
- Consider generating `apps/web/src/lib/api-types.ts` from the backend's OpenAPI schema instead of hand-maintaining it, now that there's real drift risk as the API grows (the admin schemas this session added make the hand-maintained surface noticeably bigger).
- `services/booking.py::create_booking`'s docstring says an explicit `staff_id` is "re-validated" to confirm it offers the service and is active — the current implementation doesn't actually do that check (it only validates an explicit staff_id's *overlap*, not its service-capability or active status). Pre-existing, not touched this session; worth a look before the admin manual-booking form ships, since that's the first caller that could plausibly pass a staff_id that doesn't actually offer the chosen service.

## Known gaps to flag honestly, not paper over
- Rate limiting is in-process only (documented in `app/core/rate_limit.py` and CLAUDE.md) — fine for one API replica, not for a multi-replica deployment.
- No notification worker yet — `NotificationJob` rows are modeled but nothing creates or consumes them yet (that's Phase 4).
- Admin **backend** is done and tested (see above); there is still no admin **UI** — business owners currently have no way to manage services/staff/schedules except direct API calls (curl/Postman) or DB/seed-script edits.
- The Telegram bot has never been run against real Telegram servers (see above).
