# Submodule: connections (module `energy`)

> Parent: [`docs/modules/energy/README.md`](../../README.md) · Code: `modules/energy/submodules/connections/`

## Purpose
Tibber and SolarEdge keys in the household energy settings.

## What it does
Contributes the "Energy" section to the household settings screen (`settings_sections` in the manifest). `PUT /api/energy/connections/tibber|solaredge` verifies the key with the provider and stores it in `energy_connections`; `DELETE /api/energy/connections/{provider}` removes it; `GET` returns status only.

## Rules
Keys are never returned, exported or seeded; see [ADR-0011](../../../../decisions/0011-energy-provider-connections.md). The unencrypted development database stores them as plain text.

## Status
Implemented.
