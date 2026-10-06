"""Solar production (energy/solar), read from the household's SolarEdge connection.

Measured values are `available`. The hourly "expected" curve is a forecast estimate from the weather forecast and
the plant's peak power, returned separately so the client can label it. Without a SolarEdge connection the state is
`unconfigured`.
"""
from __future__ import annotations

from pathlib import Path

from chit_server.loader import load_file_module

shared = Path(__file__).parents[3] / "shared"
solaredge = load_file_module(shared / "solaredge.py")
forecast = load_file_module(shared / "forecast.py")
net = load_file_module(shared / "net.py")
household = load_file_module(shared / "household.py")


def day_view(ctx, request):
    household_id, document, now = household.latest(ctx)
    if household_id is None:
        return 200, {"state": "unconfigured", "reason": "no_household"}
    conn = ctx.store.get_energy_connection(household_id, "solaredge")
    if conn is None:
        return 200, {"state": "unconfigured", "reason": "no_solaredge"}
    site_id, key, config = conn["config"]["site_id"], conn["secret"], conn["config"]
    day = now.date().isoformat()
    try:
        summary, fetched_at, stale = solaredge.overview(site_id, key)
        measured, _, curve_stale = solaredge.hourly_production(site_id, key, day)
        stale = stale or curve_stale
    except net.ProviderError as error:
        ctx.log("solaredge failed (%s)" % error.kind)
        return 200, {"state": "unavailable", "reason": "key_rejected" if error.kind == "auth" else error.kind}

    expected, expected_state = {}, "unconfigured"
    place = document["household"]
    if config.get("peak_kw") and place.get("latitude") is not None and place.get("longitude") is not None:
        try:
            by_hour, _, _ = forecast.expected_kw(place["latitude"], place["longitude"], float(config["peak_kw"]))
            expected, expected_state = {h: kw for (d, h), kw in by_hour.items() if d == day}, "forecast"
        except net.ProviderError as error:
            ctx.log("solar forecast failed (%s)" % error.kind)
            expected_state = "unavailable"
    hours = [{"hour": h, "kwh": measured.get(h) if h <= now.hour else None,
              "expected_kwh": expected.get(h) if h >= now.hour else None} for h in range(24)]
    return 200, {
        "state": "stale" if stale else "available", "source": "SolarEdge", "date": day, "now_hour": now.hour,
        "site_name": config.get("site_name"), "peak_kw": config.get("peak_kw"),
        "expected_state": expected_state, "hours": hours, "checked_at": fetched_at, **summary,
    }


def register(router) -> None:
    router.get("/api/energy/solar/day")(day_view)
