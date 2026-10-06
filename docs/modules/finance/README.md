# Module: Finance (`finance`)

> **Agent: read first** — `docs/00-overview/README.md` (whole-product context and rules), then this file, then the submodule you are changing. Code lives in `modules/finance/`; this file mirrors it.

## Purpose
Shared money tracking for any household: unmarried or married couples with shared financial burdens, flatmates and families. Distinguishes personal from shared, and tracks who owes whom. Valuable even for households without children.

## Where this fits in the whole product
Chit is a modular household operating system. A household enables the modules it needs; each member and each device surface (TV, tablet, web, adult mobile, kid mobile) sees only what is enabled for them. This module is one of several (see `docs/00-overview/module-map.md`). It must keep working when other modules are disabled, and it must never import another module's internals.

## Submodules
- **accounts** — Manual first, connected sources later; each account is personal or shared.
- **shared-expenses** — Split expenses by rule (50/50, proportional to income, custom), track balances and settle up.
- **budgets** — Monthly budgets per category, personal and shared.
- **recurring-bills** — Rent, utilities, subscriptions, with due dates feeding planner reminders.
- **goals** — Shared savings goals (holiday, deposit, emergency fund).
- **insights** — Spending trends and AI-derived insights. Opt-in, evidence-backed.

Each submodule has its own folder: `docs/modules/finance/submodules/<name>/` and `modules/finance/submodules/<name>/`.

## Audiences and surfaces
- Audiences: adult (own and shared), child (allowance view only, if enabled), guest (none)
- Surfaces: web, mobile-adult, tablet; not on tv unless explicitly shown in a masked summary
- Enablement is configured per household, per member and per surface (see `docs/core/enablement-and-audiences.md`). Do not hard-code who sees what.

## Data this module owns
Account (personal/shared), Expense and split rule, Balance between members, Budget, Recurring bill, Goal.

## Dependencies
- Depends on: household; kids (optional, allowance)
- Provides to other modules: shared ledger, balances between members, budgets, recurring bills, goals
- Cross-module access only through public contracts (`docs/modules/finance/contracts.md`) and the event catalog (`docs/core/cross-module-contracts.md`).

## UI contribution
Candidate cards (the unit of UI composition — see `docs/core/ui-composition.md`): shared-balance, upcoming-bills, budget-status, goal-progress

## Privacy class
Sensitive — personal vs shared ledgers; per-person visibility; never on shared screens by default.

## Module-specific rules
_None beyond `docs/00-overview/non-negotiable-rules.md` yet. Add rules here, not in code comments._

## Status
- Stage: documentation structure only; no stories yet
- Owner: TBD
- Stories: none yet — folder `docs/modules/finance/stories/` · Decisions: `docs/modules/finance/decisions/`

## Source documents and prior art
No prior documents beyond the finance agent idea in `docs/00-overview/ecosystem-vision.md`. Needs research (market-synthesis agenda), sensitivity and data-source decisions (open decisions #7).

## Open questions
- _Add as they arise._
