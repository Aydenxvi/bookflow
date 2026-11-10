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
Run for real (postgres, api, web, worker all up together via `docker compose up`) and fixed two bugs that run turned up: a worker packaging issue and a hardcoded CORS allowlist — see `CHANGELOG.md`.

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

## Deploying to a real VPS

This runs the exact same `docker-compose.yml` as local dev — no code rewrite, no serverless split, no webhook — on a real server so the bot and API stay online 24/7. The bot keeps using long-polling (it only needs outbound internet access), and a small Caddy reverse proxy (`infrastructure/caddy/Caddyfile`) is added just to get free automatic HTTPS, which Telegram's Mini App webview requires.

**1. Get a free, always-on VPS.** [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/) includes a small VM that's free forever (not a trial), with a real public IP — this is the recommended option over sleep-on-idle PaaS platforms (Render/Railway-style free tiers), which stop long-running processes like a continuously polling bot or worker. Create an Ubuntu instance and note its public IP.

**2. Get a free hostname for it.** Let's Encrypt (for HTTPS) and Telegram both require a real hostname, not a bare IP. The fastest option needs no signup: `<your-ip-with-dots-replaced-by-dashes>.sslip.io` — e.g. IP `203.0.113.10` → `203-0-113-10.sslip.io` — already resolves to that IP. (Or get a nicer name for free via [DuckDNS](https://www.duckdns.org/).)

**3. On the VPS**, open only ports 22 (SSH), 80, and 443 in its firewall/security list, then:

```bash
# Install Docker + Compose plugin (Ubuntu)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker

git clone https://github.com/<your-username>/bookflow.git
cd bookflow
cp .env.example .env
```

**4. Edit `.env`** on the VPS:
- `DOMAIN=` your sslip.io or DuckDNS hostname from step 2
- `ENVIRONMENT=production`
- `CORS_ALLOW_ORIGINS=["https://<your-domain>"]`
- `TELEGRAM_BOT_TOKEN=` your real token from @BotFather
- `VITE_API_BASE_URL=https://<your-domain>` (no trailing `/api` — the frontend's API client already adds that path)
- Change `JWT_SECRET`, `POSTGRES_PASSWORD` away from the dev defaults

**5. Bring up the full stack**, including the `prod` (Caddy) and `bot` profiles:

```bash
docker compose --profile prod --profile bot up -d --build
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m app.seed   # optional — loads the ATELIER demo business
```

Caddy requests and renews its own Let's Encrypt certificate automatically on first request to `DOMAIN` — give it a minute, then check `https://<your-domain>/health`.

**6. Point the Mini App at it.** In Telegram, message @BotFather → your bot → **Bot Settings → Menu Button → Edit Menu Button URL** → set it to `https://<your-domain>/`. Open your bot in Telegram and the menu button now launches the real Mini App over HTTPS, backed by the same booking engine as the browser demo.

To ship an update later: `git pull && docker compose --profile prod --profile bot up -d --build`.

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
