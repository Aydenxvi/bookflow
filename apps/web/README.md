# BookFlow — Web

React 19 + TypeScript + Vite + Tailwind CSS v4. The Telegram Mini App
(customer booking flow + "My Appointments") lives here; the business admin
dashboard is Phase 3 and not built yet (see repo root `NEXT_STEPS.md`).

## Running locally

```bash
npm install
npm run dev
```

Opens on http://localhost:5173. By default it talks to the API at
http://localhost:8000 — start that first (see `apps/api/README` /
root `README.md`) and seed the demo business with `python -m app.seed`.

No Telegram account is needed to try it: outside of Telegram's own WebApp
container, the app automatically falls back to browser demo mode (calls
`/api/v1/auth/demo` instead of `/api/v1/auth/telegram`) scoped to the seeded
**ATELIER — Modern Grooming Studio** business. A green "Demo mode" banner
confirms this at the top of the screen.

## What's here

- `src/lib/telegram.ts` — typed wrapper over `window.Telegram.WebApp` and the
  Telegram-vs-demo-mode detection used by `src/lib/auth.tsx`.
- `src/lib/api-client.ts` + `src/lib/api-types.ts` — typed fetch wrapper and
  hand-written mirrors of the backend's Pydantic schemas (kept in sync by
  hand for now — see `NEXT_STEPS.md` for generating these instead).
- `src/lib/queries.ts` — TanStack Query hooks over the API client.
- `src/components/ui/` — small UI primitives written in the shadcn/ui style
  directly against Radix UI primitives + `class-variance-authority` (the
  `shadcn` CLI's registry endpoint, `ui.shadcn.com`, is not reachable from
  this project's build sandbox, so these were hand-written to the same
  pattern rather than generated — functionally and stylistically equivalent).
- `src/pages/` — the booking flow (`HomePage` → `SpecialistPage` →
  `DateTimePage` → `ConfirmPage` → `SuccessPage`) and `AppointmentsPage`
  ("My Appointments", with cancel/reschedule).

## Verified

This has been driven end-to-end with a real headless browser (Playwright)
against the real local API + Postgres — not just type-checked. See
`PROGRESS.md` at the repo root for exactly what was run and what it covered
(both the "any available specialist" path and picking a named specialist,
booking, cancelling, and rescheduling).

## Environment variables

See `.env.example`. Optional — the defaults match the local dev API.
