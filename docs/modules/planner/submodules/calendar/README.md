# Submodule: calendar (module `planner`)

> Parent: [`docs/modules/planner/README.md`](../../README.md) · Code: `modules/planner/submodules/calendar/`

## Purpose
Read-only calendar subscriptions mapped to members; next three days and beyond; availability that never infers 'free' from missing data.

## Boundaries
- Owns: _to be defined_
- Reads from other submodules/modules: _to be defined (public contracts only)_
- Must not: import other modules' internals; infer availability from missing data; present forecast/manual/demo data as measured.

## Enablement
Can be enabled or disabled independently of its siblings where its dependencies allow it. Declared in `modules/planner/module.manifest.yaml`.

## UI (cards / views)
_To be defined._

## Status
Structure only — no stories yet. Stories: `docs/modules/planner/stories/`.
