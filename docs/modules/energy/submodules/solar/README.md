# Submodule: solar (module `energy`)

> Parent: [`docs/modules/energy/README.md`](../../README.md) · Code: `modules/energy/submodules/solar/`

## Purpose
SolarEdge production.

## What it does
`GET /api/energy/solar/day` returns the power now, today's energy, month, lifetime and 24 hourly slots: measured values for past hours and an `expected_kwh` estimate for the rest of today (`expected_state: forecast`; Open-Meteo radiation x plant peak power x 0.8, needs household coordinates and the plant's peak power).

## Rules
- Measured and expected values are separate fields and drawn differently; an estimate is never shown as measured.
- SolarEdge allows 300 calls per day per site, so the overview is cached 10 min and the hourly curve 20 min.
- No connection: `unconfigured`. Key rejected, rate limit or outage: `unavailable` (or `stale` with the last reading).

## Status
Implemented.
