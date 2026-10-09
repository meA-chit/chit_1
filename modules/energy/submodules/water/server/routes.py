"""Water meter readings (energy/water): total meter and garden meter, entered by hand for now (state `manual`).

Household use is total minus garden. A digital meter can later feed the same readings through a connector; nothing here changes then.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from chit_server.loader import load_file_module
from chit_server.router import HTTPError

shared = Path(__file__).parents[3] / "shared"
water = load_file_module(shared / "water.py")
household = load_file_module(shared / "household.py")

MAX_BATCH = 400
METERS = (("total", "water_total"), ("garden", "water_garden"))


def _view(ctx, household_id, today):
    readings = ctx.store.list_meter_readings(household_id)
    if not readings:
        return {"state": "unconfigured", "reason": "no_readings", "unit": "m3"}
    return {"state": "manual", "unit": "m3", **water.summarize(readings, today)}


def read(ctx, request):
    household_id, _, now = household.latest(ctx)
    if household_id is None:
        return 200, {"state": "unconfigured", "reason": "no_household", "unit": "m3"}
    return 200, _view(ctx, household_id, now.date())


def _number(raw, field, day):
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    if isinstance(raw, str):
        raw = raw.strip().replace(",", ".")
    try:
        return float(raw)
    except (TypeError, ValueError):
        raise HTTPError(400, "%s: the %s reading must be a number like 812.345" % (day, field)) from None


def save(ctx, request):
    household_id, _, now = household.latest(ctx)
    if household_id is None:
        raise HTTPError(404, "Set up a household first")
    body = request.json()
    items = body.get("readings") if isinstance(body, dict) else None
    if not isinstance(items, list) or not items or len(items) > MAX_BATCH or not all(isinstance(i, dict) for i in items):
        raise HTTPError(400, "Send between 1 and %d readings" % MAX_BATCH)
    rows = []
    for item in items:
        day = str(item.get("read_on") or "")
        given = 0
        for field, meter in METERS:
            value = _number(item.get(field), field, day)
            if value is not None:
                rows.append({"meter": meter, "read_on": day, "value": value, "note": item.get("note")})
                given += 1
        if not given:
            raise HTTPError(400, "%s: enter the total reading, the garden reading or both" % (day or "a reading"))
    try:
        ctx.store.save_meter_readings(household_id, rows, today=now.date())
    except ValueError as error:
        raise HTTPError(400, str(error)) from None
    return 200, _view(ctx, household_id, now.date())


def remove(ctx, request):
    household_id, _, now = household.latest(ctx)
    if household_id is None:
        raise HTTPError(404, "Set up a household first")
    day = request.params["day"]
    try:
        date.fromisoformat(day)
    except ValueError:
        raise HTTPError(400, "Not a date") from None
    if not ctx.store.delete_meter_readings_on(household_id, day):
        raise HTTPError(404, "No reading on that day")
    return 200, _view(ctx, household_id, now.date())


def register(router) -> None:
    router.get("/api/energy/water/readings")(read)
    router.post("/api/energy/water/readings")(save)
    router.delete("/api/energy/water/readings/{day}")(remove)
