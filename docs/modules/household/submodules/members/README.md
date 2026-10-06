# Submodule: members (module `household`)

> Parent: [`docs/modules/household/README.md`](../../README.md) · Code: `modules/household/submodules/members/`

## Purpose
Members and roles (adult, child, guest), relationships, birth dates. Members are data records, not necessarily login accounts.

## Boundaries
- Owns: _to be defined_
- Reads from other submodules/modules: _to be defined (public contracts only)_
- Must not: import other modules' internals; infer availability from missing data; present forecast/manual/demo data as measured.

## Enablement
Can be enabled or disabled independently of its siblings where its dependencies allow it. Declared in `modules/household/module.manifest.yaml`.

## UI (cards / views)
_To be defined._

## Status
Structure only — no stories yet. Stories: `docs/modules/household/stories/`.
