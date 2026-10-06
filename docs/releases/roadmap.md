# Roadmap (proposed — not approved scope)

Pilot slices are defined in `pilot-scope.md`. This page proposes how modules follow. Stories do not exist yet for later phases; the product owner must approve sequencing (open decision #6).

| Phase | Focus | Modules and submodules | Gate |
|---|---|---|---|
| Foundation (pilot 1) | Trusted ingestion, shell, provenance, privacy | core; household/setup; planner/calendar, weather; devices/home-assistant | US-101..106, 301..304 |
| Daily value (pilot 2) | Shared daily view, chores, appliance context, enablement and layout | core (enablement, layouts); planner/chores, timeline; devices/appliances; household/members, settings | Identity design decided before any non-loopback use |
| Energy (pilot 3) | Forecast vs actual, explainable suggestions | energy/* | US-402..406 |
| Attention (pilot 4) | Bounded, dismissible cards | core attention service | US-501..503 |
| Households beyond families | Shared finance for couples and flatmates | finance/accounts, shared-expenses, recurring-bills, budgets, goals | Auth, per-person privacy, finance data decisions |
| Children | School plan, activities, rewards, kid mobile view | kids/*; planner/reminders; household/settings (kid enablement) | Auth + mobile client decisions |
| Personal insight | Health metrics, AI insights | household/health, insights; finance/insights | Consent and retention design |
| Actions | Control with confirmation, messaging | devices control, energy execution, interaction layer | Per-capability ADR |

Rule: a phase is not started until its gate decisions are recorded.
