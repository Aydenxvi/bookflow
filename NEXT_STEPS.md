# NEXT_STEPS.md — Exact Next Tasks

Ordered. Pick up at the first unchecked item; don't skip ahead.

1. [ ] Backend scaffold: `apps/api` — FastAPI app factory, settings (pydantic-settings), structured logging, health endpoint, async SQLAlchemy engine/session setup, Alembic init.
2. [ ] Backend models: all entities from docs/ORIGINAL_SPEC.md section 17, in `apps/api/app/models/`.
3. [ ] Alembic initial migration, including the `btree_gist` EXCLUDE constraint on Booking to prevent staff double-booking at the DB level.
4. [ ] Pydantic schemas (`apps/api/app/schemas/`) for all API-facing shapes.
5. [ ] Telegram `initData` verification (`apps/api/app/core/telegram_auth.py`) + demo-mode auth path + role/business-scoping dependency (`apps/api/app/core/authz.py`).
6. [ ] Availability engine (`apps/api/app/services/availability.py`) with real slot computation; unit tests for it before wiring to an endpoint.
7. [ ] Booking service (`apps/api/app/services/booking.py`): create/cancel/reschedule/status-transition, with transactional overlap-safety + idempotency keys.
8. [ ] API routers: businesses, services, staff, availability, bookings, my-bookings, auth.
9. [ ] Seed script: ATELIER demo business (services, staff, schedules, a few historical bookings).
10. [ ] docker-compose.yml + Dockerfiles + .env.example — bring up Postgres + API locally, run migrations, run seed, hit health endpoint.
11. [ ] Backend tests (pytest): initData validation, overlap prevention, concurrent booking race, timezone/DST, status transitions, business isolation. Run them; fix failures; record results in PROGRESS.md.
12. [ ] Frontend scaffold: `apps/web` — Vite + React + TS + Tailwind + shadcn/ui, design tokens from spec's palette, base layout, Telegram WebApp SDK + browser-demo-mode detection.
13. [ ] Frontend booking flow: business profile → service select → specialist select → calendar (real slots from API) → confirm → success.
14. [ ] Frontend My Appointments: tabs (upcoming/completed/cancelled), cancel, reschedule.
15. [ ] Telegram bot skeleton (`apps/bot`, aiogram 3.x): `/start /help /book /mybookings /support`, reply keyboard, Mini App launch button, polling entrypoint. Document BotFather setup; do not fabricate a live run since no token exists.
16. [ ] Wire frontend to real API end-to-end locally (docker compose up, open web app, do a full booking, verify in DB).
17. [ ] Update PROGRESS.md/ROADMAP.md/CHANGELOG.md with what was actually verified; commit and push to `Aydenxvi/bookflow`.
18. [ ] Report back to the user with what's runnable and how to try it, and what Phase 3+ would need.

Items 1–17 constitute the agreed Phase 1 + 2 scope for this session.
