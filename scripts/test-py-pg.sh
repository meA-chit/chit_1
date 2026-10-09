#!/bin/sh
# Run the Python test suite against local Postgres instead of SQLite (ADR-0015). Needs `scripts/pg-local-setup.sh` once.
# Every store gets a throw-away schema in the chit_test database, dropped at exit.
set -eu
cd "$(dirname "$0")/.."
[ -f .env.postgres ] || { echo "run scripts/pg-local-setup.sh first (creates .env.postgres)"; exit 1; }
set -a; . ./.env.postgres; set +a
export PGGSSENCMODE=disable CHIT_STORE_BACKEND=postgres CHIT_PG_TEST=1
[ -x .venv/bin/python3 ] && PATH="$PWD/.venv/bin:$PATH"
exec scripts/test-py.sh
