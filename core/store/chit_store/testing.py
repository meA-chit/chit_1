"""Helpers that let the same test suite run against either storage backend (CHIT_STORE_BACKEND=postgres)."""
from __future__ import annotations

import os
import sqlite3
import unittest

from sqlcipher3 import dbapi2 as _encrypted_sqlite

POSTGRES = os.environ.get("CHIT_STORE_BACKEND") == "postgres"

# For tests of behaviour that only exists in SQLite (file encryption, key format, migrating an old database file).
sqlite_only = unittest.skipIf(POSTGRES, "SQLite-specific")

# What a violated constraint or a refused integrity trigger raises, on either backend.
INTEGRITY_ERRORS: tuple = (sqlite3.IntegrityError, _encrypted_sqlite.IntegrityError)
if POSTGRES:
    import psycopg

    INTEGRITY_ERRORS += (psycopg.errors.IntegrityError, psycopg.errors.RaiseException)
