"""Energy provider connections (energy module): Tibber token, SolarEdge site and key.

Secrets stay inside the hub. `list_energy_connections` never returns a secret, only a masked hint and the
non-secret config, so it is safe to hand to the web client. `get_energy_connection` is for provider clients.
"""
from __future__ import annotations

import json
from typing import Any

from .common import _now

PROVIDERS = ("tibber", "solaredge")


def _provider(value: str) -> str:
    if value not in PROVIDERS:
        raise ValueError("provider must be one of %s" % ", ".join(PROVIDERS))
    return value


class EnergyConnections:
    def set_energy_connection(self, household_id: str, provider: str, secret: str, config: "dict[str, Any] | None" = None) -> None:
        provider = _provider(provider)
        secret = (secret or "").strip()
        if not secret:
            raise ValueError("the key or token must not be empty")
        with self._connection() as connection:
            if not connection.execute("SELECT 1 FROM households WHERE id = ?", (household_id,)).fetchone():
                raise LookupError("household does not exist")
            connection.execute(
                "INSERT INTO energy_connections(household_id, provider, secret, config, updated_at) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(household_id, provider) DO UPDATE SET secret = excluded.secret, config = excluded.config, "
                "updated_at = excluded.updated_at",
                (household_id, provider, secret, json.dumps(config or {}, sort_keys=True), _now()))
            connection.commit()

    def get_energy_connection(self, household_id: str, provider: str) -> "dict[str, Any] | None":
        """Server-side only: includes the secret."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT secret, config FROM energy_connections WHERE household_id = ? AND provider = ?",
                (household_id, _provider(provider))).fetchone()
        return {"secret": row[0], "config": json.loads(row[1])} if row else None

    def list_energy_connections(self, household_id: str) -> "dict[str, dict[str, Any]]":
        """Safe for clients: config plus a masked hint of the secret (last four characters)."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT provider, secret, config, updated_at FROM energy_connections WHERE household_id = ?",
                (household_id,)).fetchall()
        return {provider: {"config": json.loads(config), "hint": secret[-4:] if len(secret) >= 8 else "", "updated_at": updated}
                for provider, secret, config, updated in rows}

    def delete_energy_connection(self, household_id: str, provider: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM energy_connections WHERE household_id = ? AND provider = ?", (household_id, _provider(provider)))
            connection.commit()
            return cursor.rowcount > 0
