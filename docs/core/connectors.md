# Connectors

External sources enter through connectors in `core/server` that emit normalized records with provenance. Modules consume normalized records, never raw provider payloads. Connectors are shared platform code; a module declares which connectors it needs in its manifest.

## Connector contract
1. Authentication and secret references
2. Capability declaration
3. Retrieval or subscription
4. Mapping to normalized entities
5. Health, error and freshness reporting

Contract tests verify required provenance and graceful failure. Connectors protect secrets server-side (no tokens in browser code), enforce size/time limits, and block unsafe destinations (no private/loopback addresses for user-supplied URLs).

## Catalogue
| Connector | Used by | Access | Pilot? | Failure behaviour |
|---|---|---|---|---|
| Calendar (iCal/webcal) | planner/calendar, kids/school, kids/activities | Read-only | Yes | Events unavailable; no inferred availability |
| Weather (Open-Meteo) | planner/weather, energy/forecast | Read-only | Yes | Card unavailable or stale |
| Home Assistant | devices/*, energy/overview | Read-only token + entity allowlist | Optional | Cards degrade independently |
| Solar inverter (direct or via HA) | energy/overview | Read-only | Optional | Actuals unavailable; forecast stays distinct |
| Dynamic tariff (e.g. Tibber) | energy/pricing | Read-only | Optional | No price-based suggestion without evidence |
| Health providers | household/health | Read-only, per-person consent | Post-pilot | Metric unavailable |
| Bank/transaction import | finance/accounts | Read-only, per-person consent | Post-pilot (manual first) | Account stale/unavailable |
| School systems / timetable import | kids/school | Read-only | Post-pilot | Plan unavailable |
| Document intake (image/PDF) | planner/calendar, kids/school | Human-reviewed | Post-pilot | Nothing saved as confirmed without review |

## Secrets
Keep secret values outside source control. Config may hold environment-variable or secret-store references only.

## Side-effect boundary
Pilot connectors expose no command execution. Any write capability needs a separate ADR, least-privilege credentials, explicit confirmation and auditable commands (applies to Home Assistant control, messaging, calendar write-back and any payment/transfer).
