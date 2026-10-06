# Home prototype (archived)

Static prototype of the first home dashboard, kept for visual reference only. It is **not served** by the current server and is not a requirement (see `AGENTS.md`).

Its logic moved to the modular structure:
- calendar agenda → `modules/planner/submodules/calendar` (server reader + web card)
- weather (`js/weather.js`) → `modules/planner/submodules/weather` (to be rebuilt server-side with provenance)
- tariff (`js/tibber.js`) → `modules/energy/submodules/pricing` (to be rebuilt server-side; the browser must not hold the token)
- ribbon/navigation → `core/web` shell
