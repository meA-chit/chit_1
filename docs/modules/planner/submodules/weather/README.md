# Submodule: weather (module `planner`)

> Parent: [`docs/modules/planner/README.md`](../../README.md) · Code: `modules/planner/submodules/weather/`

## Purpose
Day context: current conditions, next hours and seven-day outlook from a public provider, always labelled forecast/measured correctly. Provider access is a core connector.

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
