# Enablement and audiences

## Principle
What a user sees = modules the household enabled, narrowed by who the member is, narrowed by the surface they use. Configured, not coded.

## Layers (later layers narrow or reorder, never widen past the household admin)
1. **Platform defaults** — every module's default state.
2. **Household preset** — by household type: single, couple, family-with-children, shared-flat (see `config/household-presets/`).
3. **Household overrides** — an adult admin enables/disables modules **and submodules**.
4. **Member overrides** — per member: which enabled modules they use and their visibility settings.
5. **Surface profile** — per surface: tv, tablet, web, mobile-adult, mobile-kid (see `config/surfaces/`).

Effective visibility of a card = module enabled AND submodule enabled AND member audience allowed AND surface supported AND permission granted.

## Audiences
`adult`, `child`, `guest`. Children's views are defined by an adult. A child cannot enable anything the adult has not.

## Example: kid mobile
Household admin enables for a child's mobile: `kids/school` (timetable, holidays), `planner/reminders` (school and family events), `kids/activities` (sports plan, festivals), `planner/chores` + `kids/rewards`. Finance and health are not enabled and are never visible on that surface.

## Rules
- Enablement is data (stored per household/member/surface), not code branches.
- Screen-safe masking applies after enablement on shared surfaces.
- Sensitive modules (finance, health) are off for shared surfaces unless explicitly shown in a masked summary.
