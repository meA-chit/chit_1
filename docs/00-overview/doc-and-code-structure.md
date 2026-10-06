# Docs and code mirror each other

```
docs/00-overview/                       whole-product context (read first)
docs/core/             <->  core/       shared platform: architecture, enablement, UI, connectors, trust, specifications, core stories
docs/modules/<m>/      <->  modules/<m>/
  README.md  contracts.md  stories/  decisions/            (module brief, public surface, work items, module ADRs)
  submodules/<s>/README.md  <->  submodules/<s>/{server,web,tests}
docs/decisions/                         product-wide ADRs
docs/backlog/                           global index: backlog.yaml, epics (stories live with their module)
docs/releases/                          pilot scope, roadmap, changelog
docs/archive/                           superseded documents (history only)
```

Rules:
- Strip `docs/` and you have the code path. For `planner/chores`: `docs/modules/planner/submodules/chores/` and `modules/planner/submodules/chores/`.
- Each code folder has a README linking to its docs counterpart.
- Stories live with the module they change (`docs/modules/<m>/stories/`) or in `docs/core/stories/`. `docs/backlog/backlog.yaml` indexes all of them with `module`/`submodule`.
- A module-level decision goes in the module's `decisions/`; anything affecting several modules, deployment, privacy or data ownership is a product-wide ADR in `docs/decisions/`.
- Machine-readable contracts: platform-wide in `docs/core/specifications/`; module-specific ones next to the module README.

## Precedence when documents disagree
1. Approved story and acceptance criteria
2. Pilot scope (`docs/releases/pilot-scope.md`)
3. Module README and its contracts
4. Whole-product rules (`docs/00-overview/non-negotiable-rules.md`) and vision
5. Accepted ADRs (`docs/decisions/`)
6. Core architecture docs (`docs/core/`)
7. Specifications (`docs/core/specifications/`)
8. Directional material (market synthesis, ecosystem vision, target-stack proposal)

Do not treat `dashboard/archive/` or `docs/archive/` as requirements.

## Code layout
```
core/            server/ web/ store/ contracts/
modules/<module>/  README.md  module.manifest.yaml  shared/  submodules/<sub>/{server,web,tests}
config/          household presets and surface profiles (examples)
```
