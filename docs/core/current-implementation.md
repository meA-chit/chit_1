# Current implementation snapshot (2026-10-06, branch `devs`)

Purpose: give the code-rework phase an accurate baseline. Not a requirements document.

## Inventory (after the rework)
| Area | Location | State |
|---|---|---|
| Hub server | `core/server/chit_server` | Router, manifest registry, `/api/shell`, SPA + legacy static serving; loopback `127.0.0.1:8765` (`CHIT_PORT`) |
| Store | `core/store/chit_store` (+ migrations `001`, `002`) | Solid: transactions, validation, SQLCipher, owner-only permissions; still one shared store |
| Module routes | `modules/household/submodules/setup/server`, `modules/planner/submodules/calendar/server` | `/api/household/{summary,setup}`, `/api/planner/calendar/agenda` |
| Web client | `apps/web` + `core/web/src` + submodule `web/index.ts` | React/Vite shell, design system, two cards (agenda, household summary) |
| Household setup/edit | `modules/household/submodules/setup/web` + `server/routes.py` | React form for create and edit; prototype HTML archived in `dashboard/archive/household-setup-prototype/` |
| Seed data | `seed/households/*.json`, `core/store/chit_store/cli.py` | ADR-0010; `npm run seed`, `npm run export`; dev hub auto-seeds an empty plain database |
| Tests | `core/server/tests`, `core/store/tests`, `modules/*/submodules/*/tests`, `*.test.ts` | `npm run check` |

| Dashboard | `core/web/src/shell`, `modules/planner/submodules/{timeline,chores,calendar,weather}`, energy/devices demo cards | Rail + top bar + timeline + 3 columns; design reference `docs/design/home-dashboard/` |
| Chores | `core/store/chit_store/chore_series.py` (+ migrations 005, 006), `planner/chores` routes | Recurring chores (weekdays + day part) with computed streaks; scheduled in household settings, ticked off on the dashboard |
| Reminders | `core/store/chit_store/reminders.py` (+ migrations 006, 007), `planner/reminders` routes | One-off on a picked date, by day part; shown in timeline zone bands and the to-do card |
| Energy | `modules/energy/{shared,submodules/{pricing,solar,appliance-planner,connections,overview}}`, `core/store/chit_store/energy_connections.py` (migration 009) | Tibber hourly price + consumption, SolarEdge production, expected-solar estimate, best-two-windows suggestions; keys set in household energy settings (ADR-0011) |
| Child commute | migration 008, `planner/timeline` routes, `household/setup/web/MemberCard.tsx` | School trips by walk/cycle/car; activities with commute mode, travel time and independent or parent-accompanied |
| Kids | `core/store/chit_store/kids.py` (migration 010), `modules/kids/{shared,submodules/*}` | Stars and goals, grades (German scale, written/oral, main/other), school-day plan, medication; `/kids` page (parents manage, a child sees their own) and the `kids-goals` dashboard card; seed in `seed/kids/` |
| Skips | `core/store/chit_store/skips.py` (+ migration 007) | Skip a chore or reminder for one day; undoable; does not break streaks |

## Commands
`npm install` · `npm run dev:all` (dev hub on an unencrypted, auto-seeded database + client with hot reload) · `npm run hub` (encrypted; needs `CHIT_DB_KEY_HEX`, `CHIT_DB_PATH`) · `npm run seed` / `npm run export` · `npm run build` · `npm run check`.

## Known gaps against the rules
1. No authentication (ADR-0007, interim). Blocks mobile, TV over LAN, hosted profile (open decision 2).
2. Provenance and data states are carried only as far as `state`/`checked_at` on the agenda; not end-to-end (ADR-0003, US-102).
3. Weather (Open-Meteo), Tibber and SolarEdge are served by the hub; the archived browser-side prototypes are gone. Tibber and SolarEdge were not exercised against live accounts (see the energy README); tariffs other than Tibber are not supported.
4. Calendar parsing ignores `RRULE`, treats floating times as UTC, caps at 100 events, fetches on every request without caching.
5. Calendar feed URLs are user-supplied and fetched without blocking private/loopback addresses (SSRF).
6. No linting or CI although the definition of done requires them. API payload types are hand-written, not generated from OpenAPI.
7. Child care/activity schedules are stored inside household setup; conceptually `kids`.
8. Raspberry Pi display cannot reach a loopback-only hub (ADR-0007 conditions).
9. Submodule-level enablement is not stored; "View as" is not access control.
10. Seed households have example calendar feeds, so the agenda shows *unavailable* until a real feed is entered (no demo events yet).
11. The climate card shows demo data (no connector). Energy cards show nothing until a Tibber token / SolarEdge key is saved. Weather and the solar estimate need household latitude/longitude and network access from the hub. Stored energy keys are plain text in the unencrypted dev database; the connection endpoints are not owner-restricted until identity exists (ADR-0011).
12. The timeline merges calendar-feed events client-side by member *name*; feed-to-member mapping by id is a follow-up. Child blocks have no start unless a drop-off time is entered.
13. Kids: grades and medication are parents-only in the UI only (no identity yet, ADR-0007); medication reminders at dose time and name-free shared-screen entries are not built; star chores need a household chore with an assignee.
14. Record ids are global: two seed households must not reuse member or calendar ids.

Resolved by the rework: static path traversal check (now `is_relative_to`), `argon2-cffi` and the placeholder auth test removed, module isolation check added (`npm run check:isolation`).
