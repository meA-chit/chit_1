# Current implementation snapshot (2026-10-06, branch `devs`)

Purpose: give the code-rework phase an accurate baseline. Not a requirements document.

## Inventory
| Area | Files | State |
|---|---|---|
| HTTP server | `server/run.py` | Works: static files, `/api/health`, `/api/home/summary`, `/api/home/calendar`, `POST /api/households/setup` |
| Store | `server/chit_store/store.py`, migrations `001`, `002` | Solid: transactions, validation, SQLCipher, owner-only permissions |
| Pages | `dashboard/household-setup.html`, `calendar-home.html`, `home.html`; prototypes in `dashboard/archive/` | Working prototypes |
| JS | `js/main.js`, `weather.js`, `tibber.js`, `calendar.js` (stub), `components/chit-ribbon.js` | Prototype; `js/config.js` is not in the repo |
| Tests | `server/tests/` (11) | Pass; `test_auth.py` is a placeholder |

## Mapping to modules (target locations)
See `docs/00-overview/module-map.md` (legacy code mapping).

## Known gaps against the rules
1. No authentication while documents described it — resolved in docs by ADR-0007; code and tests still contain leftovers (`argon2-cffi` in `requirements.txt`, placeholder `test_auth.py`).
2. Provenance and data states are not carried end-to-end: the server returns `available/stale/partial/unavailable`; weather and tariff are fetched in the browser without provenance. (ADR-0003, US-102, US-301.)
3. Third-party tokens live in browser-side config (`js/tibber.js` uses a Bearer token from `js/config.js`); there is no `config.example.js`.
4. Calendar parsing ignores `RRULE` recurrence, treats floating times as UTC, and caps at 100 events after sorting; feeds are fetched on every page load without caching.
5. The server fetches user-supplied calendar URLs without blocking private/loopback addresses (SSRF).
6. Static-file traversal check uses string prefix comparison; use path-relative checks.
7. No linting, type checks or CI although the definition of done requires them.
8. Child care/activity schedules are stored inside household setup; they belong conceptually to `kids` (school, activities) and `household`.
9. The Raspberry Pi display cannot reach a loopback-only server (see ADR-0007 conditions).

## Rework intent (next phase)
Re-home code under `core/` and `modules/<m>/submodules/<s>/`, move provider calls behind the server with provenance, add the manifest registry and a card shell, and replace the placeholder tests. Stories first for anything that changes behaviour.
