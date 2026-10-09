"""Postgres support for the hosted profile (ADR-0015). Runs next to the SQLite store, which stays the standby.

Only connection handling, the migration runner and role grants live here; the store's query code is ported separately.
"""
from __future__ import annotations

from pathlib import Path

import psycopg
from psycopg import sql

PG_MIGRATIONS = Path(__file__).parent / "pg_migrations"
# Arbitrary constant: concurrent instances take this advisory lock so only one runs migrations at a time.
MIGRATION_LOCK_ID = 7_341_902


def connect(url: str, autocommit: bool = False) -> "psycopg.Connection":
    return psycopg.connect(url, autocommit=autocommit)


def migrate(url: str) -> list[str]:
    """Apply pending migrations from pg_migrations/ in order, each in its own transaction. Returns the versions applied."""
    applied_now: list[str] = []
    with connect(url) as connection:
        connection.execute("SELECT pg_advisory_lock(%s)", (MIGRATION_LOCK_ID,))
        try:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
            connection.commit()
            done = {row[0] for row in connection.execute("SELECT version FROM schema_migrations")}
            for path in sorted(PG_MIGRATIONS.glob("*.sql")):
                if path.name in done:
                    continue
                try:
                    connection.execute(path.read_text(encoding="utf-8"))
                    connection.execute(
                        "INSERT INTO schema_migrations(version, applied_at) VALUES (%s, to_char(now() AT TIME ZONE 'UTC', "
                        "'YYYY-MM-DD\"T\"HH24:MI:SS.US\"+00:00\"'))", (path.name,))
                    connection.commit()
                    applied_now.append(path.name)
                except Exception:
                    connection.rollback()
                    raise
        finally:
            connection.execute("SELECT pg_advisory_unlock(%s)", (MIGRATION_LOCK_ID,))
            connection.commit()
    return applied_now


def grant_app_role(owner_url: str, app_role: str = "chit_app") -> None:
    """Give the application role data access only: no DDL, no ownership. Safe to repeat."""
    ident = sql.Identifier(app_role)
    with connect(owner_url) as connection:
        connection.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(ident))
        connection.execute(sql.SQL(
            "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {}").format(ident))
        connection.execute(sql.SQL("GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO {}").format(ident))
        # the app role never touches the migration bookkeeping
        connection.execute(sql.SQL("REVOKE ALL ON schema_migrations FROM {}").format(ident))
        connection.commit()
