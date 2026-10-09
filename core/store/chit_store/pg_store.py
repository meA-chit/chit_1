"""Postgres backend for the household store (ADR-0015), selected with CHIT_STORE_BACKEND=postgres.

It subclasses the SQLite store and inherits every query method. Only how a connection is opened changes, plus a thin
compatibility layer that translates the few SQLite-isms still present in the shared SQL (see translate()). SQLite stays
the default backend and the standby.

Configuration (environment):
  CHIT_DB_URL        application connection URL (the restricted chit_app role)
  CHIT_DB_OWNER_URL  optional; when set, pending migrations are applied at start-up with this role
  CHIT_SINGLE_HOUSEHOLD=1  serve "the latest household" when a request names none (local hub / pilot before accounts)
  CHIT_PG_TEST=1     test mode: give every store path its own throw-away schema (dropped at exit) in the test database,
                     so the existing test suite runs unchanged. It connects as the OWNER (which bypasses row-level
                     security) unless CHIT_PG_TEST_ROLE=app; the isolation tests use PostgresHouseholdStore.with_role().

Row-level security: every connection is told which household it serves (app.household_id) from the request scope, see
EncryptedHouseholdStore.request_scope. A role that does not own the tables then sees nothing else.
"""
from __future__ import annotations

import atexit
import hashlib
import os
import re
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import psycopg

from . import pg
from .store import EncryptedHouseholdStore

MAX_CONNECTIONS = int(os.environ.get("CHIT_PG_MAX_CONNECTIONS", "8"))  # db-f1-micro allows few; keep headroom
_ROWID = re.compile(r"\browid\b", re.IGNORECASE)
_IS_NOT_PARAM = re.compile(r"\bIS\s+NOT\s+\?", re.IGNORECASE)
_IS_PARAM = re.compile(r"\bIS\s+\?", re.IGNORECASE)
_BEGIN = re.compile(r"^\s*BEGIN\s+(IMMEDIATE|EXCLUSIVE|DEFERRED)\s*$", re.IGNORECASE)

_test_schemas: set[str] = set()


def translate(sql: str, has_params: bool) -> str:
    """Rewrite the SQLite dialect still used by the shared query code. Everything else is already portable SQL."""
    if _BEGIN.match(sql):
        return "BEGIN"
    sql = _ROWID.sub("seq", sql)                       # rowid -> the identity column of the same name semantics
    sql = _IS_NOT_PARAM.sub("IS DISTINCT FROM ?", sql)  # SQLite's null-safe `IS NOT ?`
    sql = _IS_PARAM.sub("IS NOT DISTINCT FROM ?", sql)
    if has_params:
        sql = sql.replace("%", "%%").replace("?", "%s")
    return sql


def _param(value: Any) -> Any:
    return int(value) if isinstance(value, bool) else value   # SQLite stores booleans as 0/1


class _Connection:
    """The slice of the sqlite3 connection API the store uses, on top of a psycopg connection in autocommit mode
    (so explicit BEGIN / commit() / rollback() behave as they do with SQLite's isolation_level=None)."""

    def __init__(self, connection: "psycopg.Connection"):
        self._connection = connection

    def execute(self, sql: str, params: Any = ()) -> "psycopg.Cursor":
        values = tuple(_param(p) for p in params) if params else None
        return self._connection.execute(translate(sql, values is not None), values)

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        self._connection.close()


