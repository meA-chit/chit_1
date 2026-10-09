"""Weather for the household's location, fetched server-side from Open-Meteo (no API key).

The browser never calls a weather provider. Needs household latitude/longitude (set in household settings);
without them the state is `unconfigured`, never a guess. Results are cached for 15 minutes; if a refresh
fails the last good reading is returned as `stale` with its original observation time.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import time
from urllib.request import Request, urlopen

API = ("https://api.open-meteo.com/v1/forecast?latitude={lat:.4f}&longitude={lon:.4f}"
       "&current=temperature_2m,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,"
       "precipitation_probability_max&timezone=auto&forecast_days=7")
CACHE_SECONDS = 15 * 60
_cache = {}  # (lat, lon) -> (fetched_monotonic, payload)

# WMO weather codes -> (label, icon key)
CODES = {0: ("Clear", "clear"), 1: ("Mostly clear", "clear"), 2: ("Partly cloudy", "partly"), 3: ("Overcast", "cloud"),
         45: ("Fog", "fog"), 48: ("Fog", "fog"), 51: ("Drizzle", "rain"), 53: ("Drizzle", "rain"), 55: ("Drizzle", "rain"),
         61: ("Light rain", "rain"), 63: ("Rain", "rain"), 65: ("Heavy rain", "rain"), 71: ("Light snow", "snow"),
         73: ("Snow", "snow"), 75: ("Heavy snow", "snow"), 80: ("Showers", "rain"), 81: ("Showers", "rain"),
         82: ("Heavy showers", "rain"), 95: ("Thunderstorm", "storm"), 96: ("Thunderstorm", "storm"), 99: ("Thunderstorm", "storm")}


def fetch(lat, lon):
    request = Request(API.format(lat=lat, lon=lon), headers={"User-Agent": "Chit-Weather/1.0", "Accept": "application/json"})
    with urlopen(request, timeout=8) as response:
        if response.status != 200:
            raise ValueError("weather provider returned %s" % response.status)
        raw = json.loads(response.read(200_000).decode("utf-8"))
    code = int(raw["current"]["weather_code"])
    label, icon = CODES.get(code, ("Unknown", "cloud"))
    daily = raw["daily"]
    days = daily.get("time") or []
    codes = daily.get("weather_code") or []
    week = []
    for i, day in enumerate(days):
        day_label, day_icon = CODES.get(int(codes[i]) if i < len(codes) and codes[i] is not None else -1, ("Unknown", "cloud"))
        week.append({"date": day, "condition": day_label, "icon": day_icon,
                     "high": round(daily["temperature_2m_max"][i]), "low": round(daily["temperature_2m_min"][i]),
                     "rain_pct": daily["precipitation_probability_max"][i]})
    return {
        "temperature": round(raw["current"]["temperature_2m"]),
        "condition": label, "icon": icon,
        "high": round(raw["daily"]["temperature_2m_max"][0]), "low": round(raw["daily"]["temperature_2m_min"][0]),
        "rain_pct": raw["daily"]["precipitation_probability_max"][0],
        "week": week,
        "observed_at": raw["current"]["time"],
        "source": "Open-Meteo",
    }


def now(ctx, request):
    household_id = ctx.store.latest_household_id()
    if household_id is None:
        return 200, {"state": "unconfigured", "reason": "no_household"}
    place = ctx.store.get_household_document(household_id)["household"]
    if place.get("latitude") is None or place.get("longitude") is None:
        return 200, {"state": "unconfigured", "reason": "no_location"}
    key = (place["latitude"], place["longitude"])
    cached = _cache.get(key)
    if cached and time.monotonic() - cached[0] < CACHE_SECONDS:
        return 200, {**cached[1], "state": "available"}
    try:
        payload = fetch(*key)
    except Exception as error:
        ctx.log("weather fetch failed (%s)" % type(error).__name__)
        if cached:
            return 200, {**cached[1], "state": "stale"}
        return 200, {"state": "unavailable", "reason": "provider_error"}
    payload["checked_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _cache[key] = (time.monotonic(), payload)
    return 200, {**payload, "state": "available"}


def register(router) -> None:
    router.get("/api/planner/weather/now")(now)
