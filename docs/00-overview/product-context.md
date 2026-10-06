# Product context

## What Chit is
A trustworthy, local-first household overview that grows into an assistant. It brings schedules, chores, tasks, money, energy, devices and children's planning into one coherent system. Read-only and explainable first; actions only when an approved story requires them.

## Who it is for (household types)
| Household type | Typical modules enabled |
|---|---|
| Single | household, planner, energy, devices, finance (personal) |
| Couple (married or unmarried, no children) | household, planner, finance (shared expenses, bills, goals), energy, devices |
| Family with children | all of the above plus kids |
| Shared flat | household, planner (chores), finance (shared expenses) |

Finance is a first-class module for couples and flatmates, not only a family add-on: unmarried couples with shared financial burdens need personal vs shared ledgers, split rules and settle-up.

## Surfaces
| Surface | Notes |
|---|---|
| tv | Shared, always-on, glanceable. Screen-safe by default. Few, large cards. |
| tablet | Shared or personal, kitchen/hall. |
| web | Full management and setup. |
| mobile-adult | Personal view of enabled modules. |
| mobile-kid | Child's own view. An adult configures which modules/submodules appear (e.g. school plan, reminders, school holidays, sports events, family events, own chores and stars). The child cannot widen it. |

## Core idea: composition, not a fixed dashboard
What a user sees is the result of **module enablement and layout configured per household, per member and per surface**. Modules must therefore be self-contained cards and views that the shell composes; see `docs/core/ui-composition.md` and `docs/core/enablement-and-audiences.md`.

## Design inputs
Two generated dashboard mockups (family dashboard; smart-home dashboard) inform visual direction. Treat them as inspiration only: they show data that would breach our rules (precise location, children's health on a wall screen, unlabeled values, control buttons) and density too high for a TV.
