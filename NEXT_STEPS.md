# NEXT_STEPS.md — Exact Next Tasks

Ordered. Pick up at the first unchecked item.

## Backend — essentially done for Phase 1+2 scope
All items from the previous version of this list (FastAPI scaffold, models, migration incl. the exclusion constraint, Telegram auth, availability engine, booking service, routers, seed script, docker/env files, pytest suite) are **done and verified** — see PROGRESS.md for exactly what was run and checked. `docker-compose.yml`/Dockerfiles for the API are written but not yet exercised (no Docker daemon in this sandbox; Postgres was run natively instead) — worth a real `docker compose up` pass on a machine/CI that has Docker, to confirm the Dockerfiles themselves are correct, not just the application code.

## Immediate next (in order)

1. [ ] Frontend scaffold: `apps/web` — Vite + React + TS + Tailwind + shadcn/ui, design tokens from the spec's palette (warm ivory/charcoal + sage/olive/emerald, Manrope/Inter), base layout, Telegram WebApp SDK integration + browser-demo-mode detection (no `window.Telegram.WebApp` → call `/api/v1/auth/demo` instead of `/api/v1/auth/telegram`).
2. [ ] API client layer: typed fetch wrapper + TanStack Query hooks for the existing endpoints (`/businesses/:slug`, `/businesses/:id/services`, `/businesses/:id/staff`, `/businesses/:id/availability`, `/bookings`, `/bookings/mine`, `/bookings/:id/cancel`, `/bookings/:id/reschedule`).
3. [ ] Booking flow screens, in order: business profile → service cards → specialist cards (with "any available") → calendar/time-slot picker (driven by the real availability endpoint, never hardcoded) → confirmation (with notes field) → success screen.
4. [ ] My Appointments screen: upcoming/completed/cancelled tabs, cancel action, reschedule action (re-run the calendar/slot picker for a new time).
5. [ ] Run the whole thing end-to-end by hand in a browser against the local API (demo mode) and fix whatever breaks — this is the first time the frontend and the already-tested backend actually meet.
6. [ ] Telegram bot skeleton (`apps/bot`, aiogram 3.x): `/start /help /book /mybookings /support`, reply keyboard, Mini App launch button, polling entrypoint for local dev. Document BotFather setup. **No real token exists** — this stays structural/documented, not run live, until the user provides one.
7. [ ] Update PROGRESS.md/ROADMAP.md/CHANGELOG.md with what was actually verified for the frontend; commit and push.
8. [ ] Report back to the user: what's runnable right now (backend fully, via curl/pytest; frontend once built), how to try the demo booking flow locally, and exactly what Phase 3+ (admin dashboard, live notifications, analytics, i18n, real deployment) would need.

## Known gaps to flag honestly, not paper over
- Rate limiting is in-process only (documented in `app/core/rate_limit.py` and CLAUDE.md) — fine for one API replica, not for a multi-replica deployment.
- No notification worker yet — `NotificationJob` rows are modeled but nothing creates or consumes them yet (that's Phase 4).
- No admin/business-side UI at all yet (Phase 3) — business owners currently have no way to manage services/staff/schedules except direct DB/seed-script edits.
