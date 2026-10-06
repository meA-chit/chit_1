# ADR-0006: Modular architecture with mirrored docs and code

- Status: Accepted
- Date: 2026-10-06

## Context
Four people (and their agents) will build different modules in parallel branches. The UI must be composed per household, member and surface. Modules have submodules that can be enabled independently (e.g. kid mobile). Finance is relevant to couples without children.

## Decision
- Organise code as `core/` plus `modules/<module>/submodules/<sub>/`, and docs as `docs/core/` (including product-wide specifications) plus `docs/modules/<module>/submodules/<sub>/`, mirroring each other.
- Modules register through `module.manifest.yaml`; the UI shell composes registered cards/views using layered enablement (platform, household preset, household, member, surface).
- Modules communicate only through public contracts and events; each entity has one owner.
- Initial modules: household, planner, kids, energy, devices, finance. Cross-cutting concerns (registry, shell, enablement, trust layer, connectors, attention cards) live in `core/`.

## Consequences
Clear agent entry points and low merge conflict risk; cost is up-front contract discipline and a registry/shell in `core/`. Existing code under `server/`, `dashboard/` and `js/` is migrated incrementally (see module-map legacy mapping).
