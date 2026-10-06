# Submodule: rewards (module `kids`)

> Parent: [`docs/modules/kids/README.md`](../../README.md) · Code: `modules/kids/submodules/rewards/`

## Purpose
Stars or allowance for completed chores, perks/goodies catalogue and redemption. Reads chores from planner; owns reward data.

## Boundaries
- Owns: _to be defined_
- Reads from other submodules/modules: _to be defined (public contracts only)_
- Must not: import other modules' internals; infer availability from missing data; present forecast/manual/demo data as measured.

## Enablement
Can be enabled or disabled independently of its siblings where its dependencies allow it. Declared in `modules/kids/module.manifest.yaml`.

## UI (cards / views)
_To be defined._

## What it does
- A chore (planner) can be marked a **star chore** (it needs an assignee). When it is ticked off, a parent gives the outcome: **Done** (nothing extra), **Done well** (a green star) or **Try again** (no star, nothing lost). Stars are only added; a missed chore is simply open.
- **Goals** (for example sleepover 50 stars) have a star cost and a start: a fresh start counts stars from today, or all the stars the child already has. Stars are never spent: they count toward every active goal. A reached goal waits for a parent to approve it.
- API: `GET /api/kids/stars/overview`, `PUT /api/kids/stars/chores/{id}`, `POST /api/kids/stars/outcome`, `POST|PUT|DELETE /api/kids/goals[/{id}]`, `POST /api/kids/goals/{id}/approve`.
- UI: the Stars tab and Today panels of the Kids page, and the dashboard card `kids-goals` (a child viewing as themselves sees only their own row).
- Data: `kid_star_chores`, `kid_chore_outcomes`, `kid_goals` (migration 010). Seed: `seed/kids/rewards.json`.

## Status
Implemented (first version).