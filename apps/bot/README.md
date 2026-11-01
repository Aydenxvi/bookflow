# BookFlow — Telegram Bot

aiogram 3.x. Deliberately thin: its only job is getting a customer into the
Mini App (`/start`, `/book`, `/mybookings`, `/support`, `/help`, and the
reply-keyboard buttons). All booking logic lives in `apps/web` talking to
`apps/api` — the bot never touches the database directly.

## Status: structural only, not run against real Telegram servers

No bot token was available in the environment this was built in. The code
has been reviewed line-by-line against aiogram 3.x's documented API and
verified to **import cleanly and register all 7 handlers** with a real
install of the `aiogram` package (not mocked) — see `PROGRESS.md` at the
repo root for the exact command run. Running `python -m app.main` without a
token fails fast with a clear message rather than pretending to start.
Actual long-polling against Telegram's servers has never been exercised.

## Setting up a real bot (once you have a token)

1. Message [@BotFather](https://t.me/BotFather) on Telegram, send `/newbot`,
   follow the prompts. You'll get a token like `123456:ABC-DEF...`.
2. Still in BotFather: `/mybots` → your bot → **Bot Settings** → **Menu
   Button** → set it to a Web App pointing at your deployed `apps/web` URL.
   This is what makes "Open BookFlow" launch the Mini App instead of just
   sending a link.
3. Also in BotFather, `/setcommands` on your bot and paste:
   ```
   book - Book a new appointment
   mybookings - View your appointments
   support - Contact support
   help - Show available commands
   ```
4. Copy `.env.example` to `.env`, fill in `BOT_TOKEN` (from step 1) and
   `MINI_APP_URL` (your deployed `apps/web` URL — must be `https://`;
   Telegram rejects plain `http://` WebApp URLs outside of local testing
   via BotFather's test environment).
5. `pip install -e .` then `python -m app.main` to start polling locally.

## Running

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env   # fill in BOT_TOKEN and MINI_APP_URL
python -m app.main
```
