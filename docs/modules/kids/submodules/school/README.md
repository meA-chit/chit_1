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

## Bag items (2026-10-08)
Table `kid_bag_items` (migration 014): items a child takes for a lesson or an activity (PE: sports kit), written by the child or a parent (`created_by`); a child can delete only their own. Ticks of the daily checklist are in `kid_bag_ticks` (per child, day and lower-case label). Nothing is added silently: suggestions such as "Sports kit" are one-tap buttons. The checklist itself is derived on the hub by `kid-view` (`shared/plan.py`). Routes: `GET /api/kids/bag`, `POST /api/kids/bag/items`, `DELETE /api/kids/bag/items/{id}`. Parent UI: the "Bag checklist" panel in the Kids manage section. Tests: `kid-view/tests/test_plan.py`.

## Lessons create subjects (2026-10-08)
A lesson is how a subject comes to exist (`kids/learning` grades attach to subjects). `POST` and `PUT /api/kids/school/slots` accept `subject_kind` (core, minor, elective) and `subject_code` for lessons; the plan response returns both on each lesson. Subject type, archiving and renaming rules: `../../decisions/0001-subjects-come-from-the-plan.md`.

