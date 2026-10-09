# Submodule: weather (module `planner`)

> Code: `modules/planner/submodules/weather/`

**Purpose.** Today and tomorrow in the ribbon (`weather-now`, slot `topbar`), with a dropdown that opens over the page like the "Viewing as" menu and lists today plus the next five days. The separate `weather-week` card was removed.

**Behaviour.** `GET /api/planner/weather/now`: the hub fetches Open-Meteo for the household's latitude/longitude (no API key), caches 15 minutes, and returns temperature, condition, high/low, rain chance, a `week` list (date, condition, icon, high/low, rain chance for seven days), observation time and source. No coordinates → `unconfigured` (link to household settings). Provider down → last reading as `stale`, or `unavailable` if none. The browser never calls a weather provider (the prototype did).

**Not built.** Hourly forecast, alerts, address search (coordinates are entered by hand), forecast feeding energy planning (`energy/forecast`).
