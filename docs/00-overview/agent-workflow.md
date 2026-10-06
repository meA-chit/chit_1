# Agent workflow for module work

## Before coding
1. Read `docs/00-overview/` (README, product-context, rules, module-map).
2. Read your module README and the submodule README(s). Read its `contracts.md` and those of modules you depend on.
3. Read the story and its acceptance criteria (`docs/modules/<module>/stories/` or `docs/core/stories/` (index: `docs/backlog/backlog.yaml`)).
4. Check `docs/00-overview/open-decisions.md`; do not invent behaviour for undecided items.
5. If the work touches `core/`, another module's contracts, privacy, deployment or data ownership: propose an ADR first.

## While coding
- Stay inside `modules/<module>/submodules/<sub>/`. Anything shared across your module's submodules goes in `modules/<module>/shared/`; anything shared across modules goes through `core/` with review.
- Register UI as cards/views in the manifest; never reference another module's files.
- Test unavailable, stale and disabled-dependency states.

## Before merging
- Docs updated (module README, submodule README, contracts, manifest).
- Migrations named `<module>_NNN_*.sql`.
- PR description: story IDs, files changed, checks run, residual risks, deferred work.
- Rebase on main at least weekly; keep core changes in separate PRs.
