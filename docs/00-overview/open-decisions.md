# Open decisions

Do not assume an answer to any item here. Resolve through an ADR (product-wide) or a module decision, then remove it from this list.

| # | Decision | Why it matters | Blocks | Proposed owner |
|---|---|---|---|---|
| 1 | **Technology stack** — keep Python + vanilla JS, or adopt TypeScript/React (see `docs/core/architecture/target-stack-proposal.md`)? | Needs a manifest-driven card shell and a mobile client | Code rework | TBD |
| 2 | **Identity and access** — design to replace ADR-0007 (households, members, devices/surfaces, TLS) | Needed for Pi display over LAN, mobile apps, sensitive modules | Any non-loopback exposure; finance, health, kids data | TBD |
| 3 | **Mobile client approach** — PWA vs native; how kid devices are provisioned and constrained | kids/kid-view, mobile-adult | kids module | TBD |
| 4 | **Display delivery** — how the TV/Pi reaches the server | ADR-0007 conditions | TV rollout | TBD |
| 5 | **Module owners** (four people) and module order | CODEOWNERS, parallel branches | Parallel work | Product owner |
| 6 | **Module sequencing after the pilot** — see `docs/releases/roadmap.md` (proposed) | Scope of next stories | Story writing | Product owner |
| 7 | **Finance data sources** — manual first vs bank import; per-person privacy between partners | Sensitivity, compliance | finance/accounts | TBD |
| 8 | **Health data scope** — in v1 at all? providers, consent, retention | Highest privacy risk | household/health | TBD |
| 9 | **Chores vs rewards boundary** — chores live in planner; confirm rewards ownership in kids | Cross-module contract | planner, kids | Module owners |
| 10 | **Weather placement** — currently planner/weather with a core connector | Placement of US-103 weather | planner | Module owners |
| 11 | **Event bus mechanism** — in-process pub/sub vs persisted outbox | Cross-module events | contracts | TBD |
| 12 | **Migration strategy** — per-module numbering and runner in `core/store` | Parallel branches | core/store | TBD |
| 13 | **UI/UX alignment** — mockups show density, health and location data and control actions that conflict with rules | Design direction | Shell and cards | Design |
