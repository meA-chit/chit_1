# Core platform docs

Mirrors `core/`. Applies to all modules.

- [`architecture.md`](architecture.md) — modular monolith, current implementation, deployment; [`architecture/target-stack-proposal.md`](architecture/target-stack-proposal.md) (not adopted)
- [`module-contract.md`](module-contract.md) — what a module must provide (manifest, cards, permissions)
- [`enablement-and-audiences.md`](enablement-and-audiences.md) — per-household/member/surface enablement; kid mobile
- [`ui-composition.md`](ui-composition.md) — cards, views, layout, surfaces; [`ux-flows.md`](ux-flows.md) — generic UX flows
- [`cross-module-contracts.md`](cross-module-contracts.md) — module communication without coupling
- [`trust-and-privacy.md`](trust-and-privacy.md) — data states, screen-safe, sensitive classes, auth status
- [`connectors.md`](connectors.md) — external sources catalogue and rules
- [`data-model.md`](data-model.md) — normalized record envelope and entities
- [`attention-and-insights.md`](attention-and-insights.md) — cross-module attention cards
- [`branching-and-merging.md`](branching-and-merging.md) — parallel module development
- [`current-implementation.md`](current-implementation.md) — baseline and known gaps for the rework
- [`specifications/`](specifications/) — OpenAPI, data states, domain model, permissions, module enablement
- [`diagrams/`](diagrams/) — C4 DSL and runtime sequences
- [`stories/`](stories/) — platform stories (US-101/102/105/106, 201/204, 301–305, 501–503)
