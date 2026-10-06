# Seed data

Committed, portable sample data so everyone can check out the repo and see the modules they do not develop (ADR-0010).

- `seed/households/*.json` — **household documents**: exactly the shape of `POST /api/household/setup`. Stable ids, so every machine gets identical records and other modules' seeds can reference them (`hh-meyer`, `nina`, `mila`, `cal-bins`, …).
- Module data lives beside it: `seed/planner/chores.json` and `seed/planner/reminders.json` (reminders are one-off with offsets like `in_days`, so they never go stale) (loaded by the module's `server/seed.py`).
- Kids sample data lives in `seed/kids/{rewards,learning,school,health}.json` (stars and goals, grades with relative dates, a school day copied across the week, sample medication names). Modules seed in dependency order, so kids runs after the planner chores it refers to.
- Loaded by `npm run seed`, or automatically by `npm run hub:dev` when the dev database is empty. Already-present households are skipped, so seeding is idempotent.
- Ids are global across households (primary keys): a second fixture must use different member/calendar ids (`nina-2`, …).
- Energy provider keys (Tibber token, SolarEdge key) are **never** part of a household document, a fixture or an export; they live in the hub's `energy_connections` table and are entered in the household energy settings (ADR-0011).
- Only **example** URLs (`*.example`) belong here. Real calendar feeds are private (data class `personal`, ADR-0009); `export` masks them unless you pass `--include-urls`.
- Make a fixture from what you set up locally: `npm run export -- latest > seed/households/my-household.json`, review it, commit it.
- Other modules: when you have tables, add `seed/<module>/*.json` and a loader beside your module; load order follows module dependencies.

"Latest household" (what every surface shows) is the most recently *created* one, so seeding a second fixture after the first makes it the latest. Editing never changes that.
