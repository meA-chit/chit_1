# Submodule: setup (module `household`)

> Parent: [`docs/modules/household/README.md`](../../README.md) · Code: `modules/household/submodules/setup/`

## Purpose
Create a household, and edit it afterwards, in one form: household basics, members (adults and children with their routines), read-only calendar feeds, and which modules appear on the dashboard (for the household and, optionally, narrowed per member).

## Behaviour
- **Latest household rule.** Every surface shows the *most recently created* household. Editing never changes that; creating another household makes it the latest. Defined once in `core/store/chit_store/common.py` (`LATEST_HOUSEHOLD_ORDER`).
- **Setup vs edit.** `/household` creates when nothing exists and edits the latest otherwise (`/household?new=1` forces a new one). Both use one form (`web/HouseholdView.tsx`) and one document shape.
- **Edit keeps identity.** Members and calendars keep their ids across edits (generated chores, assignments and references survive). Removing a calendar removes the chores it generated. A member's role cannot change; remove and re-add instead. The owner must be an adult; transfer ownership before removing the owner.
- **Enablement drives the dashboard.** The household's module list and each member's narrowing are stored and resolved by `/api/shell` (layers 3–4 of `docs/core/enablement-and-audiences.md`). Dependencies are enforced (Kids needs Planner), Household is always on, and children can only receive modules whose manifest `audiences` include `child`. "View as" in the top bar applies a member's narrowing; it is a convenience, not access control (ADR-0007).
- **Identity on the dashboard.** Each member has a predefined avatar (adults `a1-a4`, children `k1-k4`) and a colour, chosen in the form (defaults assigned if omitted). A child cannot get an adult avatar and vice versa. Illustrations only, never photos.
- **Routine inputs for the timeline.** Adult work hours, commute and work location by weekday; child school/care days, **drop-off time**, pick-up time, travel time, **how they get to school (walk, cycle or car)** and activities, each with a commute (mode, travel time) and whether the child goes **on their own or with a parent** (a car trip always has a parent). By car, the first listed drop-off/pick-up adult takes the trip; walking or cycling puts the trip on the child's own lane. Nothing is inferred when a value is missing.
- **Location.** Optional household latitude/longitude (used only for weather).
- **Not stored yet:** submodule-level enablement.

## Data
Owns: households, members, adult/child settings, calendar sources and member mappings, chore rules, `household_modules`, `member_modules` (data classes: personal; calendar feed URLs are private). Storage and seed strategy: [ADR-0010](../../../../decisions/0010-dev-data-store-sqlite-runtime-with-json-seed-documents.md). Seed: `seed/households/*.json`.

## API (all under `/api/household/`)
| Route | Purpose |
|---|---|
| `GET summary` | Names, roles, enabled modules of the latest household (no private data) |
| `GET current` | Latest household as an editable document |
| `GET {id}` / `PUT {id}` | Read / edit a household document |
| `POST setup` | Create a household from a document |

Document shape: `household`, `owner_client_id`, `modules` (list or null = platform default), `members[]` (`client_id`, `role`, `name`, `profile`, `modules`), `calendars[]`. See `seed/households/meyer-family.json`.

## Contributed sections
Other modules add sections to this screen through the manifest (`settings_sections`, target `household`): planner contributes **Chores** and **Reminders**. They appear only when that module is enabled for the household, need saved members (so are unavailable while creating), and **save instantly through their own API**, separate from the form's Save changes button. This screen never imports their code (`SettingsSections` in `core/web`). The screen has a sticky section nav.

## UI
Card `household-summary` (names and roles only, safe on shared screens); view `household` (setup/edit form).

## Boundaries
- Must not: import other modules' internals; infer availability from missing data; present forecast/manual/demo data as measured.
- Child schedules (school, activities) are stored here today but conceptually belong to `kids` (see `docs/core/current-implementation.md`).

## Status
In progress. Prototype HTML form archived at `dashboard/archive/household-setup-prototype/`. Stories still to write: submodule-level enablement, validation of feed URLs (SSRF), health data.
