# Cross-module contracts

Modules are decoupled. Allowed interactions:
1. **Public read API** listed in the owner's `contracts.md`, returning normalized records with provenance.
2. **Domain events** (publish/subscribe) listed in the owner's `contracts.md`, e.g. `chore.completed`, `bill.due`, `event.upcoming`.
3. **Shared types** in `core/contracts/` (member reference, data state, provenance envelope).

**In-process reads.** A module reads another module's public read API with `ctx.read(path)` (`core/server/chit_server/router.py`). It calls the owner's GET route inside the hub and returns the payload; it works the same behind the phone gateway, which serves fewer routes to the network but resolves server-side reads against the full router. Only routes listed under "Read APIs" in the owner's `contracts.md` may be read this way.

Not allowed: importing another module's code, reading its tables directly, or reaching into its UI.

## Example flows
- Chore completed (planner) -> `chore.completed` -> kids/rewards credits stars -> optional finance allowance entry.
- Bill due (finance) -> `bill.due` -> planner/reminders creates a reminder.
- Appliance suggestion (energy/appliance-planner) reads price window, solar forecast, planner chores and devices appliance state via public contracts.

The event catalog is the union of all modules' `contracts.md`; keep names `<entity>.<verb>` in the past tense.
