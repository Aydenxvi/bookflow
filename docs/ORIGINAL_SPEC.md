# Original Project Specification (verbatim)

This is the exact original brief the project was commissioned from, kept for traceability per its own "persistent progress system" requirement (section 24: a future session should never need to ask for the spec to be resent). `CLAUDE.md` records what was actually decided and built; where the two disagree, `CLAUDE.md` reflects reality, and deviations are logged in `CHANGELOG.md`.

---

# BOOKFLOW — PREMIUM TELEGRAM BOOKING PLATFORM
## Complete Full-Stack Development, Telegram Mini App, Admin Dashboard & Persistent Project Recovery

You are an expert full-stack software engineer, Telegram Bot developer, SaaS architect, UI/UX designer, database engineer, and quality assurance specialist.

Your mission is to autonomously design, develop, test, and polish **BOOKFLOW**, a professional appointment-booking platform built around Telegram.

This is a serious, portfolio-quality software project that should also have the potential to become a real subscription-based SaaS product for small businesses.

Your responsibility is to CREATE THE ACTUAL WORKING PROJECT.

Do not stop at conceptual designs, mockups, pseudocode, or architecture documents.

Build the frontend, backend, Telegram bot, database, scheduling engine, notification system, and business administration interface.

Make reasonable engineering decisions independently.

Prioritize excellent user experience, correct booking logic, secure architecture, and real end-to-end functionality.

---

# 1. PRODUCT VISION

BOOKFLOW is a modern booking solution that enables customers to schedule appointments directly through Telegram.

Target businesses:

- Barbershops.
- Beauty salons.
- Nail studios.
- Massage studios.
- Private tutors.
- Fitness coaches.
- Photography studios.
- Consulting businesses.
- Small service companies.

The platform must provide two distinct experiences.

## CUSTOMER EXPERIENCE

A beautifully designed Telegram Mini App where customers can:

- Explore a business.
- Browse available services.
- Choose a specialist.
- View available dates and times.
- Book an appointment.
- View upcoming appointments.
- Reschedule appointments.
- Cancel appointments.
- Receive Telegram notifications.
- Review past appointments.

## BUSINESS EXPERIENCE

A professional administration dashboard where business owners and authorized staff can:

- Manage business information.
- Configure services and pricing.
- Manage employees.
- Configure working schedules.
- View appointments.
- Manually create appointments.
- Accept or reject booking requests.
- Block unavailable dates.
- Manage cancellations.
- Track statistics.
- Export booking data.
- Configure automatic notifications.

The application must feel like a real commercial product, not a beginner coding exercise.

---

# 2. REQUIRED TECHNOLOGY STACK

## Frontend

Use:

- React.
- TypeScript.
- Vite.
- Tailwind CSS.
- shadcn/ui.
- Lucide React.
- Motion / Framer Motion.
- TanStack Query.
- React Hook Form.
- Zod.
- date-fns.
- Recharts for dashboard analytics.

## Telegram Bot

Use:

- Python 3.12+.
- aiogram 3.x.
- Telegram Bot API.
- Telegram Mini Apps SDK or the official WebApp interface.

## Backend

Use:

- FastAPI.
- SQLAlchemy 2.x with async support.
- PostgreSQL.
- Alembic migrations.
- Pydantic.
- Structured logging.

## Background Processing

Implement a reliable background worker for scheduled notifications.

Use PostgreSQL-backed notification jobs with an idempotent worker, or an equivalent robust solution.

Do not rely on an in-memory scheduler for production-critical reminders.

## Development Infrastructure

- Docker Compose.
- Environment variables.
- .env.example.
- Database migrations.
- Seed/demo data.
- Automated tests.

Keep dependencies compatible and maintained.

Organize the project as a clean monorepo.

Suggested structure:

bookflow/
- apps/
  - web/
  - bot/
  - api/
  - worker/
- packages/
  - shared/
