"""One-time import of a SQLite household database into Postgres (ADR-0015). The SQLite file is never modified.

    PYTHONPATH=core/store python -m chit_store.pg_import --sqlite data/dev.db --env .env.postgres [--replace] [--dry-run]

Steps: apply the Postgres migrations, copy every table in dependency order inside ONE transaction (filling the
household_id and seq columns the SQLite schema lacks), verify row counts and every value against the source, and only
then commit (--dry-run rolls back after verifying). Exit status is non-zero on any mismatch.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

from . import pg

# Parents before children. Checked against the real schema at run time.
TABLE_ORDER = [
    "households", "household_members", "household_modules", "member_modules",
    "adult_settings", "adult_work_days", "child_settings", "child_care_days", "child_activities",
    "child_activity_days", "child_pickup_adults", "child_dropoff_adults",
    "calendar_sources", "calendar_source_members", "chore_generation_rules", "chore_rule_assignees",
    "chores", "chore_assignees", "chore_series", "chore_completions", "reminders", "reminder_states",
    "planner_skips", "energy_connections", "meter_readings",
    "kid_settings", "kid_star_chores", "kid_chore_outcomes", "kid_goals", "kid_subjects", "kid_grades",
    "kid_meds", "kid_med_log", "kid_school_slots", "kid_tasks", "kid_bag_items", "kid_bag_ticks",
    "kid_privacy_policy", "kid_privacy", "kid_phone_access", "kid_phone_devices", "kid_phone_handoffs",
    "kid_phone_pairings",
]

# Tables whose household_id is not in SQLite: (key column, lookup name). Lookups are built from the source below.
DERIVED_HOUSEHOLD = {
    "adult_settings": ("member_id", "member"), "adult_work_days": ("member_id", "member"),
    "child_settings": ("member_id", "member"), "child_care_days": ("member_id", "member"),
    "child_activities": ("member_id", "member"), "kid_bag_ticks": ("member_id", "member"),
    "kid_privacy": ("member_id", "member"), "member_modules": ("member_id", "member"),
    "child_activity_days": ("activity_id", "activity"),
    "chore_completions": ("series_id", "series"), "kid_chore_outcomes": ("series_id", "series"),
    "kid_star_chores": ("series_id", "series"),
    "kid_grades": ("subject_id", "subject"), "kid_med_log": ("med_id", "med"),
    "kid_phone_handoffs": ("device_id", "device"),
}


def load_env(path: str | None) -> None:
    if not path:
        return
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def open_source(path: str, key_hex: str | None):
    """Read-only snapshot of the source into memory, so a running hub's WAL file is never written."""
    if key_hex:
        from sqlcipher3 import dbapi2 as driver
    else:
        driver = sqlite3
    source = driver.connect("file:%s?mode=ro" % path, uri=True)
    if key_hex:
        source.execute("PRAGMA key = \"x'%s'\"" % key_hex)
    snapshot = driver.connect(":memory:")
    source.backup(snapshot)
    source.close()
    return snapshot


def source_tables(src) -> list[str]:
    return [r[0] for r in src.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' AND name != 'schema_migrations'")]


def build_lookups(src) -> dict[str, dict[str, str]]:
    member = dict(src.execute("SELECT id, household_id FROM household_members"))
    return {
        "member": member,
        "series": dict(src.execute("SELECT id, household_id FROM chore_series")),
        "subject": dict(src.execute("SELECT id, household_id FROM kid_subjects")),
        "med": dict(src.execute("SELECT id, household_id FROM kid_meds")),
        "device": dict(src.execute("SELECT id, household_id FROM kid_phone_devices")),
        "activity": {a: member.get(m) for a, m in src.execute("SELECT id, member_id FROM child_activities")},
    }


def pg_columns(connection, table: str) -> list[str]:
    return [r[0] for r in connection.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = %s "
        "ORDER BY ordinal_position", (table,))]


def source_rows(src, table: str, target_cols: list[str], lookups) -> list[tuple]:
    """Rows of one table shaped to the Postgres column list, ordered by rowid to keep insertion order."""
    src_cols = [r[1] for r in src.execute("PRAGMA table_info(%s)" % table)]
    unknown = [c for c in src_cols if c not in target_cols]
    if unknown:
        raise SystemExit("schema drift: %s has SQLite columns missing in Postgres: %s" % (table, unknown))
    select = ", ".join(c for c in src_cols) + ", rowid"
    raw = src.execute("SELECT %s FROM %s ORDER BY rowid" % (select, table)).fetchall()
    index = {c: i for i, c in enumerate(src_cols)}
    rows = []
    for record in raw:
        out = []
        for column in target_cols:
            if column in index:
                out.append(record[index[column]])
            elif column == "seq":
                out.append(record[-1])
            elif column == "household_id" and table in DERIVED_HOUSEHOLD:
                key_column, lookup = DERIVED_HOUSEHOLD[table]
                household = lookups[lookup].get(record[index[key_column]])
                if household is None:
                    raise SystemExit("orphan row in %s: %s=%r has no parent household" % (table, key_column, record[index[key_column]]))
                out.append(household)
            else:
                raise SystemExit("cannot fill %s.%s from the source" % (table, column))
        rows.append(tuple(out))
    return rows


