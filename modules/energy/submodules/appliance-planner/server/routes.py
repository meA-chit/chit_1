"""Best windows for heavy workloads (energy/appliance-planner): the two cheapest, most solar-friendly runs of hours.

Read-only advice. Chit never switches a device. Needs Tibber prices; when a SolarEdge connection and the household
location exist, expected solar output (an estimate) lowers the score of sunny hours. See shared/windows.py.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from chit_server.loader import load_file_module
from chit_server.router import HTTPError

shared = Path(__file__).parents[3] / "shared"
tibber = load_file_module(shared / "tibber.py")
forecast = load_file_module(shared / "forecast.py")
windows = load_file_module(shared / "windows.py")
net = load_file_module(shared / "net.py")
household = load_file_module(shared / "household.py")


def _length(request):
    raw = request.query.get("hours", "2")
    if raw not in ("1", "2", "3", "4"):
        raise HTTPError(400, "hours must be 1 to 4")
    return int(raw)


def build(prices, solar, now, length):
    """Pure: Tibber hourly map, optional {(date, hour): kW} solar estimate -> windows payload."""
    slots = [{"start": datetime.strptime("%s %02d" % key, "%Y-%m-%d %H"), "price": price,
              "solar_kw": None if solar is None else solar.get(key)} for key, price in prices["by_hour"].items()]
    found = windows.best_windows(slots, now.replace(tzinfo=None), length=length, count=2)
    out = []
    for w in found["windows"]:
        saving = -w["vs_average"]
        out.append({
            "start": w["start"].isoformat(timespec="minutes"), "end": w["end"].isoformat(timespec="minutes"),
            "day": "today" if w["start"].date() == now.date() else "tomorrow",
            "average_price": round(w["average_price"], 4), "solar_kw": w["solar_kw"],
            "saving_vs_average": round(saving, 3), "worth_moving": saving >= windows.FLAT_BAND or bool(w["solar_kw"]),
        })
    return {"windows": out, "average_price": None if found["average_price"] is None else round(found["average_price"], 4)}


def best(ctx, request):
    length = _length(request)
    household_id, document, now = household.latest(ctx)
    if household_id is None:
        return 200, {"state": "unconfigured", "reason": "no_household"}
    conn = ctx.store.get_energy_connection(household_id, "tibber")
    if conn is None:
        return 200, {"state": "unconfigured", "reason": "no_tibber_token"}
    try:
        prices, fetched_at, stale = tibber.prices(conn["secret"], conn["config"].get("home_id"))
    except net.ProviderError as error:
        ctx.log("tibber prices failed (%s)" % error.kind)
        return 200, {"state": "unavailable", "reason": "token_rejected" if error.kind == "auth" else error.kind}

    solar, basis = None, "price"
    pv = ctx.store.get_energy_connection(household_id, "solaredge")
    place = document["household"]
    if pv and pv["config"].get("peak_kw") and place.get("latitude") is not None and place.get("longitude") is not None:
        try:
            solar, _, _ = forecast.expected_kw(place["latitude"], place["longitude"], float(pv["config"]["peak_kw"]))
            basis = "price_and_solar"
        except net.ProviderError as error:
            ctx.log("solar forecast failed (%s)" % error.kind)
    result = build(prices, solar, now, length)
    tomorrow = any(key[0] > now.date().isoformat() for key in prices["by_hour"])
    return 200, {
        "state": "stale" if stale else "available", "source": "Tibber prices" + (" and a solar estimate" if basis == "price_and_solar" else ""),
        "basis": basis, "hours": length, "currency": prices["currency"], "tomorrow_included": tomorrow,
        "checked_at": fetched_at, **result,
    }


def register(router) -> None:
    router.get("/api/energy/suggestions/windows")(best)
