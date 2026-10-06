# Docs and code mirror each other

```
docs/core/                              <->  core/
docs/modules/<module>/                  <->  modules/<module>/
docs/modules/<module>/submodules/<sub>/ <->  modules/<module>/submodules/<sub>/
docs/modules/<module>/contracts.md      <->  modules/<module>/module.manifest.yaml (public surface)
docs/modules/<module>/stories/          (work items for that module)
docs/modules/<module>/decisions/        (module-level ADRs)
docs/00-overview/                       (whole-product context: read first)
```

Rules:
- Replace `docs/` with nothing and you have the code path. An agent assigned `planner/chores` opens `docs/modules/planner/submodules/chores/` and `modules/planner/submodules/chores/`.
- Each code folder has a README that links to its docs counterpart.
- Product-wide ADRs stay in `docs/architecture/adr/`; module-level ADRs go in the module's `decisions/`.
- Stories move over time from `docs/backlog/stories/` to `docs/modules/<module>/stories/`; the global backlog remains the index.

## Code layout
```
core/            server/ web/ store/ contracts/   (shared platform)
modules/<module>/
  README.md  module.manifest.yaml  shared/
  submodules/<sub>/  server/ web/ tests/
config/          household presets and surface defaults (examples)
```
