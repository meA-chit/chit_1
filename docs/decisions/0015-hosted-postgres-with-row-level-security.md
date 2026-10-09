# ADR-0015: Hosted storage: PostgreSQL (Cloud SQL) with row-level security

- Status: Proposed
- Date: 2026-10-09
- Deciders: product owner
- Relates to: ADR-0004 (SQLite + SQLCipher; this replaces it **for the hosted profile**, once accepted), ADR-0010 (SQLite runtime for dev/pilot), ADR-0013 (hosted profile), ADR-0014 (identity), open decisions 12 and 15

## Context
The hosted profile is multi-household. Two storage shapes were considered: a SQLite file per household, and one shared Postgres database. The current store is SQLite-specific. Measured on 2026-10-09: 20 migration files (about 640 lines of SQL), roughly 230 `execute` calls, `ORDER BY ..., rowid` used for stable ordering in four modules, triggers in two migration files (including the "owner must be an adult" and "owner cannot be removed" rules), SQLCipher key handling, `?` placeholders and SQLite date and `INSERT OR` forms.

Schema changes are certain as features are added. A file per household turns every migration into a fleet job (N runs, possible partial failure, no single rollback), and SQLite's limited `ALTER` already forced a table rebuild (migration 015). Postgres offers one migration run, transactional DDL and point-in-time recovery.

