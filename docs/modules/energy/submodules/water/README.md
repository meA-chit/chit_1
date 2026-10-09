# Submodule: water (module `energy`)

> Parent: [`docs/modules/energy/README.md`](../../README.md) · Code: `modules/energy/submodules/water/` · Maths: `modules/energy/shared/water.py` · Table: `meter_readings` (migration 018)

## Purpose
Water use from meter readings typed in by hand (data state `manual`), until a digital meter can feed the same readings. Two meters: **total** and **garden**. **Household = total − garden.**

## What it does
- `GET /api/energy/water/readings` → readings (newest first, with usage since the previous reading of that meter), per-month and per-year usage for total, garden and household, and warnings.
- `POST /api/energy/water/readings` `{readings:[{read_on, total?, garden?, note?}]}` saves 1 to 400 readings atomically; the same meter and day replaces. Decimal commas are accepted.
- `DELETE /api/energy/water/readings/{YYYY-MM-DD}` removes that day's readings.
- The Water card on the Grid page has an add form, a "paste many" box for a history (`date total garden` per line) and an edit/remove table.

## Trends and insights
Trends use only the dates actually read, no interpolation: for each pair of consecutive reading days, litres per day = (usage in m³ × 1000) / days between. Household uses the days both meters were read (total − garden); with fewer than two such days it falls back to the total meter alone (`intervals.basis: total`). The Grid insight and the Water card compare the latest period with the period before and with the average of all earlier periods, and appear only once there are two periods (three reading days). With one period the card says so and shows no trend; a longer period is not weighted as if it were a short one because the unit is per day.

## Rules
- Readings are what the meter shows, in m³, and only count up: a reading lower than an earlier one is rejected with the dates named, and nothing from that batch is saved. Future dates are rejected.
- A missing meter reading stays missing, never zero. Household needs both meters over the same window.
- Calendar months and years (the year tile) rarely fall on a reading day. The boundary is interpolated linearly between the two readings around it and the figure carries `estimated`; periods are clipped to the first and last reading, never extrapolated, and carry `partial`. The UI marks both with `~`. Trends do not need this.
- Garden above total in a period produces a warning instead of a hidden negative.
- Not built: price per m³ (so no water cost yet), a replaced-meter reset, litres per day, a digital meter connector.

## Status
Implemented, with tests in `modules/energy/submodules/water/tests/` and `water/web/parsePaste.test.ts`.
