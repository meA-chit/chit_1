# Module: Children (`kids`)

> **Agent: read first** — `docs/00-overview/README.md` (whole-product context and rules), then this file, then the submodule you are changing. Code lives in `modules/kids/`; this file mirrors it.

## Purpose
Supports children and their parents: school plan and timetable, school holidays and festivals, sports and activity plans, exams and learning, and a chore-rewards system. Also defines the child-facing mobile experience.

## Where this fits in the whole product
Chit is a modular household operating system. A household enables the modules it needs; each member and each device surface (TV, tablet, web, adult mobile, kid mobile) sees only what is enabled for them. This module is one of several (see `docs/00-overview/module-map.md`). It must keep working when other modules are disabled, and it must never import another module's internals.

## Submodules
- **school** — School timetable, school calendar, term and holiday plans, school-to-home reminders.
- **activities** — Sports events plans, clubs, festivals and family/cultural events relevant to the child.
- **learning** — Exam and homework tracker; later tutor support and exam preparation planning.
- **rewards** — Stars or allowance for completed chores, perks/goodies catalogue and redemption. Reads chores from planner; owns reward data.
- **kid-view** — Composition of the child's own mobile view: which modules and cards appear, as configured by an adult in household settings.

Each submodule has its own folder: `docs/modules/kids/submodules/<name>/` and `modules/kids/submodules/<name>/`.

## Audiences and surfaces
- Audiences: adult (manage), child (own view only)
- Surfaces: mobile-kid (primary), tablet, web (adult management)
- Enablement is configured per household, per member and per surface (see `docs/core/enablement-and-audiences.md`). Do not hard-code who sees what.

## Data this module owns
_To be defined with the module's first stories. Rule: one owner per entity (see ownership table in `docs/00-overview/module-map.md`)._

## Dependencies
- Depends on: household, planner (chores, reminders, events); finance (optional, for allowance)
- Provides to other modules: school and activity events (to planner), reward balances, child view composition
- Cross-module access only through public contracts (`docs/modules/kids/contracts.md`) and the event catalog (`docs/core/cross-module-contracts.md`).

## UI contribution
Candidate cards (the unit of UI composition — see `docs/core/ui-composition.md`): school-today, exams, my-chores, stars-balance, perks, holiday-countdown

## Privacy class
Strict (children's data) — least-data default; adults control what a child's device shows.

## Module-specific rules
_None beyond `docs/00-overview/non-negotiable-rules.md` yet. Add rules here, not in code comments._

## Status
- Stage: structure only (no stories yet)
- Owner: TBD
- Stories: `docs/modules/kids/stories/` · Decisions: `docs/modules/kids/decisions/`

## Open questions
- _Add as they arise._