- docs/
- infrastructure/
- AGENTS.md
- PROGRESS.md
- ROADMAP.md
- NEXT_STEPS.md
- README.md
- docker-compose.yml

You may adjust the structure if a different organization is technically superior.

---

# 3. BRAND IDENTITY AND VISUAL DIRECTION

Brand name: BOOKFLOW.

Tagline: "Bookings made effortless."

BOOKFLOW must have a premium, elegant, minimal, welcoming aesthetic.

It should feel like a carefully designed digital product for contemporary service businesses.

## Visual Personality

- Refined.
- Minimal.
- Professional.
- Warm.
- Trustworthy.
- Modern.
- Elegant.
- Calm.
- Intuitive.

## Suggested Palette

Primary:
- Warm white.
- Soft ivory.
- Natural beige.
- Deep charcoal.

Accents:
- Muted sage green.
- Soft olive.
- Restrained emerald.

Secondary:
- Light gray.
- Warm stone.
- Subtle neutral borders.

Avoid:
- Cyberpunk aesthetics.
- Excessive gradients.
- Generic AI-looking interfaces.
- Oversized rounded cards everywhere.
- Unnecessary glassmorphism.
- Cluttered layouts.
- Aggressive animations.

## Typography

Use modern, readable typography.

Suggested fonts:
- Manrope.
- Inter.
- DM Sans.

Use an elegant editorial font for selective large headings if appropriate.

## Design Quality

Every page must have:

- Carefully designed spacing.
- Consistent typography.
- Beautiful interactive elements.
- Clear visual hierarchy.
- Smooth microinteractions.
- Appropriate hover and pressed states.
- Elegant loading skeletons.
- Meaningful empty states.
- Helpful error messages.
- Beautiful confirmation screens.

The interface should look and feel like a real premium SaaS application.

---

# 4. TELEGRAM BOT

Create a real working Telegram bot.

## Bot Commands

/start
/help
/book
/mybookings
/support

## Main Menu

Provide the following reply keyboard:

- Open BookFlow.
- My Appointments.
- How It Works.
- Contact Support.

Configure a Telegram menu button to open the Mini App when supported.

## Start Experience

When a user starts the bot:

1. Welcome the user.
2. Explain the booking service briefly.
3. Provide a prominent button to launch BookFlow.
4. Allow access to existing appointments.
5. Provide help and support navigation.

Avoid sending excessive messages.

Use concise and professional copy.

## Bot Functionality

The bot must:

- Recognize Telegram users.
- Open the Mini App.
- Handle supported commands.
- Show appointment summaries.
- Send booking confirmations.
- Send cancellation notifications.
- Send rescheduling notifications.
- Send appointment reminders.
- Notify staff of relevant changes.

Use Telegram deep links to identify a specific business when necessary.

Design for multiple businesses using a single platform.

---

# 5. TELEGRAM MINI APP

Create an exceptionally polished, mobile-first Telegram Mini App.

The Mini App must integrate with Telegram's official WebApp APIs.

Support:

- Telegram theme integration.
- Light and dark modes.
- Safe-area insets.
- Appropriate viewport handling.
- Haptic feedback where available.
- Native-feeling interactions.
- Telegram Back Button integration where appropriate.
- Smooth screen transitions.
- Loading and error states.

Do not rely exclusively on client-side Telegram user information for authentication.

Verify Telegram initData securely on the backend according to the official protocol, including signature and freshness validation.

Never treat initDataUnsafe as trusted authentication data.

Provide a separate local browser demo mode for development and portfolio presentation.

---

# 6. CUSTOMER BOOKING EXPERIENCE

Create the complete booking flow.

## STEP 1 — BUSINESS PROFILE

Display:

- Business name.
- Logo.
- Cover image.
- Short description.
- Address.
- Contact information.
- Business hours.
- Available services.
- Available specialists.

Use realistic fictional data in demo mode.

## STEP 2 — SELECT SERVICE

Display beautiful service cards.

Each service contains:

- Name.
- Description.
- Price.
- Duration.
- Optional image.
- Category.
- Available specialists.

