# Pilot Scope

## Objective

Validate that households find a trustworthy shared overview useful before investing in broad agent autonomy.

## Modules in the pilot
Pilot work touches `core`, `household` (setup), `planner` (calendar, chores, weather), `devices` (Home Assistant, appliances) and `energy`. The `kids`, `finance` and `household` health/insights modules are not in the pilot (see `roadmap.md`).

## Delivery slices

| Slice | Objective | Story range |
|---|---|---|
| Pilot 1: Trusted foundation | Real source ingestion, normalized provenance, local access and privacy | US-101–US-106, US-301–US-304 |
| Pilot 2: Shared daily view | Readable household dashboard, availability and read-only appliance context | US-201–US-204, US-305, US-401, US-404 |
| Pilot 3: Energy context | Clearly separated solar forecast/actuals and explainable suggestions | US-402–US-406 |
| Pilot 4: Focused attention | Bounded, explainable and dismissible attention cards | US-501–US-503 |

## Minimum usable pilot

Must Have stories define the minimum usable pilot. Should Have stories are delivered only when they do not put trust, privacy or Must Have completion at risk.

## Deferred

- WhatsApp and Telegram queries
- Messaging others or changing schedules
- Appliance control
- AI agents for school, health, finance and tax (the underlying modules are planned post-pilot; see `roadmap.md`)
- Child-facing mobile views and the rewards system
- Shared finance tracking
- Autonomous actions of any kind

## Exit signals

- A household can connect calendar and weather and understand source health.
- Shared-display users can read the day and next three days quickly.
- Users distinguish measured, forecast, manual, unavailable and demo information.
- Screen-safe mode protects sensitive information.
- Energy and attention insights can be explained from their underlying evidence.
