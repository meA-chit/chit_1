# Postgres port audit (input to ADR-0015)

Date: 2026-10-09. Read-only audit of `core/store/chit_store` and its migrations against ADR-0015 (hosted Postgres with row-level security). The schema was inspected by applying all 20 migrations to a throwaway SQLite database; the SQL was grepped. No code was changed.

## Scope

- **All SQL lives in one package**: `core/store/chit_store/*.py` (14 files, 96 `_connection()` call sites). No module or server code touches the database (checked: no `.execute(` or `sqlite` outside the package). Module isolation held, so the port is contained to the store and its migrations.
- **43 tables**, 20 migrations (about 640 lines of SQL), about 276 lines with `?` placeholders.
- Column types: 241 TEXT, 35 INTEGER (flags and counts), 4 REAL. Dates and times are ISO strings in TEXT columns.

## 1. Tenant coverage for row-level security

27 tables already carry `household_id`. **16 do not.** Plan: add `household_id` to the 15 non-root tables (denormalised) and enforce it with composite foreign keys, so RLS policies stay a simple `household_id = current_setting('app.household_id')` and never need joins.

| Group | Tables lacking `household_id` | Parent to reference |
|---|---|---|
| Root tenant | `households` | RLS on `id` itself |
| Via member | `adult_settings`, `child_settings`, `kid_privacy`, `kid_bag_ticks`, `member_modules` | `household_members(id, household_id)` (already `UNIQUE (id, household_id)`) |
| Via member, 2nd level | `adult_work_days`, `child_care_days`, `child_activities`, `child_activity_days` | their settings or activity row |
| Via chore series | `chore_completions`, `kid_chore_outcomes`, `kid_star_chores` | `chore_series` (needs `UNIQUE (id, household_id)`) |
| Kids health and school | `kid_grades`, `kid_med_log` | `kid_subjects`, `kid_meds` (need the same unique) |
| Devices | `kid_phone_handoffs` | `kid_phone_devices` |

Priority: `kid_med_log` and `kid_grades` hold the most sensitive data (health, grades), so they go first.

**Two design issues found, not in the ADR yet**
1. **`planner_skips` primary key is `(kind, item_id, day)` with no `household_id`.** Two households could collide on the key. It must become `(household_id, kind, item_id, day)`. Check other composite keys for the same flaw (`kid_bag_ticks`, `kid_med_log`, `reminder_states` are scoped through their parent, which is acceptable once `household_id` is added).
2. **Lookups that happen before the household is known.** A kid device token (`kid_phone_devices`, `kid_phone_handoffs`) and a pairing code must be resolved to a household before `app.household_id` can be set. With RLS on, that first query would return nothing. Needs an explicit design: either a small `auth`-schema lookup table (token hash → household) outside RLS, or a `SECURITY DEFINER` function. Same for adult pairing and email-code redemption (ADR-0014).

## 2. SQLite-specific code to replace

| # | Item | Where | Port |
|---|---|---|---|
| 1 | `?` placeholders | about 276 lines, all store files | Mechanical: wrap the connection so `?` becomes the driver's `%s` in one place, or rewrite. |
| 2 | `ORDER BY ..., rowid` | 13 sites in `chore_series`, `reminders`, `documents`, `common` (`LATEST_HOUSEHOLD_ORDER`) | Postgres has no `rowid`. Add `seq BIGINT GENERATED ALWAYS AS IDENTITY` to the affected tables and order by it. Includes ordered junction tables whose order is meaningful (`child_pickup_adults`, `child_dropoff_adults`, `calendar_source_members`, `chore_rule_assignees`: first adult in list is the primary). Backfill `seq` from `rowid` in the one-time import. |
| 3 | `INSERT OR IGNORE` | 5 sites | `INSERT ... ON CONFLICT DO NOTHING`. |
| 4 | `ON CONFLICT ... DO UPDATE SET x = excluded.x` | 13 sites | Same syntax in Postgres; check the conflict target exists as a unique constraint. |
| 5 | `BEGIN IMMEDIATE` | about 25 sites | Becomes plain `BEGIN` plus `SET LOCAL app.household_id`. **See section 3.** |
| 6 | Triggers | 4 in migrations 001 and 002: `household_owner_must_be_adult`, `household_owner_cannot_be_removed`, `child_pickup_assignment_must_be_adult`, `child_dropoff_assignment_must_be_adult` | Rewrite as PL/pgSQL trigger functions. The circular `households.owner_member_id` foreign key is `DEFERRABLE INITIALLY DEFERRED`, which Postgres supports. |
| 7 | Dynamic SQL | `documents.py:259`, `kids.py:65` (table name formatted in), `kid_bag.py:64`, `meter_readings.py:18` (`IN (?,?,...)` lists) | Verify the table names come from a fixed internal allowlist, never user input. `IN` lists become `= ANY(%s)`. |
| 8 | Migration 015 | `randomblob`, `hex`, `strftime`, `COLLATE NOCASE` index | `gen_random_uuid()`/`encode(gen_random_bytes(12),'hex')`, `to_char(now() ...)`, and a unique index on `lower(name)`. |
| 9 | `PRAGMA` and SQLCipher | `store.py` (`key`, `foreign_keys`, `secure_delete`, `busy_timeout`, `journal_mode`) | Removed for the hosted profile. Cloud SQL encrypts at rest and enforces foreign keys. `energy_connections.secret` (provider keys) still needs application-level encryption before that module is enabled. |
| 10 | Connection model | `_access = threading.RLock()` serialises every database call, `_open()` opens a new connection per call | Replace with a small pool (5 to 10 on `db-f1-micro`). |
| 11 | Booleans and dates | 35 INTEGER flags, ISO-string dates | Keep INTEGER (0/1) and TEXT for the port so API output does not change. Revisit `timestamptz` later. |

## 3. The real risk: concurrency semantics

SQLite plus the global lock plus `BEGIN IMMEDIATE` means **every write is serialised**, and read-then-write code is safe by accident. Postgres runs transactions concurrently. Review each read-then-write block for races, especially:
- the `if cursor.rowcount != 1` guards (`chore_series`, `reminders`, `kid_phone`, `store.py`, `kids.py`),
- pairing redemption and attempt counting in `kid_phone.py` (single-use codes and lockout must be atomic: use `UPDATE ... WHERE ... RETURNING` or `SELECT ... FOR UPDATE`),
- the "latest household" lookup and ownership transfer,
- the migration runner (needs an advisory lock so two instances do not migrate at once).

## 4. Tests

The 261 Python tests run on a fresh SQLite file per test. For Postgres they need a harness: a template database cloned per test, or a schema per test with rollback. Without this the suite will be too slow to use. Add the isolation suite (ADR-0015 point 8): two households, every store method, the wrong household's id.

## 5. Suggested order of work

1. Postgres running locally (Postgres.app, version 17). Docker or CI later.
2. Test harness and a `PostgresStore` behind the existing interface; port the migration runner (with advisory lock).
3. Port the 20 migrations to Postgres SQL, adding `seq`, `household_id` columns and composite keys. Run them from empty.
4. Port the store file by file, running that file's tests: `store.py`, `documents.py`, `kids.py` first (the largest).
5. Review concurrency (section 3).
6. RLS policies and a restricted app role. **Local superuser connections bypass RLS, so tests must use the restricted role.**
7. Isolation suite, then the one-time import from a copy of `data/dev.db`.

Estimate: unchanged at about 3 to 5 focused days. The concurrency review and the RLS retrofit are the parts most likely to run over.