def import_all(src, connection, replace: bool) -> dict[str, int]:
    src_tabs = set(source_tables(src))
    pg_tabs = {r[0] for r in connection.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name != 'schema_migrations'")}
    if src_tabs != set(TABLE_ORDER) or pg_tabs != set(TABLE_ORDER):
        raise SystemExit("table sets differ. only in SQLite: %s | only in Postgres: %s | missing from TABLE_ORDER: %s" % (
            sorted(src_tabs - pg_tabs), sorted(pg_tabs - src_tabs), sorted((src_tabs | pg_tabs) - set(TABLE_ORDER))))
    if connection.execute("SELECT count(*) FROM households").fetchone()[0]:
        if not replace:
            raise SystemExit("target already has data; pass --replace to wipe it first (development databases only)")
        connection.execute("TRUNCATE %s CASCADE" % ", ".join(TABLE_ORDER))
    lookups = build_lookups(src)
    counts: dict[str, int] = {}
    for table in TABLE_ORDER:
        columns = pg_columns(connection, table)
        rows = source_rows(src, table, columns, lookups)
        if rows:
            placeholders = ", ".join(["%s"] * len(columns))
            with connection.cursor() as cursor:
                cursor.executemany("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(columns), placeholders), rows)
        if "seq" in columns:
            connection.execute(
                "SELECT setval(pg_get_serial_sequence(%s, 'seq'), COALESCE(MAX(seq), 1), MAX(seq) IS NOT NULL) FROM " + table,
                (table,))
        counts[table] = len(rows)
    return counts


def verify(src, connection, counts: dict[str, int]) -> list[str]:
    """Compare every row and value, in insertion order, with the source. Returns a list of problems (empty = identical)."""
    problems: list[str] = []
    lookups = build_lookups(src)
    for table in TABLE_ORDER:
        columns = pg_columns(connection, table)
        expected = source_rows(src, table, columns, lookups)
        actual = connection.execute("SELECT %s FROM %s ORDER BY seq NULLS LAST" % (", ".join(columns), table)
                                    if "seq" in columns else "SELECT %s FROM %s" % (", ".join(columns), table)).fetchall()
        if len(expected) != len(actual):
            problems.append("%s: %d rows in SQLite, %d in Postgres" % (table, len(expected), len(actual)))
            continue
        if "seq" in columns:
            if [tuple(r) for r in actual] != expected:
                problems.append("%s: values or order differ" % table)
        elif sorted(map(repr, expected)) != sorted(repr(tuple(r)) for r in actual):
            problems.append("%s: values differ" % table)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sqlite", required=True, help="source database (opened read-only)")
    parser.add_argument("--key-hex", help="SQLCipher key for an encrypted source")
    parser.add_argument("--env", help="file with CHIT_PG_OWNER_URL (and CHIT_PG_APP_URL)")
    parser.add_argument("--target", default="CHIT_PG_OWNER_URL", help="env var holding the owner connection URL")
    parser.add_argument("--replace", action="store_true", help="wipe the target tables first")
    parser.add_argument("--dry-run", action="store_true", help="import and verify, then roll back")
    args = parser.parse_args()
    load_env(args.env)
    url = os.environ.get(args.target)
    if not url:
        raise SystemExit("%s is not set (use --env .env.postgres)" % args.target)

    print("migrations applied:", pg.migrate(url) or "none (already current)")
    src = open_source(args.sqlite, args.key_hex)
    with pg.connect(url) as connection:
        counts = import_all(src, connection, args.replace)
        problems = verify(src, connection, counts)
        for table in TABLE_ORDER:
            print("  %-26s %5d rows" % (table, counts[table]))
        if problems:
            connection.rollback()
            print("\nVERIFICATION FAILED, nothing committed:", *problems, sep="\n  - ")
            return 1
        if args.dry_run:
            connection.rollback()
            print("\nDry run: all %d tables identical to the source; rolled back." % len(TABLE_ORDER))
            return 0
        connection.commit()
    app_url = os.environ.get("CHIT_PG_APP_URL")
    if app_url:
        pg.grant_app_role(url)
    print("\nImported and verified: %d tables, %d rows. Source untouched." % (len(TABLE_ORDER), sum(counts.values())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
