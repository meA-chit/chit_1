# Submodule: kid-view (module `kids`)

> Parent: [`docs/modules/kids/README.md`](../../README.md) · Code: `modules/kids/submodules/kid-view/`

## Purpose
Composition of the child's own mobile view: which modules and cards appear, as configured by an adult in household settings.

## Boundaries
- Owns: _to be defined_
- Reads from other submodules/modules: _to be defined (public contracts only)_
- Must not: import other modules' internals; infer availability from missing data; present forecast/manual/demo data as measured.

## Enablement
Can be enabled or disabled independently of its siblings where its dependencies allow it. Declared in `modules/kids/module.manifest.yaml`.

## UI (cards / views)
_To be defined._

## What it does
`/kids` composes the other submodules' panels. A parent picks a child and a tab (Today, Stars, Grades, Health). Viewing as a child shows only that child's school day, stars, chores and goals: no grades, no medication, no management controls. "View as" is a convenience, not access control, until identity exists (ADR-0007).

## Status
Implemented (first version).