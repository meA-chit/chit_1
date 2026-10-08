# Module: Children (`kids`)

> **Agent: read first** — `docs/00-overview/README.md` (whole-product context and rules), then this file, then the submodule you are changing. Code lives in `modules/kids/`; this file mirrors it.

## Purpose
Supports children and their parents: school plan and timetable, school holidays and festivals, sports and activity plans, exams and learning, and a chore-rewards system. Also defines the child-facing mobile experience.

## Where this fits in the whole product
Chit is a modular household operating system. A household enables the modules it needs; each member and each device surface (TV, tablet, web, adult mobile, kid mobile) sees only what is enabled for them. This module is one of several (see `docs/00-overview/module-map.md`). It must keep working when other modules are disabled, and it must never import another module's internals.

## Submodules
- **school** — School timetable, school calendar, term and holiday plans, school-to-home reminders.
- **activities** — Sports events plans, clubs, festivals and family/cultural events relevant to the child.
- **learning** — Grades and the exam and homework tracker; later tutor support and exam preparation planning. Subjects come from the school plan (core, minor, elective).
- **rewards** — Stars or allowance for completed chores, perks/goodies catalogue and redemption. Reads chores from planner; owns reward data.
- **health** — Medication and pill reminders with a given/missed log and supply tracking; strictest privacy (proposed, see `docs/design/kids-module/`).
- **kid-view** — Composition of the child's own mobile view: which modules and cards appear, as configured by an adult in household settings.

Each submodule has its own folder: `docs/modules/kids/submodules/<name>/` and `modules/kids/submodules/<name>/`.

## Audiences and surfaces
- Audiences: adult (manage), child (own view only)
- Surfaces: mobile-kid (primary: phone or tablet), tablet, web (adult management). The built child app is portrait-only on phones and has no tablet layout yet; experience design, age tiers and journeys: [`kid-experience.md`](kid-experience.md)
- Enablement is configured per household, per member and per surface (see `docs/core/enablement-and-audiences.md`). Do not hard-code who sees what.

## Data this module owns
School plan and timetable, holiday/term plan, activity and event plans, Exam/homework, Reward balance and Perk (reads chores from planner). Child-view composition is configuration owned jointly with household/settings.

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
- Stage: implemented (first version): school-day plan, star chores and goals, grades, homework and tests, bag checklist, activities on the child's phone, medication, the Kids page, a dashboard goals card, and the child's own phone app (pairing, offline snapshot, six screens; audit in `submodules/kid-view/README.md`). Design: `docs/design/kids-module/`. Previously: documentation structure only; no stories yet
- Owner: TBD
- Stories: none yet — folder `docs/modules/kids/stories/` · Decisions: `docs/modules/kids/decisions/`

## Source documents and prior art
Child care and activity schedules currently live in the household setup store; the Alfred spec (S2, S3) overlaps school and activities — see `docs/modules/planner/time-keeper-spec.md`.

## Open questions
- _Add as they arise._