class PostgresHouseholdStore(EncryptedHouseholdStore):
    backend = "postgres"

    def __init__(self, path: str | Path | None = None, key_hex: str | None = None, plain: bool | None = None):
        # path / key_hex / plain are SQLite concepts, accepted so callers need no change; Postgres encrypts at rest.
        test = os.environ.get("CHIT_PG_TEST") == "1"
        self.plain = False
        self.path = None
        self.key_hex = None
        self.schema: str | None = None
        self.single_household = os.environ.get("CHIT_SINGLE_HOUSEHOLD") == "1"
        if test:
            self._owner_url = _need("CHIT_PG_TEST_OWNER_URL")
            self._url = _need("CHIT_PG_TEST_APP_URL") if os.environ.get("CHIT_PG_TEST_ROLE") == "app" else self._owner_url
            key = str(Path(path).resolve()) if path else os.urandom(8).hex()
            self.schema = "t_" + hashlib.sha1(key.encode()).hexdigest()[:16]
        else:
            self._url = _need("CHIT_DB_URL")
            self._owner_url = os.environ.get("CHIT_DB_OWNER_URL")
        self._slots = threading.BoundedSemaphore(MAX_CONNECTIONS)
        self._initialize()
        self._confined = self._detect_confined()

    @property
    def storage_label(self) -> str:
        return "postgres"

    # The SQLite store serialises all access with a process-wide lock; Postgres handles concurrency itself, so each
    # use gets its own connection (bounded, to respect small instances' connection limits).
    @contextmanager
    def _connection(self) -> Iterator[Any]:
        with self._open() as connection:
            yield connection

    @contextmanager
    def _open(self) -> Iterator[Any]:
        with self._slots:
            options = "-c search_path=%s" % self.schema if self.schema else None
            raw = psycopg.connect(self._url, autocommit=True, options=options)
            try:
                # Session-level on purpose: every use gets its own connection. A pooled connection must RESET these first.
                raw.execute("SELECT set_config('app.household_id', %s, false), set_config('app.single_household', %s, false)",
                            (self.current_household() or "", "on" if self.single_household else "off"))
                yield _Connection(raw)
            finally:
                raw.close()

    def _initialize(self) -> None:
        if self.schema and self.schema not in _test_schemas:
            _test_schemas.add(self.schema)
            atexit.register(_drop_schema, self._owner_url, self.schema)
        if self._owner_url:
            pg.migrate(self._owner_url, schema=self.schema)
            pg.grant_app_role(self._owner_url, os.environ.get("CHIT_DB_APP_ROLE", "chit_app"), schema=self.schema or "public")


    # --- row-level security plumbing ------------------------------------------------------------------------------
    def _detect_confined(self) -> bool:
        """True when this role does not own the tables, i.e. row-level security applies to it."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT c.relowner = (SELECT oid FROM pg_roles WHERE rolname = current_user) FROM pg_class c "
                "WHERE c.relname = 'households' AND c.relnamespace = current_schema()::regnamespace").fetchone()
        return not (row and row[0])

    def with_role(self, url: str) -> "PostgresHouseholdStore":
        """The same database and schema through another role (the isolation tests connect as the application role)."""
        clone = object.__new__(type(self))
        clone.__dict__.update(self.__dict__)
        clone._url = url
        clone._confined = clone._detect_confined()
        return clone

    def _latest_via_function(self) -> "str | None":
        with self._connection() as connection:
            return connection.execute("SELECT chit_latest_household_id()").fetchone()[0]

    def default_scope(self) -> "str | None":
        return self._latest_via_function() if (self._confined and self.single_household) else None

    def _bind_phone_credential(self, kind: str, hashed: str) -> None:
        if not self._confined:
            return
        with self._connection() as connection:
            self.bind_household(connection.execute("SELECT chit_household_for_phone_credential(?, ?)", (kind, hashed)).fetchone()[0])

    # "Latest household" is a single-household idea. Confined, it means the household this request serves.
    def latest_household_id(self) -> "str | None":
        if not self._confined:
            return super().latest_household_id()
        return self.current_household() or (self._latest_via_function() if self.single_household else None)

    def _in_latest(self, method):
        if not self._confined or self.current_household():
            return method()
        household = self._latest_via_function() if self.single_household else None
        if not household:
            return None
        with self.request_scope(household):
            return method()

    def latest_household_summary(self) -> "dict[str, Any] | None":
        return self._in_latest(super().latest_household_summary)

    def latest_household_calendar_sources(self) -> "dict[str, Any] | None":
        return self._in_latest(super().latest_household_calendar_sources)


def _need(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError("%s must be set for the postgres backend" % name)
    return value


def _drop_schema(owner_url: str, schema: str) -> None:
    try:
        with pg.connect(owner_url, autocommit=True) as connection:
            connection.execute('DROP SCHEMA IF EXISTS "%s" CASCADE' % schema)
    except Exception:
        pass
