# Submodule: appliances (module `devices`)

> Parent: [`docs/modules/devices/README.md`](../../README.md) · Code: `modules/devices/submodules/appliances/`

## Purpose
Washing machine, dryer, dishwasher and similar: state, remaining time, schedule.

## Boundaries
- Owns: _to be defined_
- Reads from other submodules/modules: _to be defined (public contracts only)_
- Must not: import other modules' internals; infer availability from missing data; present forecast/manual/demo data as measured.

## Enablement
Can be enabled or disabled independently of its siblings where its dependencies allow it. Declared in `modules/devices/module.manifest.yaml`.

## UI (cards / views)
_To be defined._

## Status
Structure only — no stories yet. Stories: `docs/modules/devices/stories/`.
