# Module map

| Module | Purpose | Submodules | Depends on | Privacy | Stories |
|---|---|---|---|---|---|
| `household` | Household setup, members, settings, health, personal insights | setup, members, settings, health, insights | core | sensitive | none yet |
| `planner` | Calendar, reminders, chores, tasks, routines, timeline, weather, time intelligence | calendar, reminders, chores, tasks, routines, timeline, weather, time-intelligence (deferred) | household | normal | US-103, 202, 203, 401 |
| `kids` | School plan, activities and festivals, learning, rewards, kid-view | school, activities, learning, rewards, kid-view | household, planner, (finance) | strict | none yet |
| `energy` | Production, consumption, pricing, forecast, appliance suggestions | overview, pricing, forecast, appliance-planner | household, devices, planner | normal | US-402, 403, 405, 406 |
| `devices` | Device overview, Home Assistant connector, appliances, climate, maintenance | overview, home-assistant, appliances, climate, maintenance | household | normal | US-104, 404 |
| `finance` | Shared and personal money for couples, flatmates, families | accounts, shared-expenses, budgets, recurring-bills, goals, insights | household, (kids) | sensitive | none yet |

Platform (not a module): `core/` — module registry, UI shell and layout, enablement, trust layer, connectors, permissions, attention service, encrypted store, shared contracts. Docs: `docs/core/`. Stories: US-101/102/105/106, 201/204, 301–305, 501–503 (`docs/core/stories/`).

## Entity ownership (one owner each)
| Entity | Owner | Used by |
|---|---|---|
| Household, Member, Role, Profile | household | all |
| Health metric | household/health | household/insights |
| Calendar source, Event, Availability | planner/calendar | kids, energy |
| Weather observation/forecast | planner/weather | energy/forecast |
| Reminder | planner/reminders | kids, finance (bill reminders) |
| Chore (and rules) | planner/chores | kids/rewards, energy/appliance-planner |
| Task, Routine | planner/tasks, planner/routines | household |
| Reward balance, Perk | kids/rewards | finance (allowance, optional) |
| School plan, Exam, Activity plan | kids/school, kids/learning, kids/activities | planner (as events) |
| Energy reading, Price window, Forecast | energy | planner |
| Device, Appliance state | devices | energy |
| Account, Expense, Balance, Budget, Bill, Goal | finance | planner (due dates), kids (allowance) |
| Insight / Attention card | core (attention service) | all surfaces |

## Dependency direction
household <- planner <- kids; household <- devices <- energy (also reads planner chores); finance depends on household (optionally kids/planner through contracts). No cycles: when two modules need each other, move the shared concept into `core/` or the lower module.

## Ownership by people
Owners are listed in each module README (`Owner: TBD`) and mirrored in `.github/CODEOWNERS`.

## Legacy code mapping (existing code to migrate in the rework)
| Existing | Target |
|---|---|
| `server/chit_store/` | `core/store` (engine, migrations runner) and module-owned tables (`household_*`, `planner_*`) |
| `server/run.py` | `core/server` (routing, policy) |
| `dashboard/household-setup.html` | `modules/household/submodules/setup/web` |
| `dashboard/calendar-home.html`, calendar reader in `run.py` | `modules/planner/submodules/calendar` |
| `js/weather.js` | `modules/planner/submodules/weather` (+ core connector) |
| `js/tibber.js` | `modules/energy/submodules/pricing` (+ core connector, server-side) |
| `js/components/chit-ribbon.js` | `core/web` |
| child care/activity schedules in household store | `modules/kids/submodules/{school,activities}` |
| `dashboard/archive/` | stays archived |
