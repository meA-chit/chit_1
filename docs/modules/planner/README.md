# Module: Time & Planner (`planner`)

> **Agent: read first** — `docs/00-overview/README.md` (whole-product context and rules), then this file, then the submodule you are changing. Code lives in `modules/planner/`; this file mirrors it.

## Purpose
Everything about time: connected calendars, family timeline, reminders, chores, tasks and routines. These submodules are one connected system and share one timeline.

## Where this fits in the whole product
Chit is a modular household operating system. A household enables the modules it needs; each member and each device surface (TV, tablet, web, adult mobile, kid mobile) sees only what is enabled for them. This module is one of several (see `docs/00-overview/module-map.md`). It must keep working when other modules are disabled, and it must never import another module's internals.

## Submodules
- **calendar** — Read-only calendar subscriptions mapped to members; next three days and beyond; availability that never infers 'free' from missing data.
- **reminders** — Time- or event-based reminders for one or more members, including preparation reminders (e.g. swim bag).
- **chores** — Chit-owned chores with assignees, rules and provenance. Owns chore data; the kids module only adds rewards on top.
- **tasks** — One-off tasks and to-dos, personal or shared, optionally linked to events or chores.
- **routines** — Recurring patterns such as the school run, bin day and weekly washing.
- **timeline** — The combined, per-member-filterable timeline view over calendar, reminders, chores, tasks and routines.
- **weather** — Day context: current conditions, next hours and seven-day outlook from a public provider, always labelled forecast/measured correctly. Provider access is a core connector.
- **time-intelligence** — DEFERRED. Deterministic availability, conflict and childcare-gap reasoning plus timely, explainable recommendations (Alfred part 2). Not a prerequisite for calendar views.

Each submodule has its own folder: `docs/modules/planner/submodules/<name>/` and `modules/planner/submodules/<name>/`.

## Audiences and surfaces
- Audiences: adult (full), child (own and family items, per setting), guest (none)
- Surfaces: tv, tablet, web, mobile-adult, mobile-kid (filtered)
- Enablement is configured per household, per member and per surface (see `docs/core/enablement-and-audiences.md`). Do not hard-code who sees what.

## Data this module owns
Calendar source and source-to-member mapping, Event view (subscribed events are not mirrored), Availability, Reminder, Chore and chore-generation rule (idempotent, linked to source occurrence), Task, Routine, Weather observation/forecast.

## Dependencies
- Depends on: household
- Provides to other modules: events, reminders, chores, tasks, routines, availability, the combined timeline
- Cross-module access only through public contracts (`docs/modules/planner/contracts.md`) and the event catalog (`docs/core/cross-module-contracts.md`).

## UI contribution
Candidate cards (the unit of UI composition — see `docs/core/ui-composition.md`): family-calendar, timeline, chore-planner, reminders, tasks, upcoming, weather-today

## Privacy class
Normal; event details can be hidden by screen-safe mode.

## Module-specific rules
_None beyond `docs/00-overview/non-negotiable-rules.md` yet. Add rules here, not in code comments._

## Status
- Stage: pilot stories exist; module not yet re-homed in code
- Owner: TBD
- Stories: [US-103](stories/), [US-202](stories/), [US-203](stories/), [US-401](stories/) — folder `docs/modules/planner/stories/` · Decisions: `docs/modules/planner/decisions/`

## Source documents and prior art
Detailed design: [`time-keeper-spec.md`](time-keeper-spec.md) (Alfred Part 1 and 2). Code today: calendar reader in `server/run.py`, `dashboard/calendar-home.html`, `js/weather.js`, `js/calendar.js`.

## Open questions
- _Add as they arise._
