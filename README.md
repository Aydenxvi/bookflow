# BookFlow

**Bookings made effortless.**

A Telegram-first appointment-booking platform. Customers book services through a Telegram Mini App (or a browser demo mode); business owners manage services, staff, schedules and appointments through a web admin dashboard.

> Status: early build (Phase 1–2 of 5 — foundation + booking MVP). See `PROGRESS.md`, `ROADMAP.md`, `NEXT_STEPS.md` for exact status, and `CLAUDE.md` for architecture and how to resume work on this project.

## Stack

- **API**: FastAPI, SQLAlchemy 2.x (async), PostgreSQL, Alembic, Pydantic v2
- **Web** (Mini App + Admin): React, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query, React Hook Form + Zod, date-fns, Recharts
- **Bot**: Python 3.12+, aiogram 3.x
- **Worker**: Postgres-backed idempotent notification job runner
- **Infra**: Docker Compose

## Local development

```bash
cp .env.example .env            # fill in values; see comments in the file
docker compose up -d postgres
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m app.seed       # loads the ATELIER demo business
docker compose up -d api web
```

- API: http://localhost:8000 (docs at `/docs`)
- Web (browser demo mode): http://localhost:5173

No Telegram bot token is required to try the booking flow — opening `apps/web` outside of Telegram automatically switches to **browser demo mode**, scoped to the seeded demo business, so the real booking engine can be exercised without a Telegram account.

### Running the Telegram bot

Requires a bot token from [@BotFather](https://t.me/BotFather). See `docs/` (added as the bot is wired up) for the exact BotFather steps and how to point the Mini App button at your deployed `apps/web` URL. Not configured in this repository yet — no token was available when this was built.

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
