# Glossary

| Term | Definition |
|---|---|
| Actual | A value obtained from a connected system as an observation or measurement. |
| Attention card | A limited, prioritised item explaining something that may require review. |
| Availability | A calendar-supported indication that a person is busy, free or unknown; absence of data is never free. |
| Connector | An adapter that retrieves data from an external provider and maps it to Chit's normalized model. |
| Data state | The declared interpretation of a value: measured, forecast, manual, unavailable or demo. |
| Household | The top-level tenant containing members, sources, displays and policies. |
| Ingested time | The time Chit received a record. |
| Observed time | The time the underlying event or measurement occurred. |
| Provenance | Metadata describing where information came from and when it was observed and ingested. |
| Screen-safe mode | A presentation policy that removes or masks sensitive information on a shared display. |
| Source | The calendar, weather service, Home Assistant instance, inverter, tariff provider or person providing data. |
| Stale | Available information older than the configured freshness threshold for its source type. |
| Module | A self-contained product area (household, planner, kids, energy, devices, finance) with its own data, contracts, cards and manifest. |
| Submodule | An independently enable-able part of a module (e.g. planner/chores). |
| Card | The unit of UI composition: a registered, self-contained widget with sizes, surfaces, permissions and data states. |
| View | A full-screen page contributed by a module or submodule. |
| Shell | The core UI that resolves enablement and layout and arranges registered cards. |
| Surface | A target display or client: tv, tablet, web, mobile-adult, mobile-kid. |
| Audience | Who a view is for: adult, child, guest. |
| Enablement | The layered configuration (preset, household, member, surface) deciding which modules, submodules and cards a viewer sees. |
| Household preset | Default module set by household type: single, couple, family-with-children, shared-flat. |
| Manifest | `module.manifest.yaml` declaring a module's submodules, cards, permissions, dependencies and events. |
| Contract | A module's public read APIs and events; the only way other modules may use its data. |
| Shared ledger | Finance records visible to all members of a household, as distinct from personal ledgers. |
| Stars | Reward points a child earns for completed chores, redeemable for perks (kids/rewards). |

