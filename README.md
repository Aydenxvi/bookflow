# BookFlow

**Bookings made effortless.**

A Telegram-first appointment-booking platform. Customers book services through a Telegram Mini App (or a browser demo mode); business owners manage services, staff, schedules and appointments through a web admin dashboard.

> Status: Phases 1–4 of 5 done — foundation, a working booking MVP, a full admin dashboard, and automation (Telegram notifications, a reminder worker, status history, analytics). Phase 5 (multi-business onboarding, i18n, deployment polish) not started. See `PROGRESS.md`, `ROADMAP.md`, `NEXT_STEPS.md` for exact status, and `CLAUDE.md` for architecture and how to resume work on this project.

## Stack

- **API**: FastAPI, SQLAlchemy 2.x (async), PostgreSQL, Alembic, Pydantic v2
- **Web** (Mini App + Admin): React, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query, React Hook Form + Zod, date-fns, Recharts
- **Bot**: Python 3.12+, aiogram 3.x
- **Worker**: Postgres-backed idempotent notification job runner
- **Infra**: Docker Compose

## Local development

### Via Docker Compose
(Written to the same standard as everything else here, but — unlike the two commands below — **not itself exercised** in the sandbox this was built in, which has no Docker daemon. Worth a first real run before relying on it.)

```bash
cp .env.example .env            # fill in values; see comments in the file
docker compose up -d postgres
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m app.seed       # loads the ATELIER demo business
docker compose up -d api web worker                  # worker is included by default
```

The Telegram bot (`apps/bot`) is opt-in since it fails fast without a real `BOT_TOKEN`: `docker compose --profile bot up -d bot`.

### Without Docker (what was actually run and verified this session)

```bash
# Postgres running natively, with the btree_gist extension available
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # point DATABASE_URL at your local Postgres
alembic upgrade head
python -m app.seed              # loads the ATELIER demo business; safe to re-run
uvicorn app.main:app --reload   # http://localhost:8000 (docs at /docs)

# in another terminal
cd apps/web
npm install
npm run dev                     # http://localhost:5173

# in a third terminal — optional, but needed to actually see notifications/reminders enqueue and get picked up
cd apps/worker
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # point DATABASE_URL at the same Postgres as apps/api
python -m app.main
```

No Telegram bot token is required to try the booking flow — opening `apps/web` outside of Telegram automatically switches to **browser demo mode** (a green banner confirms it), scoped to the seeded demo business, so the real booking engine can be exercised end-to-end without a Telegram account. This exact path — demo auth → browse → book → My Appointments → cancel/reschedule — has been driven with a real headless browser against this exact setup; see `PROGRESS.md`.

**Admin dashboard**: open `http://localhost:5173/admin` — it signs you in automatically with a demo-admin token scoped to the same seeded ATELIER business (no separate setup). From there: Dashboard, Calendar (manual bookings, status changes, status history), Services, Staff, Settings, and Analytics.

Without a real `TELEGRAM_BOT_TOKEN` set, the worker still runs its full claim/retry loop — it just logs each send attempt failing cleanly (no token to call Telegram's API with) rather than crashing. Enqueued jobs, retries, and the daily-summary scheduling are all still real and inspectable in the `notification_jobs` table; only the actual Telegram delivery is unverified without a token.

### Running the Telegram bot

Structurally complete (`apps/bot`) but **never run against real Telegram servers** — no bot token was available when this was built. See `apps/bot/README.md` for the exact BotFather steps (including pointing the Mini App Menu Button at your deployed `apps/web` URL) once you have one:

```bash
cd apps/bot
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env            # fill in BOT_TOKEN and MINI_APP_URL
python -m app.main
```

## Project structure

```
apps/
  web/      Telegram Mini App + admin dashboard (React/TS/Vite)
  api/      Backend (FastAPI)
  bot/      Telegram bot (aiogram)
  worker/   Notification worker
packages/
  shared/   Shared TS types/constants
docs/       Architecture notes, original spec
infrastructure/
```

## License

Private portfolio project.
