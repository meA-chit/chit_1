"""Prices and consumption for one day (energy/pricing), from the household's Tibber connection.

Needs the Tibber token from the household energy settings; without it the state is `unconfigured` and nothing is
invented. Consumption needs a Tibber Pulse or smart-meter connection: when Tibber has none, prices are still shown
and consumption is reported as `unavailable` rather than as zeros.
"""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from chit_server.loader import load_file_module
from chit_server.router import HTTPError

shared = Path(__file__).parents[3] / "shared"
tibber = load_file_module(shared / "tibber.py")
net = load_file_module(shared / "net.py")
household = load_file_module(shared / "household.py")


def connection(ctx):
    """-> (household_id, document, now, tibber connection or None)"""
    household_id, document, now = household.latest(ctx)
    if household_id is None:
        return None, None, None, None
    return household_id, document, now, ctx.store.get_energy_connection(household_id, "tibber")


def build_day(prices, consumption, day: str, now_hour: "int | None", consumption_reason: str = "no_meter"):
    """Pure: Tibber maps -> the day payload. `consumption` is {(date, hour): kWh} or None."""
    hours = []
    for hour in range(24):
        price = prices["by_hour"].get((day, hour))
        used = consumption.get((day, hour)) if consumption else None
        hours.append({"hour": hour, "price": None if price is None else round(price, 4),
                      "level": prices["levels"].get((day, hour)), "consumption": None if used is None else round(used, 3)})
    priced = [h for h in hours if h["price"] is not None]
    average = sum(h["price"] for h in priced) / len(priced) if priced else None
    reported = [h for h in hours if h["consumption"] is not None]
    paid = None
    weighted = [h for h in reported if h["price"] is not None and h["consumption"] > 0]
    if weighted and average:
        paid = sum(h["price"] * h["consumption"] for h in weighted) / sum(h["consumption"] for h in weighted)
    current = next((h for h in hours if h["hour"] == now_hour), None) if now_hour is not None else None
    cheapest = min(priced, key=lambda h: h["price"]) if priced else None
    priciest = max(priced, key=lambda h: h["price"]) if priced else None
    return {
        "hours": hours,
        "average_price": None if average is None else round(average, 4),
        "cheapest_hour": cheapest["hour"] if cheapest else None, "priciest_hour": priciest["hour"] if priciest else None,
        "current": None if not current or current["price"] is None else {
            "hour": current["hour"], "price": current["price"],
            "vs_average": round((current["price"] - average) / average, 3) if average else None,
            "consumption": current["consumption"]},
        "consumption": ({"state": "available", "total_kwh": round(sum(h["consumption"] for h in reported), 2),
                         "hours_reported": len(reported), "paid_average_price": None if paid is None else round(paid, 4)}
                        if reported else {"state": "unavailable", "reason": consumption_reason}),
    }


def build_totals(months, today: str, currency):
    """Pure: Tibber monthly map -> month-to-date and year-to-date use and cost. Months Tibber has no figure for are skipped, not zeroed."""
    if not months:
        return {"state": "unavailable", "reason": "no_meter"}
    year, month = today[:4], today[:7]

    def sum_of(keys):
        rows = [months[k] for k in keys if months[k]["cost"] is not None]
        if not rows:
            return None
        return {"cost": round(sum(r["cost"] for r in rows), 2), "kwh": round(sum(r["kwh"] or 0 for r in rows), 1)}
    year_keys = sorted(k for k in months if k.startswith(year))
    month_total, year_total = sum_of([month] if month in months else []), sum_of(year_keys)
    if year_total is None:
        return {"state": "unavailable", "reason": "no_cost"}
    covered = [k for k in year_keys if months[k]["cost"] is not None]
    return {"state": "available", "currency": currency, "month": month_total, "year": year_total,
            "year_from": covered[0] if covered and covered[0] != year + "-01" else None}


def day_view(ctx, request):
    household_id, document, now, conn = connection(ctx)
    if household_id is None:
        return 200, {"state": "unconfigured", "reason": "no_household"}
    if conn is None:
        return 200, {"state": "unconfigured", "reason": "no_tibber_token"}
    which = request.query.get("date", "today")
    if which not in ("today", "tomorrow"):
        raise HTTPError(400, "date must be today or tomorrow")
    day = (now.date() + timedelta(days=1 if which == "tomorrow" else 0)).isoformat()
    token, home_id = conn["secret"], conn["config"].get("home_id")
    try:
        prices, fetched_at, stale = tibber.prices(token, home_id)
    except net.ProviderError as error:
        ctx.log("tibber prices failed (%s)" % error.kind)
        return 200, {"state": "unavailable", "reason": "token_rejected" if error.kind == "auth" else error.kind}
    consumption, reason = None, "no_meter" if which == "today" else "future_day"
    if which == "today":
        try:
            consumption, _, consumption_stale = tibber.consumption(token, home_id)
            stale = stale or consumption_stale
        except net.ProviderError as error:
            ctx.log("tibber consumption failed (%s)" % error.kind)
            reason = "provider_error"
    payload = build_day(prices, consumption, day, now.hour if which == "today" else None, reason)
    totals = {"state": "unavailable", "reason": "future_day"}
    if which == "today":
        try:
            months, _, _ = tibber.monthly(token, home_id)
            totals = build_totals(months, now.date().isoformat(), prices["currency"])
        except net.ProviderError as error:
            ctx.log("tibber monthly failed (%s)" % error.kind)
            totals = {"state": "unavailable", "reason": "provider_error"}
    tomorrow = (now.date() + timedelta(days=1)).isoformat()
    return 200, {
        "totals": totals,
        "state": "stale" if stale else "available", "source": "Tibber", "currency": prices["currency"],
        "date": day, "which": which, "now_hour": now.hour if which == "today" else None, "timezone": document["household"]["timezone"],
        "tomorrow_available": any(key[0] == tomorrow for key in prices["by_hour"]),
        "checked_at": fetched_at, **payload,
    }


def register(router) -> None:
    router.get("/api/energy/pricing/day")(day_view)
