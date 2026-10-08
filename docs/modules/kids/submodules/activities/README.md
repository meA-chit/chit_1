# Submodule: activities (module `kids`)

> Parent: [`docs/modules/kids/README.md`](../../README.md) · Code: `modules/kids/submodules/activities/`

## Purpose
Sports events plans, clubs, festivals and family/cultural events relevant to the child.

## Boundaries
- Owns: _to be defined_
- Reads from other submodules/modules: _to be defined (public contracts only)_
- Must not: import other modules' internals; infer availability from missing data; present forecast/manual/demo data as measured.

## Enablement
Can be enabled or disabled independently of its siblings where its dependencies allow it. Declared in `modules/kids/module.manifest.yaml`.

## UI (cards / views)
_To be defined._

## Where activities live today
This submodule has no code. Regular activities are stored per child in **household setup** (`child_activities`, `child_activity_days`: name, place, time range, weekdays, commute mode, travel time, escort) and feed the family timeline. School, care and sport **events** reach the family view through the calendar links attached to each child's calendars in household setup (types include `school_care` and `sport_activity`). Gaps: activities are weekly-only; the feed reader ignores `RRULE`; the child's phone app now receives the child's weekly activities and the events of their own calendars (kid-view `activities`; 2026-10-08); there is no in-app way to create a one-off event. See `docs/00-overview/market-research/03-missing-feature-analysis.md` (section 3) and `docs/modules/kids/kid-experience.md`.

## Status
Structure only — no stories yet. Stories: `docs/modules/kids/stories/`.