Users must be able to select a service easily.

## STEP 3 — SELECT SPECIALIST

Display available staff members.

Each profile includes:

- Name.
- Photo.
- Specialization.
- Short biography.
- Available services.

Provide an "Any available specialist" option.

The selected specialist must affect the available appointment slots.

## STEP 4 — SELECT DATE AND TIME

Build a beautiful interactive calendar.

Features:

- Horizontal date selector.
- Monthly calendar navigation.
- Available time slots.
- Disabled unavailable dates.
- Clear selected state.
- Smooth transitions.

Available slots must come from the real backend scheduling engine.

Do not hardcode available times.

## STEP 5 — CONFIRMATION

Display a booking summary:

- Business.
- Service.
- Specialist.
- Date.
- Time.
- Duration.
- Price.

Allow customers to enter relevant booking notes.

Request only personal information that is genuinely necessary.

Require confirmation before creating the appointment.

## STEP 6 — SUCCESS SCREEN

Display an elegant confirmation screen showing:

- Booking confirmation.
- Appointment details.
- Status.
- Instructions.
- Button to view appointments.

Send a Telegram confirmation when possible.

---

# 7. MY APPOINTMENTS

Implement a complete appointment management section.

Tabs:

- Upcoming.
- Completed.
- Cancelled.

Each appointment card includes:

- Service.
- Specialist.
- Date.
- Time.
- Booking status.
- Business information.

Actions:

- View details.
- Reschedule.
- Cancel.

Apply configurable cancellation and rescheduling policies.

Do not allow customers to modify appointments that do not belong to them.

Provide clear success and failure feedback.

---

# 8. BUSINESS ADMIN DASHBOARD

Create a separate, responsive administrative interface.

It must work well on desktop, tablet, and mobile.

## Dashboard Overview

Show:

- Today's appointments.
- Upcoming appointments.
- Completed appointments.
- Cancelled appointments.
- Booking trends.
- Popular services.
- Specialist workload.
- Revenue estimates based on completed bookings.

Never label estimates as verified payments.

## Appointment Calendar

Implement:

- Daily view.
- Weekly view.
- Calendar navigation.
- Appointment cards.
- Status indicators.
- Staff filters.
- Service filters.
- Appointment details.
- Manual appointment creation.
- Status changes.
- Cancellation handling.

Ensure calendar updates reflect actual database changes.

## Appointment Management

Statuses:

- Pending.
- Confirmed.
- Completed.
- Cancelled.
- No-show.

Allow the business to choose automatic confirmation or manual approval.

Define valid status transitions.

Store appointment history and relevant timestamps.

---

# 9. SERVICE MANAGEMENT

Business owners must be able to:

- Create services.
- Edit services.
- Archive services.
- Change prices.
- Change durations.
- Assign specialists.
- Organize service categories.
- Configure booking availability.

Each service should support:

- Name.
- Description.
- Duration.
- Price.
- Currency.
- Category.
- Active/inactive status.

Use proper validation.

Archived services must not destroy historical booking records.

---

# 10. STAFF MANAGEMENT

Create a full staff management system.

Features:

- Add staff members.
- Edit employee profiles.
- Assign services.
- Set working hours.
- Set breaks.
- Define days off.
- Set temporary leave.
- Control availability.
- View individual calendars.

Support roles:

- Platform administrator.
- Business owner.
- Business manager.
- Staff member.
- Customer.

Role access must be enforced on the backend.

Employees should only access data their role permits.

---

# 11. BOOKING AVAILABILITY ENGINE — CRITICAL

This is one of the most important technical systems.

Implement a reliable appointment scheduling engine.

Available time slots must consider:

- Business operating hours.
- Employee working hours.
- Employee breaks.
- Existing appointments.
- Service duration.
- Buffer time.
- Holidays.
- Special closures.
- Employee leave.
- Minimum booking notice.
- Maximum advance booking window.
- Business timezone.

