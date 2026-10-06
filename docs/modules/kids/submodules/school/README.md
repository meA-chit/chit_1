# Submodule: school (module `kids`)

> Parent: [`docs/modules/kids/README.md`](../../README.md) · Code: `modules/kids/submodules/school/`

## Purpose
School timetable, school calendar, term and holiday plans, school-to-home reminders.

## Boundaries
- Owns: _to be defined_
- Reads from other submodules/modules: _to be defined (public contracts only)_
- Must not: import other modules' internals; infer availability from missing data; present forecast/manual/demo data as measured.

## Enablement
Can be enabled or disabled independently of its siblings where its dependencies allow it. Declared in `modules/kids/module.manifest.yaml`.

## UI (cards / views)
_To be defined._

## What it does
Lessons, recess, meals and after-school care per weekday, typed in by a parent (state `manual`; nothing is read from a school). Add, edit, remove, and copy one day to others. The current slot is highlighted on today. Trips to and from school stay on the family timeline (planner, from household setup).
- API: `GET /api/kids/school/plan?member=[&weekday=0-6|today]`, `POST /api/kids/school/slots`, `PUT|DELETE /api/kids/school/slots/{id}`, `POST /api/kids/school/copy`.
- Data: `kid_school_slots` (migration 010). Seed: `seed/kids/school.json`.

## Status
Implemented (first version).