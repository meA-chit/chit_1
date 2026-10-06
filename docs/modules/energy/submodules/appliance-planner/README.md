# Submodule: appliance-planner (module `energy`)

> Parent: [`docs/modules/energy/README.md`](../../README.md) · Code: `modules/energy/submodules/appliance-planner/`

## Purpose
Explainable, read-only suggestions that combine price, solar forecast and chores. Execution is out of scope until an approved story and explicit confirmation flow exist.

## Boundaries
- Owns: _to be defined_
- Reads from other submodules/modules: _to be defined (public contracts only)_
- Must not: import other modules' internals; infer availability from missing data; present forecast/manual/demo data as measured.

## Enablement
Can be enabled or disabled independently of its siblings where its dependencies allow it. Declared in `modules/energy/module.manifest.yaml`.

## UI (cards / views)
_To be defined._

## Status
Structure only — no stories yet. Stories: `docs/modules/energy/stories/`.
