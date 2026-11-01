# NEXT_STEPS.md — Exact Next Tasks

Ordered. Pick up at the first unchecked item.

## Phase 1 + Phase 2 — done for this session's agreed scope
Backend, frontend, and a Telegram bot skeleton are all built and verified —
see PROGRESS.md for exactly what was run and checked (27/27 backend
pytest, a real headless-browser click-through of the full booking flow
twice over, bot handlers import/register-verified). Remaining items below
are follow-ups, not blockers.

## Immediate next (in order)

1. [x] Frontend scaffold, design tokens, booking flow screens, My Appointments, Telegram SDK + demo-mode detection.
2. [x] Typed API client + TanStack Query hooks.
3. [x] End-to-end manual (headless-browser) run against the local API in demo mode — two bugs found this pass are already fixed (see CHANGELOG.md: the seed-script reseed `IntegrityError`, and nothing on the frontend side needed fixing after the first pass).
4. [x] Telegram bot skeleton (`apps/bot`) — structural/documented, not run live (no token).
5. [x] Update PROGRESS.md/ROADMAP.md/CHANGELOG.md with what was actually verified.
6. [ ] Commit and push this checkpoint to `Aydenxvi/bookflow`.
7. [ ] Report back to the user: what's runnable right now and how to try it, what was verified vs. not, and what Phase 3+ would need.

## Worth doing in a future session, not blocking

- **Exercise `docker compose up` for real** on a machine/CI with a Docker daemon (none is available in this sandbox — Postgres was run natively and the frontend with `npm run dev`/`vite build` directly). The compose file and all three Dockerfiles (`api`, `web`, `bot`) are written to the same standard as the rest of the code but have never themselves been built/run.
- **Get a real Telegram bot token** (via @BotFather — see `apps/bot/README.md`) to actually verify the bot against live Telegram: the reply keyboard, the WebApp Menu Button, and real `initData` flowing into the already-tested backend verification code.
- **Retry the `shadcn` CLI** if this project ever moves to an environment where `ui.shadcn.com` isn't blocked — not required (the hand-written primitives in `apps/web/src/components/ui/` are complete and working), but it's the more typical way to add further shadcn components later.
- Consider generating `apps/web/src/lib/api-types.ts` from the backend's OpenAPI schema instead of hand-maintaining it, now that there's real drift risk as the API grows.

## Known gaps to flag honestly, not paper over
- Rate limiting is in-process only (documented in `app/core/rate_limit.py` and CLAUDE.md) — fine for one API replica, not for a multi-replica deployment.
- No notification worker yet — `NotificationJob` rows are modeled but nothing creates or consumes them yet (that's Phase 4).
- No admin/business-side UI at all yet (Phase 3) — business owners currently have no way to manage services/staff/schedules except direct DB/seed-script edits.
- The Telegram bot has never been run against real Telegram servers (see above).
