# Local encrypted datastore (`core/store`)

The datastore is a local Python repository backed by SQLCipher-encrypted SQLite. It is exposed through the hub (`core/server`) by module routes, and it does not implement application authentication or member authorization.

## Setup

Use Python 3.9 or newer in a project virtual environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

Generate a development key outside the repository and provide it to the process:

```sh
export CHIT_DB_KEY_HEX="$(openssl rand -hex 32)"
export CHIT_DB_PATH="$PWD/data/chit.db"
```

The key must be exactly 32 random bytes encoded as 64 hexadecimal characters. Do not put the value in a checked-in config file, shell script, or `.env` file. For production, inject it from an operating-system secret store or deployment secret mechanism; key rotation, recovery, backups and unattended service startup need deployment-specific design.

## Run the hub

On macOS, reload the Keychain key into the current terminal and start the loopback-only hub from the repository root:

```sh
source .venv/bin/activate
export CHIT_DB_KEY_HEX="$(security find-generic-password -a "$USER" -s chit-db-key -w)"
export CHIT_DB_PATH="$PWD/data/chit.db"
npm run hub
```

Use `npm run dev` for the UI at <http://localhost:5173>, or `npm run build` and open <http://127.0.0.1:8765/>. The prototype setup form is served at <http://127.0.0.1:8765/legacy/household/setup/household-setup.html>. The hub applies pending encrypted migrations at start-up and listens on `127.0.0.1` only (`CHIT_PORT` changes the port). Stop any older server on the same port first. The flow is intentionally public (ADR-0007).

Subscribed calendar feeds are read on request by `modules/planner/submodules/calendar`; occurrences are not persisted, only source health and last-checked time.

Initialize/use the store from Python:

```python
from chit_store import EncryptedHouseholdStore

store = EncryptedHouseholdStore()
household = store.create_household(
    name="Meyer household",
    owner_name="Nina Meyer",
    timezone_name="Europe/Berlin",
    country_code="DE",
    region="Bayern",
)
```

Set `PYTHONPATH=core/server:core/store` when running scripts from the repository root. The database directory is restricted to the current user where supported; the database file is created with owner-only permissions. SQLite WAL sidecars remain inside that protected directory and are encrypted by SQLCipher.

## Data boundary

Migrations live in `chit_store/migrations/` and are applied at store initialization. The schema stores household/member settings, adult work patterns, child care/activity schedules, read-only calendar subscriptions and member mappings, configured chore rules, and Chit-owned chores with assignees and provenance.

Subscribed calendar occurrences are not mirrored into an event table. A generated chore stores its source occurrence reference and generation-rule reference, and repeated ingestion updates the same chore. Completed or manually edited chores are retained without upstream overwrite.

The repository layer performs storage validation and household referential-integrity checks only. Authentication, authorization, consent and household access policy are deliberately not implemented here.

## Tests

```sh
npm run test:py   # runs every python tests folder
```
