# Product Vision

## Vision

Chit gives a household one trustworthy, always-visible view of what is happening, what is due and what may need attention.

## Product shape
Chit is a modular household operating system. Households enable the modules they need (household, planner, kids, energy, devices, finance); each member and each display surface sees only what is enabled for them. See [`product-context.md`](product-context.md) and [`module-map.md`](module-map.md).

## Pilot promise

The pilot combines real calendar and weather information with optional Home Assistant and energy context. It clearly identifies whether information is measured, forecast, manually entered, unavailable or demonstration data.

## Product principles

1. **Trust before autonomy:** Make information accurate, attributable and understandable before taking actions.
2. **Household decisions over device controls:** Organise data around what people need to know and decide.
3. **Local-first privacy:** Prefer local processing and explicit access boundaries.
4. **Graceful absence:** Missing integrations produce an honest unavailable state, not an invented value.
5. **Explainable attention:** Every suggestion states why it appeared and which sources support it.
6. **Shared-screen safety:** Sensitive details remain hidden unless the viewer is authorised.
7. **Composable by household and person:** Modules, submodules and cards are configured per household, member and surface. Children's views are defined by an adult; sensitive modules are off for shared screens by default.
8. **Incremental integration:** Start with calendar, weather and optional Home Assistant; add providers through stable connector contracts.

## Pilot non-goals

- Autonomous appliance control
- Sending messages or changing schedules without explicit confirmation
- AI agents for health, finance, tax or school (the finance, kids and health *modules* are planned after the pilot; see `docs/releases/roadmap.md`)
- Claiming availability when calendar data is missing
- Presenting demo or forecast data as live measurement
