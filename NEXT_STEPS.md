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
11. [ ] Commit and push this Phase 3 frontend checkpoint.

## Worth doing in a future session, not blocking

- **Exercise `docker compose up` for real** on a machine/CI with a Docker daemon (none is available in this sandbox — Postgres was run natively and the frontend with `npm run dev`/`vite build` directly). The compose file and all three Dockerfiles (`api`, `web`, `bot`) are written to the same standard as the rest of the code but have never themselves been built/run.
- **Get a real Telegram bot token** (via @BotFather — see `apps/bot/README.md`) to actually verify the bot against live Telegram: the reply keyboard, the WebApp Menu Button, and real `initData` flowing into the already-tested backend verification code.
- **Retry the `shadcn` CLI** if this project ever moves to an environment where `ui.shadcn.com` isn't blocked — not required (the hand-written primitives in `apps/web/src/components/ui/` are complete and working), but it's the more typical way to add further shadcn components later.
- Consider generating `apps/web/src/lib/api-types.ts`/`admin-api-types.ts` from the backend's OpenAPI schema instead of hand-maintaining them, now that there's real drift risk as the API surface has grown across two checkpoints.
- `services/booking.py::create_booking`'s docstring says an explicit `staff_id` is "re-validated" to confirm it offers the service and is active — the current implementation doesn't actually do that check (it only validates an explicit staff_id's *overlap*, not its service-capability or active status). Pre-existing, not touched this session; the admin manual-booking form is the first caller that could plausibly pass a staff_id that doesn't actually offer the chosen service — worth a look.
- The main bundle is a single ~515KB JS chunk (`vite build` warns past 500KB) — fine for now, but worth code-splitting the admin bundle from the customer bundle (they're never needed in the same page load) if this grows further.
- **Admin UI polish not attempted**: no loading-skeleton-to-content transition animation, no optimistic updates on mutations (every save does a full refetch), no toast confirmation on successful saves (errors show inline, but a successful "Service created" currently has no explicit feedback beyond the dialog closing and the list updating). None of this blocks functionality; it's a polish pass, closer to Phase 5's scope.

## Known gaps to flag honestly, not paper over
- Rate limiting is in-process only (documented in `app/core/rate_limit.py` and CLAUDE.md) — fine for one API replica, not for a multi-replica deployment.
- No notification worker yet — `NotificationJob` rows are modeled but nothing creates or consumes them yet (that's Phase 4).
- The Telegram bot has never been run against real Telegram servers (see above).
- No Docker daemon in this sandbox — `docker compose up` has never actually been run for any of the three services (see above).