Store timestamps consistently and handle timezone conversion correctly.

Support daylight-saving-time transitions.

Prevent double bookings.

## Concurrency Safety

Two customers must not be able to book the same specialist for overlapping times.

Availability checks in the frontend are not sufficient.

Implement a database-enforced or transactionally safe booking strategy using PostgreSQL.

Revalidate availability immediately before confirming any appointment.

Prevent overlaps based on the actual service duration and applicable buffer time.

Protect against race conditions.

Use idempotency keys for booking creation where appropriate.

Apply the same rules to manual admin bookings and rescheduling.

## Booking Rules

Support:

- Configurable slot intervals.
- Service-specific durations.
- Staff-specific schedules.
- Multiple staff members.
- Booking lead times.
- Cancellation windows.
- Rescheduling windows.

The system must provide correct results rather than visually simulated availability.

---

# 12. NOTIFICATION SYSTEM

Implement automated Telegram notifications.

## Customer Notifications

- Booking received.
- Booking confirmed.
- Booking rejected.
- Booking cancelled.
- Booking rescheduled.
- Appointment reminder.

## Business Notifications

- New booking.
- Cancellation.
- Rescheduling.
- Upcoming appointment summary.

## Reminder Scheduling

Support configurable reminders such as:

- 24 hours before.
- 2 hours before.
- 30 minutes before.

Business owners should be able to configure reminder timing.

Notifications must be:

- Persistent.
- Retryable.
- Idempotent.
- Logged.
- Timezone-aware.

Prevent duplicate reminders.

Handle Telegram API errors gracefully, including users who have blocked the bot.

Do not let a failed message corrupt appointment data.

---

# 13. MULTI-BUSINESS ARCHITECTURE

BOOKFLOW should be designed as a reusable platform.

Support multiple independent businesses.

Each business has:

- Its own profile.
- Services.
- Staff.
- Schedule.
- Appointments.
- Settings.
- Customers.
- Notification preferences.

Prevent data leakage between businesses.

Use business ownership and role-based authorization.

A customer may book appointments with multiple businesses.

Keep the first working version simple while preserving the correct multi-tenant architecture.

Do not implement paid subscriptions or billing unless the core application is already stable.

---

# 14. ANALYTICS

Build a professional analytics dashboard.

Include:

- Bookings by day.
- Bookings by week.
- Monthly booking volume.
- Cancellation rate.
- No-show rate.
- Most popular services.
- Specialist workload.
- Estimated service revenue.

Use Recharts.

Provide interactive filters.

All analytics must use actual stored records.

Handle empty datasets gracefully.

---

# 15. SETTINGS

Create business settings for:

- Business name.
- Description.
- Contact details.
- Address.
- Timezone.
- Currency.
- Operating hours.
- Booking confirmation mode.
- Booking policies.
- Reminder timing.
- Notification preferences.
- Business branding.

Keep configuration centralized and maintainable.

---

# 16. MULTILINGUAL SUPPORT

Prepare the platform for international use.

Support:

- English.
- Russian.
- Turkish.

Use centralized translation files.

Avoid hardcoding interface strings throughout the frontend.

Choose the initial language using Telegram language information when appropriate, while allowing users to change it manually.

---

# 17. DATABASE ARCHITECTURE

Design a relational PostgreSQL database.

Suggested entities:

- User.
- TelegramIdentity.
- Business.
- BusinessMembership.
- Staff.
- Service.
- StaffService.
- WorkingSchedule.
- ScheduleException.
- Booking.
- BookingStatusHistory.
- BookingPolicy.
- NotificationJob.
- BusinessSettings.

Add additional entities where necessary.

Implement:

- Foreign keys.
- Appropriate indexes.
- Database migrations.
- Referential integrity.
- Tenant isolation.
- Transactional booking operations.
- Correct uniqueness and overlap constraints.

Use Decimal or exact integer minor units for prices.

Never use floating-point arithmetic for financial values.

---

# 18. SECURITY

