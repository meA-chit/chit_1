# Chit Agent Instructions

## Navigation (read first)

Chit is a modular household operating system built in parallel by several people/agents. Keep the whole-product context while working on one module:

1. Read `docs/00-overview/README.md` (product context, rules, module map, workflow).
2. Jump to your module: `docs/modules/<module>/README.md` and its `submodules/<sub>/README.md`. Code mirrors docs: `modules/<module>/submodules/<sub>/`.
3. Shared platform work: `docs/core/` and `core/`.
4. Never import another module's code; use public contracts and events. UI is contributed as registered cards/views, composed per household, member and surface.

## Product intent

Chit is a trustworthy, read-only household overview before it is an autonomous assistant. Do not introduce messaging, schedule changes, appliance control or other external side effects unless an approved story explicitly requires them.

## Sources of truth

Use this precedence when documents disagree:

1. Approved story and acceptance criteria (`docs/modules/<module>/stories/` or `docs/core/stories/`; index in `docs/backlog/backlog.yaml`)
2. Current pilot scope in `docs/releases/pilot-scope.md`
3. The module README and its `contracts.md`
4. Whole-product rules (`docs/00-overview/non-negotiable-rules.md`) and product principles (`docs/00-overview/product-vision.md`)
5. Accepted decisions in `docs/decisions/`
6. Architecture documents in `docs/core/`
7. Machine-readable contracts in `docs/core/specifications/`
8. Directional material: `docs/00-overview/market-synthesis.md`, `ecosystem-vision.md`, `docs/core/architecture/target-stack-proposal.md`

Do not treat archived dashboard prototypes (`dashboard/archive/`) or `docs/archive/` as current requirements. Check `docs/00-overview/open-decisions.md` before assuming an undecided topic (stack, identity, mobile, sequencing).

## Before coding

- Identify one or more story IDs and read their dependencies and architecture references. Read the module README for the module you change.
- Confirm that acceptance criteria are unambiguous and testable.
- Check relevant ADRs and specifications.
- Ask for clarification instead of inventing product behaviour.
- Propose a new ADR when a change affects deployment, data ownership, privacy, integration boundaries or major technology choices.

## Non-negotiable rules

- Respect module isolation: no cross-module imports; use public contracts and events; contribute UI only as registered cards/views; never hard-code who sees what (enablement is configuration).
- Preserve source, observed time, ingestion time, availability and data state for normalized records.
- Use only the states defined in `docs/core/specifications/data-states.yaml`.
- Treat missing information as `unavailable` or `unknown`; never infer availability from absence.
- Never label forecast, manual or demo values as measured.
- Keep pilot device integrations read-only.
- Apply screen-safe presentation before returning shared-display data.
- Minimise data collection and enforce explicit permissions for sensitive domains.

## Definition of done

- All story acceptance criteria are implemented and covered by tests.
- Linting, type checks and automated tests pass.
- API/schema changes update the corresponding specification.
- Architectural changes update documentation and, when significant, add an ADR.
- The pull request lists story IDs, files changed, checks run, residual risks and deferred work.
