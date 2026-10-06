# Submodule: overview (module `energy`)

> Parent: [`docs/modules/energy/README.md`](../../README.md) · Code: `modules/energy/submodules/overview/`

## Purpose
Live power flow and daily production/consumption, measured only when a source is connected.

## Boundaries
- Owns: _to be defined_
- Reads from other submodules/modules: _to be defined (public contracts only)_
- Must not: import other modules' internals; infer availability from missing data; present forecast/manual/demo data as measured.

## Enablement
Can be enabled or disabled independently of its siblings where its dependencies allow it. Declared in `modules/energy/module.manifest.yaml`.

## UI (cards / views)
_To be defined._

## What it does
Renders `/api/energy/pricing/day`: the price now against the day average, 24 bars of hourly consumption coloured by price band (below, about, above the average), the hourly price line with the dashed day average, tomorrow's price as a faint second line once Tibber has published it (the Today/Tomorrow switch is gone), month-to-date and year-to-date cost in money, and a line comparing what was paid per kWh with the average price.

## Rules
No token: the card says how to connect Tibber and shows no numbers. See the pricing submodule for the data states.

## Status
Implemented (see the energy module README). Stories: `docs/modules/energy/stories/`.