Implement:

- Secure Telegram authentication verification.
- Server-side role authorization.
- Business-level data isolation.
- Request validation.
- Secure environment variables.
- Rate limiting on sensitive endpoints.
- Protection against duplicate booking requests.
- Safe error handling.
- Secure webhook handling.
- Appropriate CORS policy.
- Audit logging for important administrative actions.

Never expose the Telegram bot token to the frontend.

Do not commit credentials.

Never trust client-provided prices, permissions, booking statuses, or staff availability.

The backend must verify all sensitive actions.

---

# 19. PORTFOLIO DEMO MODE

This project must be easy for recruiters and potential clients to explore.

Create a public demo experience.

Use a fictional example business, such as:

**ATELIER — Modern Grooming Studio**

Provide:

- Sample services.
- Sample employees.
- Example working schedules.
- Demo appointments.
- Attractive business imagery.
- Functional booking demonstrations.
- A sample admin dashboard.

Allow visitors to test the booking flow without needing a real Telegram account.

Keep demo data completely isolated from production.

Use safe, resettable demo data or simulated demo writes.

Clearly label demo behavior.

Never present demo bookings as real reservations.

---

# 20. TESTING

Implement automated tests.

Backend:

- Telegram authentication validation.
- Invalid authentication rejection.
- Role permission checks.
- Business isolation.
- Slot generation.
- Overlapping booking prevention.
- Concurrent booking attempts.
- Cancellation policies.
- Rescheduling.
- Timezone correctness.
- Reminder idempotency.
- Booking status transitions.

Frontend:

- Navigation.
- Service selection.
- Specialist selection.
- Calendar interactions.
- Booking confirmation.
- Appointment cancellation.
- Responsive layouts.
- Admin forms.

Test critical end-to-end workflows.

Do not claim that a feature works without actually verifying it.

---

# 21. DEPLOYMENT

Prepare the project for real deployment.

Provide:

- Docker Compose configuration.
- Backend Dockerfile.
- Bot Dockerfile or equivalent service configuration.
- Frontend production build.
- Database migration commands.
- Environment variable documentation.
- Webhook setup instructions.
- HTTPS configuration guidance.
- Worker deployment instructions.
- Health-check endpoints.

Keep local development straightforward.

Use polling for convenient local bot development when appropriate.

Use secure webhooks for production deployment.

Do not enable polling and webhook update delivery simultaneously.

Document setup through BotFather.

Provide a clear guide for connecting the deployed Mini App URL to the Telegram bot.

Never claim deployment was completed unless it actually occurred.

---

# 22. DEVELOPMENT ROADMAP

Complete the project incrementally.

## PHASE 1 — FOUNDATION

- Initialize repository.
- Configure backend.
- Configure frontend.
- Configure Telegram bot.
- Configure PostgreSQL.
- Implement database migrations.
- Establish design system.
- Create application layouts.
- Implement basic Telegram authentication.
- Add demo mode foundation.

## PHASE 2 — BOOKING MVP

- Business profile.
- Service selection.
- Staff selection.
- Availability calendar.
- Booking creation.
- Booking confirmation.
- My appointments.
- Cancellation.
- Real database persistence.

This phase must deliver a working end-to-end booking flow.

## PHASE 3 — ADMINISTRATION

- Owner dashboard.
- Service management.
- Staff management.
- Work schedules.
- Appointment calendar.
- Manual booking management.
- Booking policies.

## PHASE 4 — AUTOMATION

- Telegram notifications.
- Scheduled reminders.
- Rescheduling.
- Booking status history.
- Retryable notification jobs.
- Business analytics.

## PHASE 5 — COMMERCIAL READINESS

- Multi-business onboarding.
- Advanced settings.
- Internationalization.
- Responsive polishing.
- UI animations.
- Demo enhancements.
- Security tests.
- Deployment configuration.
- Documentation.

Do not sacrifice correctness of the core booking engine to implement advanced decorative features.

---

