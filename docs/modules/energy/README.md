# Module: Energy (`energy`)

> **Agent: read first** — `docs/00-overview/README.md` (whole-product context and rules), then this file, then the submodule you are changing. Code lives in `modules/energy/`; this file mirrors it.

## Purpose
Production, consumption, grid, battery and dynamic prices — with forecast and measured values kept visibly separate — and read-only suggestions for when to run energy-intensive tasks (washing, drying, dishwashing).

## Where this fits in the whole product
Chit is a modular household operating system. A household enables the modules it needs; each member and each device surface (TV, tablet, web, adult mobile, kid mobile) sees only what is enabled for them. This module is one of several (see `docs/00-overview/module-map.md`). It must keep working when other modules are disabled, and it must never import another module's internals.

## Submodules
- **overview** — Live power flow and daily production/consumption, measured only when a source is connected.
- **pricing** — Tariffs and dynamic electricity prices with freshness and source.
- **forecast** — Public solar estimates, always labelled as forecast, shown beside (never merged with) actuals.
- **appliance-planner** — Explainable, read-only suggestions that combine price, solar forecast and chores. Execution is out of scope until an approved story and explicit confirmation flow exist.

Each submodule has its own folder: `docs/modules/energy/submodules/<name>/` and `modules/energy/submodules/<name>/`.

## Audiences and surfaces
- Audiences: adult (full), child (read-only summary, if enabled)
- Surfaces: tv, tablet, web, mobile-adult
- Enablement is configured per household, per member and per surface (see `docs/core/enablement-and-audiences.md`). Do not hard-code who sees what.

## Data this module owns
Energy reading (measured vs forecast), Tariff/price window, Solar forecast, Appliance timing suggestion.

## Dependencies
- Depends on: household, devices (inverter/meter data via Home Assistant), planner (chores)
- Provides to other modules: energy readings, price windows, solar forecast, appliance timing suggestions
- Cross-module access only through public contracts (`docs/modules/energy/contracts.md`) and the event catalog (`docs/core/cross-module-contracts.md`).

## UI contribution
Candidate cards (the unit of UI composition — see `docs/core/ui-composition.md`): power-flow, production-vs-forecast, price-now, best-time-suggestion

## Privacy class
Normal.

## Module-specific rules
_None beyond `docs/00-overview/non-negotiable-rules.md` yet. Add rules here, not in code comments._

## Status
- Stage: pilot stories exist; module not yet re-homed in code
- Owner: TBD
- Stories: [US-402](stories/), [US-403](stories/), [US-405](stories/), [US-406](stories/) — folder `docs/modules/energy/stories/` · Decisions: `docs/modules/energy/decisions/`

## Source documents and prior art
Code today: `js/tibber.js` (browser-side; to move behind the server).

## Open questions
- _Add as they arise._
