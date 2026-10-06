# Start here (agents and humans)

Chit is a **modular household operating system**: several modules (household, planner, kids, energy, devices, finance), composed into per-household, per-member, per-surface experiences. Several people and agents work on different modules in parallel branches, so context must survive module boundaries.

## Reading order (about 10 minutes)
1. This page.
2. [`product-context.md`](product-context.md) — what we are building, for whom, on which surfaces.
3. [`non-negotiable-rules.md`](non-negotiable-rules.md) — rules every module obeys.
4. [`module-map.md`](module-map.md) — all modules, submodules, ownership of data, dependencies.
5. [`doc-and-code-structure.md`](doc-and-code-structure.md) — docs and code mirror each other; how to jump to your folder.
6. [`agent-workflow.md`](agent-workflow.md) — checklist for starting, working and merging.

## Then jump to your module
`docs/modules/<module>/README.md` → `docs/modules/<module>/submodules/<submodule>/README.md`
Code: `modules/<module>/submodules/<submodule>/`

Touching shared behaviour (UI shell, enablement, trust labels, connectors, auth)? Read `docs/core/` and work in `core/` — those changes need wider review.

## Where the older documents fit
Product vision, personas, ADRs, specifications, backlog and the original pilot scope remain valid and live under their existing paths (see `docs/README.md`). Where they conflict with this overview, raise it; do not guess.
