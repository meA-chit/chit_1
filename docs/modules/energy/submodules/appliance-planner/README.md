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

## What it does
`GET /api/energy/suggestions/windows?hours=2` ranks every run of consecutive hours from the next full hour (today, plus tomorrow once Tibber has published it) and returns the two best that are at least one hour apart, so they are real alternatives.

## Ranking (`modules/energy/shared/windows.py`)
Score = mean over the window of price x (1 - solar share). The solar share of an hour is the expected PV output divided by a typical heavy load of 2 kW, capped at 1; without SolarEdge it is 0 and the score is the plain mean price. Each window reports its average price, expected solar, and the saving against the average price of the horizon; under 5 % better (and no sun) it is flagged `worth_moving: false` and the card says prices are flat.

## Rules
Read-only advice. Chit never switches a device. Needs Tibber prices (`unconfigured` otherwise).

## Status
Implemented (see the energy module README). Stories: `docs/modules/energy/stories/`.
