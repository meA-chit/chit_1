# ADR-0011: Energy provider connections (Tibber, SolarEdge): server-side keys, per-household, verified before storing

- Status: Accepted (scope: development and pilot; production encryption stays governed by ADR-0004)
- Date: 2026-10-06
- Deciders: product owner, energy module owner
- Relates to: ADR-0003 (provenance), ADR-0007 (loopback), ADR-0009 (data classes), ADR-0010 (dev store)

## Context
The energy module now reads real data: Tibber (hourly prices, hourly consumption) and SolarEdge (production). Both need a credential, the household owner types it into the household energy settings, and the dashboard must show nothing until it exists. The archived prototype called Tibber from the browser with a token in JavaScript; that must not return.

## Decision
1. **The hub talks to providers; the browser never does.** Keys stay on the hub. No API returns a key: the client only learns `connected`, a masked hint (last four characters) and non-secret details (SolarEdge site id, plant name and peak power).
2. **One row per household and provider** in `energy_connections` (migration 009): `secret` plus a JSON `config`. Stored in the same SQLite file as the household, so it is encrypted at rest under SQLCipher; in the unencrypted dev mode (ADR-0010) it is plain text and the settings screen says so.
3. **Verify, then store.** `PUT /api/energy/connections/{tibber|solaredge}` calls the provider first. A rejected key is a `400`, an unreachable or rate-limited provider a `502`; nothing is stored in either case.
4. **Never in seed, export or documents.** Credentials are not part of the household document, so seed fixtures, `export` and the edit view cannot carry them.
5. **Honest states.** No key: `unconfigured` (the card says how to connect, no demo values). Key rejected or provider down: `unavailable`, or `stale` with the last good reading and its time. A home without a Tibber Pulse reports consumption as `unavailable`, never as zeros. Estimates (expected solar) are `forecast` and drawn differently from measurements.
6. **Provider limits are respected by caching**: Tibber prices 10 min, consumption 15 min; SolarEdge overview 10 min, hourly curve 20 min (SolarEdge allows 300 calls/day per site); solar forecast 60 min. Error messages never contain URLs because SolarEdge puts its key in the query string.

## Options considered
- **Key in an environment variable / config file.** Simple, but not editable by the household, one key per hub rather than per household, and invisible in the UI. Rejected as the primary path.
- **Key in the browser (localStorage) and calls from the client.** Rejected: leaks the key to every surface and breaks ADR-0007/0009.
- **Home Assistant as the only energy source (ADR-0002).** Good later for inverter/meter data; Tibber prices and SolarEdge cloud data are available now without it. The connections stay behind the energy module's own API, so a Home Assistant source can replace or complement them.

## Consequences
- Easier: a household connects its own accounts in one screen; other modules can read prices and production through the energy API later (public contract) without ever seeing a key.
- Harder: key rotation, multiple Tibber homes (the first running home is used) and multiple solar sites are not handled yet.
- Risk: in dev mode the key is plain text in `data/dev.db`. Mitigation: `data/` is git-ignored, the settings screen warns, production mode refuses plain storage (ADR-0010).
- Revisit: when authentication exists (ADR-0005/0007 follow-up), restrict these endpoints to the household owner; before real family data is stored, encryption on.

## Action items
1. [x] `energy_connections` table, store mixin, `/api/energy/connections`.
2. [x] Tibber prices/consumption, SolarEdge production, expected-solar estimate, best-window suggestions.
3. [ ] Owner-only access to connection endpoints once identity exists.
4. [ ] Multiple Tibber homes / SolarEdge sites, key rotation reminders.
