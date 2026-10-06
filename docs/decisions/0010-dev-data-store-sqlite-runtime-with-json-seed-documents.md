# ADR-0010: Dev/pilot data store — SQLite at runtime, portable JSON household documents for seed and sharing

- Status: Accepted (scope: development, testing and pilot; production encryption stays governed by ADR-0004)
- Date: 2026-10-06
- Deciders: product owner, module owners (household, planner, kids, energy, devices, finance)
- Relates to: ADR-0004 (SQLCipher), ADR-0009 (data classes), open decision 12 (migrations)

## Context
Module teams build in parallel branches and need to *see each other's modules working*: someone building `energy` must check out the repo and immediately see a realistic household (members, children, calendars) without running setup by hand or sharing a database file. The household module needs create **and edit** of the same household, and every surface shows the **latest household**. The team prefers a simple store for testing ("SQL or JSON files"), with encryption later.

Forces:
- The existing store is relational and tested (foreign keys, owner/pickup triggers, generated chores that reference members and calendar sources).
- Seed data must be **diffable, reviewable and mergeable in git**. Binary files are not.
- Seed data must be **identical on every machine** (same ids), so other modules' seeds can reference it.
- Requiring a SQLCipher key for every contributor adds friction for local testing.
- Calendar feed URLs are private (data class `personal`, ADR-0009): committed samples must contain only public/example URLs.

## Decision
**SQLite stays the runtime store. JSON is the interchange and seed format.**

1. **One shape everywhere: the *household document*.** It is the setup payload (`household`, `owner_client_id`, `members[]` with `profile`, `calendars[]`, plus `modules` enablement). The same shape is used for `POST /api/household/setup` (create), `PUT /api/household/{id}` (edit), `GET /api/household/{id}` (read for the edit view), seed files and exports.
2. **Seed fixtures are committed JSON**: `seed/households/*.json`. They use stable ids (`preserve_ids`), so they load identically on every machine and are idempotent (existing ids are skipped).
3. **The database file is never committed** (`data/` stays git-ignored). `npm run seed` loads fixtures; `npm run hub:dev` starts the hub and seeds an empty database automatically.
4. **Plain mode for dev only.** `CHIT_STORAGE=plain` opens an unencrypted SQLite file (default `data/dev.db`) and prints a warning. Without it the store still requires `CHIT_DB_KEY_HEX` (ADR-0004 unchanged). Plain mode is refused when `CHIT_ENV=production`. Same schema and migrations in both modes, so moving to encrypted is a configuration change.
5. **Share what you create**: `python -m chit_store.cli export latest > seed/households/x.json` turns any local household into a fixture to commit (after removing private URLs).
6. **"Latest household" is defined once**, in the store: the household with the greatest `created_at`. Editing never changes `created_at`, so an edit does not reorder households.

## Options considered

### A — JSON files as the store (one file per household)
| Dimension | Assessment |
|---|---|
| Complexity | Low to start; grows (locking, referential integrity, partial updates) |
| Team familiarity | High |
| Git friendliness | Excellent |
| Fit with existing code | Poor: chores, calendar sources and triggers are relational; would rewrite and re-test the store |

**Pros:** trivially portable; no tooling. **Cons:** no integrity (orphaned member ids), concurrent writers corrupt files, every module needing queries reimplements them, throws away tested code.

### B — Unencrypted SQLite committed to git
| Dimension | Assessment |
|---|---|
| Complexity | Low |
| Git friendliness | Poor: binary, unmergeable, conflicts on every branch |

**Pros:** zero loader code. **Cons:** merge conflicts, no review of data changes, WAL sidecars, accidental commit of real personal data, ids/timestamps drift per machine.

### C — SQLite runtime + JSON seed/export documents (chosen)
| Dimension | Assessment |
|---|---|
| Complexity | Medium-low: one loader, one exporter, one document shape |
| Git friendliness | Excellent (text, reviewable) |
| Fit with existing code | Keeps the tested relational store and its integrity rules |
| Path to production | Same schema; encryption already supported |

**Pros:** keeps integrity and queries; seeds are text; one shape serves API, seed, export; dev friction removed. **Cons:** a loader/exporter to maintain; two representations that must round-trip (covered by tests).

### D — Share a dev SQLCipher key and commit an encrypted DB
Rejected: still binary and unmergeable, and a shared key in the repo defeats the point of ADR-0004.

## Trade-off analysis
The real choice is between *simplest possible storage* (A) and *simplest possible collaboration* (B/C). A optimises for day one and loses the integrity the household/chores model already depends on; B optimises for file sharing and loses git. C puts the portability in the one place git is good at (text) and keeps the database a local, disposable cache of the fixtures plus whatever a developer creates. Because the seed shape equals the API shape, there is no separate "seed format" to learn or keep in sync.

## Consequences
- **Easier:** onboarding (`git clone`, `npm install`, `npm run dev:all`), cross-module demos, reproducible tests, bug reports as a JSON document.
- **Harder:** every schema change to household data must update the document reader/writer and fixtures; a round-trip test enforces this.
- **Risks:** a developer exports a real household with private feed URLs and commits it. Mitigation: exporter masks `subscription_url` unless `--include-urls`; CODEOWNERS review of `seed/`; seed lint test rejects non-example hosts.
- **Revisit:** when non-household modules need seeds (convention: `seed/<module>/*.json`, loaded in manifest dependency order), when the migration strategy is decided (open decision 12), and before any real family data is stored (encryption on, ADR-0004).

## Action items
1. [x] Household document read/create/update in `core/store` (id-preserving edit, no cascade loss of generated chores).
2. [x] `chit_store.cli` with `seed` and `export`; `CHIT_STORAGE=plain` for dev.
3. [x] `seed/households/` fixture and a seed-lint test.
4. [x] Stored module enablement (household and member) feeding `/api/shell`.
5. [ ] Seed conventions for other modules (`seed/<module>/`), once they have tables.
6. [ ] Decide migration numbering across modules (open decision 12).
