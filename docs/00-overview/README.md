# Start here (agents and humans)

Chit is a **modular household operating system**: modules (household, planner, kids, energy, devices, finance) on a shared platform (`core/`), composed into per-household, per-member, per-surface experiences. Several people and agents build different modules in parallel branches, so context must survive module boundaries.

## Reading order (about 15 minutes)
1. This page.
2. [`product-vision.md`](product-vision.md) and [`product-context.md`](product-context.md) — what and for whom; household types; surfaces.
3. [`non-negotiable-rules.md`](non-negotiable-rules.md) — rules every module obeys.
4. [`module-map.md`](module-map.md) — modules, submodules, entity ownership, dependencies, story coverage.
5. [`doc-and-code-structure.md`](doc-and-code-structure.md) — docs and code mirror each other.
6. [`agent-workflow.md`](agent-workflow.md) — start / work / merge checklist.
7. [`open-decisions.md`](open-decisions.md) — what is not decided yet (do not assume).

## Then jump to your module
`docs/modules/<module>/README.md` → `submodules/<submodule>/README.md` → `stories/`
Code: `modules/<module>/submodules/<submodule>/`

Shared behaviour (UI shell, enablement, trust labels, connectors, attention cards, auth)? Read `docs/core/` and work in `core/`; changes there need wider review.

## Other documents in this folder
| Document | Use |
|---|---|
| [`personas.md`](personas.md), [`customer-journey.md`](customer-journey.md), [`glossary.md`](glossary.md) | Users, journeys, terms |
| [`market-synthesis.md`](market-synthesis.md) | Directional competitor and segment research |
| [`market-research/`](market-research/01-market-research-report.md) | Competitor and user-voice research, tier pricing hypotheses, missing-feature ranking (2026-10-07, directional) |
| [`ecosystem-vision.md`](ecosystem-vision.md) | Long-term agent/messaging ecosystem (directional, not pilot) |

Decisions: [`docs/decisions/`](../decisions/README.md). Backlog index: [`docs/backlog/`](../backlog/README.md). Releases: [`docs/releases/`](../releases/).
