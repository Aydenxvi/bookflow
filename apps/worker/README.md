# BookFlow — Notification Worker

Polls `notification_jobs` (written by `apps/api`'s booking-lifecycle hooks —
see `apps/api/app/services/notifications.py`) and sends each one over
Telegram's raw Bot API. No in-memory scheduler: a reminder is just a row
with a future `scheduled_for`, picked up by the same ordinary poll loop as
everything else — see repo root `CLAUDE.md`.

A separate deployable service (own `pyproject.toml`/`Dockerfile`, built from
its own directory, same pattern as `apps/bot`). It does **not** import
`apps/api`'s ORM package — see `app/tables.py`'s module docstring for why —
so it declares its own thin SQLAlchemy Core view of exactly the columns it
reads or writes on the same tables `apps/api`'s Alembic migrations own.

## Status: claim/retry/render logic verified against real PostgreSQL; actual Telegram delivery never exercised

No Telegram bot token was available in this environment (same constraint as
`apps/bot` — see repo root `PROGRESS.md`). What **has** been verified, all
against a real PostgreSQL database (`bookflow_worker_test`), not mocked:

- 25 pytest tests covering: `SELECT ... FOR UPDATE SKIP LOCKED` claiming
  (including that two concurrent transactions claiming at once never get the
  same row), retry/backoff math and the terminal `FAILED` transition at
  `MAX_ATTEMPTS`, message rendering for every job type, and
  `BUSINESS_DAILY_SUMMARY` enqueueing (idempotent per business per day,
  respects `notify_business_daily_summary`, skips blocked/missing Telegram
  identities and non-owner/manager roles).
- The actual Telegram HTTP call (`app/telegram_client.py::send_message`) is
  mocked in `test_worker_integration.py`; everything *around* it — claiming,
  rendering from live booking data, marking SENT/retry/FAILED — is real.
- A cross-service smoke test (not checked in — it's not an automated test,
  just a one-off verification step this was built with): created a real
  booking through `apps/api`'s own `create_booking()` against the live
  `bookflow` database (with a real `TelegramIdentity`-linked customer and
  business owner), confirmed the resulting `notification_jobs` rows looked
  exactly as expected (`BOOKING_CONFIRMED`, `BUSINESS_NEW_BOOKING`, three
  `REMINDER`s at the policy's configured 24h/2h/30m offsets), then ran this
  worker's actual `process_one()` against those exact rows and confirmed it
  claimed the two due jobs, correctly failed them without crashing (no bot
  token configured) with a clear `last_error`, and rescheduled them with
  backoff — proving this package's hand-kept schema mirror in `app/tables.py`
  actually matches what `apps/api`'s ORM/Alembic produces, not just its own
  self-created test schema.
- **Not verified**: an actual `sendMessage` call reaching Telegram's real
  servers. `python -m app.main` without `TELEGRAM_BOT_TOKEN` set still runs
  the full loop — every send attempt fails fast with a clear error and goes
  through the normal retry path rather than crashing — but nothing is
  actually delivered until a real token is configured.

## Running

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # fill in DATABASE_URL and TELEGRAM_BOT_TOKEN
python -m app.main
```

## Testing

Needs its own test database once (separate from `apps/api`'s
`bookflow_test` — this package doesn't share schema-creation code with it,
see `tests/conftest.py`):

```bash
createdb -U bookflow bookflow_worker_test
pip install -e ".[dev]"
pytest
```

## Getting a real bot token

Same bot as `apps/bot` uses — see `apps/bot/README.md` for the full
`@BotFather` setup. This worker only needs the same `TELEGRAM_BOT_TOKEN` in
its own `.env`.

## Design notes

- **Retry/backoff**: a failed send increments `attempts` and reschedules
  `scheduled_for` with exponential backoff (`BACKOFF_BASE_SECONDS *
  2**attempts`, capped at `BACKOFF_MAX_SECONDS`) until `MAX_ATTEMPTS`, at
  which point the job becomes `FAILED` (terminal — see
  `NotificationJobStatus` in `apps/api`).
- **One job, one transaction**: each claimed job is rendered and sent inside
  the same transaction that holds its row lock, then committed. If the
  process crashes mid-send, the lock releases with the connection and the
  job is still `PENDING` for the next poll — see `app/claim.py`'s docstring
  for why this is simpler and safer here than introducing an undocumented
  "processing" status.
- **Daily summaries** (`app/daily_summary.py`): each poll cycle checks
  whether "the next" `BUSINESS_DAILY_SUMMARY` job for each opted-in business
  already exists (by `dedupe_key`) and inserts it if not — no persistent
  scheduler state, the dedupe key and `scheduled_for` do all the work.
