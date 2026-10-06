# Module map

| Module | Purpose | Submodules | Depends on | Privacy |
|---|---|---|---|---|
| `household` | Household setup, members, settings, health, personal insights | setup, members, settings, health, insights | core | sensitive |
| `planner` | Calendar, reminders, chores, tasks, routines, timeline (one connected system) | calendar, reminders, chores, tasks, routines, timeline | household | normal |
| `kids` | School plan, activities and festivals, learning, rewards, kid-view | school, activities, learning, rewards, kid-view | household, planner, (finance) | strict |
| `energy` | Production, consumption, pricing, forecast, appliance suggestions | overview, pricing, forecast, appliance-planner | household, devices, planner | normal |
| `devices` | Device overview, Home Assistant connector, appliances, climate, maintenance | overview, home-assistant, appliances, climate, maintenance | household | normal |
| `finance` | Shared and personal money for couples, flatmates, families | accounts, shared-expenses, budgets, recurring-bills, goals, insights | household, (kids) | sensitive |

Platform (not a module): `core/` — module registry, UI shell and layout, enablement, trust layer, connectors, permissions, cross-module contracts. See `docs/core/`.

## Entity ownership (one owner each)
| Entity | Owner | Used by |
|---|---|---|
| Household, Member, Role, Profile | household | all |
| Health metric | household/health | household/insights |
| Calendar source, Event, Availability | planner/calendar | kids, energy |
| Reminder | planner/reminders | kids, finance (bill reminders) |
| Chore (and rules) | planner/chores | kids/rewards, energy/appliance-planner |
| Task | planner/tasks | household |
| Reward balance, Perk | kids/rewards | finance (allowance, optional) |
| School plan, Exam | kids/school, kids/learning | planner (as events) |
| Energy reading, Price window, Forecast | energy | planner |
| Device, Appliance state | devices | energy |
| Account, Expense, Balance, Budget, Bill, Goal | finance | planner (due dates), kids (allowance) |

## Dependency direction
household <- planner <- kids; household <- devices <- energy (also reads planner chores); finance depends only on household (optionally kids/planner via contracts). No cycles: if two modules need each other, the shared concept moves into `core/` or the lower module.

## Ownership by people
Each module has an owner in its README (`Owner: TBD`). Owners are mirrored in `.github/CODEOWNERS`.

## Legacy code mapping (existing code to migrate later)
| Existing | Will move to |
|---|---|
| `server/chit_store/` (encrypted store) | `core/store` (generic) and `modules/household` / `modules/planner` (entities) |
| `server/run.py` | `core/server` (shell, routing) |
| `dashboard/household-setup.html` | `modules/household/submodules/setup/web` |
| `dashboard/calendar-home.html`, calendar code | `modules/planner/submodules/calendar` |
| `js/weather.js` | candidate shared connector in `core` |
| `js/tibber.js` | `modules/energy/submodules/pricing` |
| `js/components/chit-ribbon.js` | `core/web` |
| `dashboard/archive/` | stays archived |
