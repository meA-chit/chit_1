# Submodule: pricing (module `energy`)

> Parent: [`docs/modules/energy/README.md`](../../README.md) · Code: `modules/energy/submodules/pricing/`

## Purpose
Tariffs and dynamic electricity prices with freshness and source.

## Boundaries
- Owns: _to be defined_
- Reads from other submodules/modules: _to be defined (public contracts only)_
- Must not: import other modules' internals; infer availability from missing data; present forecast/manual/demo data as measured.

## Enablement
Can be enabled or disabled independently of its siblings where its dependencies allow it. Declared in `modules/energy/module.manifest.yaml`.

## UI (cards / views)
_To be defined._

## What it does
`GET /api/energy/pricing/day?date=today|tomorrow` returns 24 hourly slots (price, level, consumption), the day average, cheapest and priciest hour, the current hour against the average and, when consumption is known, the consumption-weighted price actually paid.

## Rules
- Quarter-hourly prices are averaged into clock hours; the date and hour come from Tibber's own timestamps (assumes the household time zone equals the Tibber home's).
- No token: `unconfigured`. Token rejected: `unavailable` (`token_rejected`). Provider down with an earlier reading: `stale`.
- Consumption needs a Tibber Pulse or smart meter. Without it `consumption.state` is `unavailable` and hours carry `null`, never `0`.
- `totals` gives month-to-date and year-to-date use and cost in money, from Tibber's monthly consumption (the cost Tibber reports per month, last 12 months). Months without a figure are skipped, never zeroed; a year that starts mid-year says so (`year_from`). Cached 30 min. Needs a smart meter, like consumption.
- Caching: prices 10 min, consumption 15 min (`modules/energy/shared/tibber.py`).

## Status
Implemented (see the energy module README). Stories: `docs/modules/energy/stories/`.
