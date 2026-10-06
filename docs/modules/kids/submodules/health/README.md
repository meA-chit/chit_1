# Submodule: health (module `kids`)

> Parent: [`docs/modules/kids/README.md`](../../README.md) · Code: `modules/kids/submodules/health/`

## Purpose
Medication and pill reminders for children.

## What it does
Per child: medication with dose, time, weekdays, which adult is reminded and an optional supply. Mark each dose given or missed (a week grid shows the log); giving a dose uses one unit of supply and a refill warning appears at 10 days or less. **The strictest data class**: parents only, never on shared screens or the timeline, never on a child's own view.
- Not built yet: push or on-screen reminders at the dose time (needs notifications), a name-free "Mila, 19:00" entry on shared screens.
- API: `GET|POST /api/kids/health/meds`, `PUT|DELETE /api/kids/health/meds/{id}`, `POST /api/kids/health/meds/{id}/log`.
- Data: `kid_meds`, `kid_med_log` (migration 010). Seed: `seed/kids/health.json` (sample names only; never put real medication in seed data).

## Status
Implemented (first version).
