# Chit Documentation

Version-controlled source of truth for product intent, architecture, module designs and delivery scope. Docs mirror the code layout (`docs/core` <-> `core/`, `docs/modules/<m>` <-> `modules/<m>`).

**New here, or an agent starting a task? Read [`00-overview/README.md`](00-overview/README.md) first.**

## Map
| Path | Contents |
|---|---|
| [`00-overview/`](00-overview/README.md) | Vision, product context, rules, module map, workflow, open decisions, personas, journey, glossary, market synthesis, ecosystem vision |
| [`core/`](core/README.md) | Platform docs: architecture, enablement, UI composition, contracts, trust and privacy, connectors, data model, attention service, specifications, current implementation, core stories |
| [`modules/`](modules/README.md) | One folder per module: README, contracts, submodules, stories, decisions |
| [`decisions/`](decisions/README.md) | Product-wide ADRs |
| [`backlog/`](backlog/README.md) | Global story/epic index |
| [`releases/`](releases/pilot-scope.md) | Pilot scope, proposed roadmap, changelog |
| [`archive/`](archive/) | Superseded documents |

## Reading paths
- **Product owner:** `00-overview/product-vision.md` -> `product-context.md` -> `module-map.md` -> `personas.md` -> `customer-journey.md` -> `releases/pilot-scope.md` -> `releases/roadmap.md` -> `backlog/`
- **Architect:** `core/architecture.md` -> `core/data-model.md` -> `core/enablement-and-audiences.md` -> `core/cross-module-contracts.md` -> `core/trust-and-privacy.md` -> `decisions/` -> `core/specifications/`
- **Module developer or agent:** `00-overview/` (all) -> `modules/<module>/README.md` -> submodule README -> stories -> `contracts.md` of dependencies
- **Core/platform developer:** `core/` (all) + `core/current-implementation.md`

## Status vocabulary
`draft` (incomplete), `ready` (approved, implementable), `in-progress`, `blocked` (documented dependency), `done` (acceptance verified), `deferred` (outside the active release). ADR statuses: Proposed, Accepted, Superseded.

## Change policy
Behaviour changes start in a story (in the owning module). Contract changes update the module's `contracts.md` and, where platform-wide, `core/specifications/`. Significant or cross-module choices create an ADR and update `00-overview/open-decisions.md`. Supersede accepted ADRs; do not rewrite their history. Update module docs in the same PR as the code.
