# Module: Energy (`energy`), shown to users as **Grid**

> **Agent: read first** — `docs/00-overview/README.md` (whole-product context and rules), then this file, then the submodule you are changing. Code lives in `modules/energy/`; this file mirrors it.

## Purpose
Production, consumption, grid, battery and dynamic prices — with forecast and measured values kept visibly separate — and read-only suggestions for when to run energy-intensive tasks (washing, drying, dishwashing).

## Where this fits in the whole product
Chit is a modular household operating system. A household enables the modules it needs; each member and each device surface (TV, tablet, web, adult mobile, kid mobile) sees only what is enabled for them. This module is one of several (see `docs/00-overview/module-map.md`). It must keep working when other modules are disabled, and it must never import another module's internals.

## Submodules
- **overview** — The dashboard Energy card: hourly consumption bars coloured by price against the day's average, the price line and the day average, plus what was actually paid per kWh. Needs a Tibber token.
- **pricing** — Tibber hourly prices (today, tomorrow once published) and hourly consumption, served at `/api/energy/pricing/day`.
- **solar** — Until SolarEdge is connected the tab shows a clearly labelled example day (state `demo`). SolarEdge production now, today, month, lifetime and per hour; the rest of today is an estimate drawn hollow.
- **forecast** — Public solar estimates, always labelled as forecast, shown beside (never merged with) actuals. Today a shared helper (`shared/forecast.py`, Open-Meteo radiation x plant peak power x 0.8) feeds the suggestions and the solar card; it has no card of its own yet.
- **appliance-planner** — Shown at the bottom of the Energy card (no separate tab). The two best windows for heavy loads (run length 1 to 4 hours), read-only. Ranked by average hourly price; with SolarEdge connected, sunny hours count cheaper. Execution is out of scope until an approved story and explicit confirmation flow exist.
- **grid** — The Grid page (`/grid`), the one place for energy and devices (the devices module has no rail entry, `nav: false`). Order: key insights first ("your heating will pre-heat 13:00 to 16:00", ventilation, appliance windows, peak to avoid), then cost and usage tiles (today, month, year, water, solar), key devices ranked by consumption, upcoming automations, price/use chart, and an integration preview for HomematicIP. Prices, totals and solar are live when Tibber/SolarEdge are connected; everything from HomematicIP is demo data (`grid.demo.ts`) and badged demo. Read-only: automations are shown or suggested, never created or started.
- **water** — Manual total and garden water meter readings (state `manual`); household use is total minus garden. Add one reading or paste a history; shown as the Water card on the Grid page. See its README.
- **connections** — The household energy settings section: Tibber token, SolarEdge site id and API key. Verified before storing, never shown again ([ADR-0011](../../decisions/0011-energy-provider-connections.md)).

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
- Stage: Tibber prices/consumption, SolarEdge production and best-window suggestions are implemented behind the hub; Home Assistant sources, battery/EV and tariffs other than Tibber are not
- Owner: TBD
- Stories: [US-402](stories/), [US-403](stories/), [US-405](stories/), [US-406](stories/) — folder `docs/modules/energy/stories/` · Decisions: `docs/modules/energy/decisions/`

## Source documents and prior art
The archived prototype `js/tibber.js` called Tibber from the browser; it is replaced by the server-side client in `modules/energy/shared/tibber.py`. Unverified against a live account: the GraphQL queries follow Tibber's public schema but were exercised only against recorded-shape test data, so check the first real token on a development hub.

## Open questions
- _Add as they arise._
