# Module: Household & Members (`household`)

> **Agent: read first** — `docs/00-overview/README.md` (whole-product context and rules), then this file, then the submodule you are changing. Code lives in `modules/household/`; this file mirrors it.

## Purpose
Who lives in the home: household setup and type, member profiles, personal settings, opt-in health data and personal insights. Every other module asks this one 'who is this person and what may they see'.

## Where this fits in the whole product
Chit is a modular household operating system. A household enables the modules it needs; each member and each device surface (TV, tablet, web, adult mobile, kid mobile) sees only what is enabled for them. This module is one of several (see `docs/00-overview/module-map.md`). It must keep working when other modules are disabled, and it must never import another module's internals.

## Submodules
- **setup** — Create the household, choose its type (single, couple, family with children, shared flat) and apply a module preset.
- **members** — Members and roles (adult, child, guest), relationships, birth dates. Members are data records, not necessarily login accounts.
- **settings** — Per-person preferences: language, notifications, what appears on shared displays, which modules appear on their own devices (set by an adult for children).
- **health** — OPT-IN health metrics from third-party sources (steps, sleep, HRV). Sensitive; per-person consent; hidden on shared displays by default.
- **insights** — AI-derived trends and insights about a person. Opt-in; every insight must cite its underlying evidence and data state.

Each submodule has its own folder: `docs/modules/household/submodules/<name>/` and `modules/household/submodules/<name>/`.

## Audiences and surfaces
- Audiences: adult (full), child (own profile only), guest (none)
- Surfaces: web, tablet, mobile-adult; mobile-kid shows own profile only
- Enablement is configured per household, per member and per surface (see `docs/core/enablement-and-audiences.md`). Do not hard-code who sees what.

## Data this module owns
Household, Member (adult/child/guest), Role, Profile and settings; (existing store also holds adult work patterns and child care/activity schedules inside setup — to be re-homed, see `docs/core/current-implementation.md`); Health metric (opt-in); personal insights.

## Dependencies
- Depends on: core only
- Provides to other modules: member identity, roles, audience, household type, per-person visibility settings
- Cross-module access only through public contracts (`docs/modules/household/contracts.md`) and the event catalog (`docs/core/cross-module-contracts.md`).

## UI contribution
Candidate cards (the unit of UI composition — see `docs/core/ui-composition.md`): household-header, member-switcher, personal-summary, health-glance (opt-in)

## Privacy class
Sensitive (health) — per-person consent, never shown on shared screens by default.

## Module-specific rules
_None beyond `docs/00-overview/non-negotiable-rules.md` yet. Add rules here, not in code comments._

## Status
- Stage: documentation structure only; no stories yet
- Owner: TBD
- Stories: none yet — folder `docs/modules/household/stories/` · Decisions: `docs/modules/household/decisions/`

## Source documents and prior art
Existing: `docs/core/data-model.md`, `docs/core/specifications/domain-model.yaml`, `docs/core/specifications/permissions.yaml`. Code today: `server/chit_store/`, `dashboard/household-setup.html`.

## Open questions
- _Add as they arise._
