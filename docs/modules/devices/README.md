# Module: Devices & IoT (`devices`)

> **Agent: read first** — `docs/00-overview/README.md` (whole-product context and rules), then this file, then the submodule you are changing. Code lives in `modules/devices/`; this file mirrors it.

## Purpose
The most important devices at a glance, with Home Assistant as the integration boundary for device state. Read-only in the pilot.

## Where this fits in the whole product
Chit is a modular household operating system. A household enables the modules it needs; each member and each device surface (TV, tablet, web, adult mobile, kid mobile) sees only what is enabled for them. This module is one of several (see `docs/00-overview/module-map.md`). It must keep working when other modules are disabled, and it must never import another module's internals.

## Submodules
- **overview** — Key devices in one view with state, freshness and offline indicators.
- **home-assistant** — The Home Assistant connector: read-only entity ingestion with provenance. Control/automation execution deferred.
- **appliances** — Washing machine, dryer, dishwasher and similar: state, remaining time, schedule.
- **climate** — Room temperatures and air quality as measured values with freshness.
- **maintenance** — Filter life, battery levels, devices offline.

Each submodule has its own folder: `docs/modules/devices/submodules/<name>/` and `modules/devices/submodules/<name>/`.

## Audiences and surfaces
- Audiences: adult (full), child (limited, if enabled)
- Surfaces: tv, tablet, web, mobile-adult
- Enablement is configured per household, per member and per surface (see `docs/core/enablement-and-audiences.md`). Do not hard-code who sees what.

## Data this module owns
Device and Appliance state, connection status and freshness, maintenance signals.

## Dependencies
- Depends on: household
- Provides to other modules: normalized device and appliance state, device health, connection status
- Cross-module access only through public contracts (`docs/modules/devices/contracts.md`) and the event catalog (`docs/core/cross-module-contracts.md`).

## UI contribution
Candidate cards (the unit of UI composition — see `docs/core/ui-composition.md`): device-overview, appliances, climate, device-health

## Privacy class
Normal; camera and security data are sensitive and deferred.

## Module-specific rules
_None beyond `docs/00-overview/non-negotiable-rules.md` yet. Add rules here, not in code comments._

## Status
- Stage: pilot stories exist; module not yet re-homed in code
- Owner: TBD
- Stories: [US-104](stories/), [US-404](stories/) — folder `docs/modules/devices/stories/` · Decisions: `docs/modules/devices/decisions/`

## Source documents and prior art
ADR: [`0002`](../../decisions/0002-home-assistant-integration.md) (read-only boundary).

## Open questions
- _Add as they arise._
