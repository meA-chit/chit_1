# Public contracts: Household & Members

The only surface other modules may use. Anything not listed here is private.

## Read APIs
- `GET /api/household/summary`: id, name, members (id, name, role), enabled modules of the latest household. Safe for shared screens.
- Other modules read household data through `ctx.store` documents/summary only; they never touch household tables.
- Enablement (which modules a household or member has) is resolved by `GET /api/shell`; modules do not read it themselves.

## Events published
_None defined yet._

## Events consumed
_None defined yet._

Changes to this file are contract changes: update the module manifest, `docs/core/specifications/` where applicable, and notify the owners of dependent modules (`docs/00-overview/module-map.md`).