# 23. AUTONOMOUS EXECUTION

You are an implementation agent.

You must:

1. Inspect the repository.
2. Create a plan.
3. Start coding.
4. Create real source files.
5. Install necessary dependencies when possible.
6. Configure the database.
7. Implement functionality.
8. Run available validation commands.
9. Fix discovered errors.
10. Update project progress.
11. Continue with the next unfinished task.

Avoid unnecessary questions.

Do not repeatedly ask for approval on routine technical choices.

If environment-specific secrets are missing, build everything that can be built without them and document the required configuration.

Do not fabricate successful external integrations.

---

# 24. MANDATORY PERSISTENT PROGRESS SYSTEM

This project may exceed one Claude Code session or one usage-limit window.

You MUST maintain persistent project documentation so work can continue after interruption.

Create:

**CLAUDE.md**
Permanent project instructions, conventions, architectural decisions, and recovery rules.

**PROGRESS.md**
Current implementation status.

**ROADMAP.md**
Development phases and checklist.

**NEXT_STEPS.md**
Exact next tasks.

**CHANGELOG.md**
Completed development changes.

## Checkpoint Requirements

After every substantial completed task:

1. Save the actual source files.
2. Update PROGRESS.md.
3. Update ROADMAP.md.
4. Update NEXT_STEPS.md.
5. Record relevant changes in CHANGELOG.md.
6. Record validation results.
7. Document blockers.
8. Preserve useful technical decisions.

Create meaningful Git commits when safe and appropriate.

Never overwrite unrelated user changes.

Do not wait until the entire phase ends before creating checkpoints.

---

# 25. SESSION RECOVERY AFTER USAGE LIMITS

Claude Code may be interrupted by usage limits, context limits, or unexpected failures.

The project must be designed for reliable continuation.

At the beginning of every resumed session:

1. Read CLAUDE.md.
2. Read PROGRESS.md.
3. Read ROADMAP.md.
4. Read NEXT_STEPS.md.
5. Inspect Git status.
6. Inspect the existing code.
7. Identify finished features.
8. Identify unfinished features.
9. Verify the current state.
10. Continue from the next unfinished task.

Never restart the project unnecessarily.

Never rewrite already completed modules without justification.

Never ask the user to resend the full specification when it is already available in project files.

Maintain sufficient information so a fresh Claude Code session can understand the project.

If the platform supports automatic continuation, use only officially supported mechanisms.

Otherwise, make manual resumption straightforward.

Do not claim the project will restart automatically after a limit reset unless the environment actually supports that behavior.

## RESUME COMMAND

When the user says:

"Continue BookFlow"

or

"Resume the project"

you must immediately read the persistent state files and continue coding.

Do not waste time restating the original project description.

Resume from the exact next unfinished task.

---

# 26. DEFINITION OF DONE

The application is complete only when:

- The Telegram bot functions.
- The Mini App opens correctly.
- Authentication is validated.
- Customers can make real bookings.
- Availability is calculated correctly.
- Overlapping appointments are prevented.
- Customers can manage their appointments.
- Owners can manage services and staff.
- The admin calendar functions.
- Notifications operate reliably.
- The database persists information.
- Business data remains isolated.
- The application is responsive.
- The demo mode works.
- Critical tests pass.
- Deployment instructions are complete.
- No known critical bugs remain.

Do not mark an incomplete feature as completed.

---

# FINAL INSTRUCTIONS

Build BOOKFLOW as a polished, professional Telegram-first booking platform.

The product must demonstrate excellent full-stack development, reliable scheduling logic, backend architecture, beautiful UI/UX, and practical business automation.

Prioritize real working functionality over superficial complexity.

Begin immediately.

First create the repository structure, persistent progress files, database foundation, API, bot integration, and frontend design system.

Then implement the complete customer booking MVP.

Continue through subsequent phases while execution capacity is available.

**Do not stop at planning. Write the actual application code, test it, fix problems, and continuously save progress for future sessions.**