## Decision
1. **Hosted data lives in one Cloud SQL for PostgreSQL database** (ADR-0013), in the EU region, with automated backups and point-in-time recovery enabled. Tier: at least a dedicated-core small instance for the pilot (not the shared-core micro tier).
2. **Tenant isolation by row-level security (RLS).**
   - Every tenant table has a non-null `household_id`. Tables keyed only by `member_id` today (for example `adult_settings`, `child_settings`) gain a `household_id` column, populated by migration and kept consistent by a foreign key to `household_members (id, household_id)`.
   - Each request runs in a transaction that sets `app.household_id` (from the session's membership, ADR-0014) with `SET LOCAL`. RLS policies allow only rows where `household_id = current_setting('app.household_id')`.
   - The application connects as a role that **does not own the tables and cannot bypass RLS**. Migrations run as a separate owner role.
   - Authentication tables (accounts, memberships, pairings, one-time codes, sessions, terms acceptance) live in a separate `auth` schema, not under tenant RLS, and are reachable only through the auth module.
   - **Composite keys carry the tenant.** Any primary or unique key that identifies a tenant row includes `household_id` (the audit found `planner_skips` keyed by `(kind, item_id, day)` only, which would let two households collide; it becomes `(household_id, kind, item_id, day)`).
   - **Lookups before the household is known** (kid device tokens, pairing codes, email-code redemption) cannot run under RLS, because `app.household_id` is not set yet. They go through a narrow `auth`-schema lookup table (token hash to household and role) or a `SECURITY DEFINER` function, and the result then sets `app.household_id` for the rest of the request.
   - The full per-table list (which tables lack `household_id` and what they reference) is in [`docs/core/postgres-port-audit.md`](../core/postgres-port-audit.md).
3. **Port behind the existing store interface** (`chit_store`). Replace SQLite specifics: `?` to the driver's placeholder, `rowid` ordering to an explicit ordering column or identity, the two trigger sets to constraints or PL/pgSQL (owner rules also enforced in application code), SQLite date functions to Postgres equivalents, and drop SQLCipher (Cloud SQL encrypts at rest; application-level secrets such as energy credentials still need their own encryption before that module is enabled).
4. **Migrations.** Keep the numbered SQL runner, add a Postgres advisory lock so two instances never migrate at once, run migrations as a deploy step, and use **expand-then-contract** (add, dual-write, backfill, switch, drop) for any change that is not backward compatible.
5. **Local development and CI run real Postgres** (Docker Compose; testcontainers or a service container in CI). Tests do not substitute SQLite for Postgres.
6. **Existing data.** `data/dev.db` is a real household and is never modified. A one-time import script reads it read-only and loads it into a Postgres household. Tests that write use a copy.
7. **SQLite stays only as a time-boxed fallback** (ADR-0013 point 6). After the Postgres cutover the hosted profile does not run on SQLite, and the two dialects are not maintained in parallel for hosted features. Whether the local hub profile keeps SQLite is a separate decision (see Revisit).
8. **Isolation tests are mandatory.** A suite creates at least two households and exercises every route and every store method with the other household's session and identifiers; each must return nothing or an authorization error. A test that runs a tenant query without `app.household_id` set must return no rows.

## Implementation status (2026-10-09)
Migrations `002` and `003` in `core/store/chit_store/pg_migrations/` implement points 2 and 3, tested by `core/store/tests/test_isolation.py` (21 tests, run as the restricted role, including the real kid-phone gateway over HTTP).
- **Scope is per request, set by the server, never by query code.** `store.request_scope(household)` opens it; `default_scope()` supplies the household in single-household mode (`CHIT_SINGLE_HOUSEHOLD=1`, the local hub and pilot before accounts). A store method that receives a `household_id` does not widen what the connection may see. With accounts (ADR-0014) the server will pass the session's household.
- **Pre-household lookups** use two `SECURITY DEFINER` functions with a pinned `search_path`, returning only a household id: `chit_household_for_phone_credential(kind, hash)` and `chit_latest_household_id()` (answers only in single-household mode). A credential can bind a request to its household but can never move a request that already serves another one (`PermissionError`).
- **The owner role bypasses RLS on purpose** (migrations, import, admin tasks); policies are not `FORCE`d. The application must connect as a different, non-owner role. The suite fails if a table lacks RLS or a policy, or if the application role owns or bypasses anything.
- **Known limit.** The scope is a session setting. Anyone who can run arbitrary SQL as the application role could re-point it, so RLS defends against bugs in query code, not against SQL injection. All values are bound parameters; the few places that format a table name use fixed internal names. Pooled connections must reset the setting before reuse (today each use opens its own connection).
- **Not done yet:** household creation by the application role (sign-up) must bind the new household before inserting it; accounts, sessions and the operator console (ADR-0014).

## Options considered
- **SQLite file per household plus an accounts database.** Isolation by construction, and almost no port. Rejected as the long-term choice because schema evolution becomes a fleet operation and cross-household features (linked child) need file-spanning designs. It remains the temporary fallback.
- **One shared SQLite database with `household_id` filters.** Isolation depends on every query being right; one miss leaks a family. Rejected.
- **Postgres with application-level filtering only (no RLS).** Same weakness as above; RLS adds a database-enforced second line of defence for little cost. Rejected.
- **Cloud SQL vs self-run Postgres.** Managed backups, recovery and patching matter more than cost while the data includes children's information (ADR-0013).
- **ORM rewrite (for example SQLAlchemy).** Larger change than needed for the pilot. May be revisited; the store interface keeps this open.

## Consequences
- **Concurrency changes.** SQLite with a global lock and `BEGIN IMMEDIATE` serialises every write, so read-then-write code is safe today by accident. On Postgres each such block (about 25 sites, notably pairing-code redemption and attempt counting) must be made atomic with `UPDATE ... RETURNING`, `SELECT ... FOR UPDATE`, or unique constraints. See the audit.
- A port of roughly 3 to 5 focused days with tests (estimate from the audit in `docs/core/postgres-port-audit.md`; the concurrency review and the RLS retrofit are the parts most likely to run over). Risk areas: ordering by `rowid`, triggers, date arithmetic, and any dynamic SQL.
- RLS requires the `household_id` audit above; it overlaps with open decision 15 (data class per table).
- Per-request transaction and `SET LOCAL` add small overhead and require connection handling that never leaks the setting between requests (use `SET LOCAL` inside a transaction only, and test it).
- ADR-0004 (SQLCipher) and ADR-0010 (SQLite runtime) continue to describe the local profile only.
- Open decision 12 (migration strategy) is resolved for the hosted profile by point 4.

## Revisit when
- A home hub exists: decide whether it keeps SQLite and how it syncs with hosted Postgres (one schema, two engines, or one engine everywhere).
- Load or isolation needs outgrow one database (read replicas, per-region instances).
- An ORM or typed query layer is justified by the number of modules touching the store.
