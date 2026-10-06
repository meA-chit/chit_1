# Chit

Chit is a personal automation and intelligence platform: a local-first logic layer that brings household schedules, chores, weather, smart-home and energy context into a trustworthy shared view.

## Current product direction

The first pilot is an always-visible, read-only household dashboard. It prioritises trustworthy data ingestion, visible provenance, privacy and explainable insights before autonomous actions.

## Documentation

Start with [`docs/00-overview/README.md`](docs/00-overview/README.md); the full map is in [`docs/README.md`](docs/README.md). Docs mirror code: `docs/core` <-> `core/`, `docs/modules/<module>` <-> `modules/<module>`.

- Product vision and context: [`docs/00-overview/`](docs/00-overview/README.md)
- Modules: household, planner, kids, energy, devices, finance — [`docs/modules/`](docs/modules/README.md)
- Platform architecture, enablement, trust and contracts: [`docs/core/`](docs/core/README.md)
- Decisions: [`docs/decisions/`](docs/decisions/README.md) · Open decisions: [`docs/00-overview/open-decisions.md`](docs/00-overview/open-decisions.md)
- Backlog index: [`docs/backlog/`](docs/backlog/README.md) · Pilot scope and roadmap: [`docs/releases/`](docs/releases/pilot-scope.md)
- Agent guidance: [`AGENTS.md`](AGENTS.md)

## Repository state

Documentation has been restructured into the modular layout. The module folders under `modules/` and `core/` contain manifests and empty scaffolding only. Existing implementation code (`server/`, `dashboard/`, `js/`, `css/`) has not yet been migrated into them; see `docs/00-overview/module-map.md` (legacy code mapping) and `docs/core/current-implementation.md`. Historical dashboard prototypes remain under `dashboard/archive/`.
