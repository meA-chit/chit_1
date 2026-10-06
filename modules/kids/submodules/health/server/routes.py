"""Medication reminders and the given/missed log (kids/health). The strictest data class.

Parents only. Shared screens never get a medicine's name from here; the timeline shows nothing from this module.
"""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from chit_server.loader import load_file_module
from chit_server.router import HTTPError

shared = Path(__file__).parents[3] / "shared"
api = load_file_module(shared / "api.py")
meds = load_file_module(shared / "meds.py")


def build(rows, now):
    """Pure: stored medications (with their log since Monday) -> the payload for the week of `now`."""
    today = now.date()
    monday = today - timedelta(days=today.weekday())
    week = [(monday + timedelta(days=i)) for i in range(7)]
    out = []
    for med in rows:
        left = meds.days_left(med["supply"], med["weekdays"])
        out.append({
            "id": med["id"], "name": med["name"], "dose": med["dose"], "time": med["time"], "weekdays": [api.WEEKDAYS[d] for d in med["weekdays"]],
            "remind_member_id": med["remind_member_id"], "supply": med["supply"], "days_left": left,
            "refill_soon": left is not None and left <= meds.REFILL_WARNING_DAYS,
            "today": {"due": meds.due_on(med["weekdays"], today), "status": med["log"].get(today.isoformat())},
            "week": [{"day": d.isoformat(), "due": meds.due_on(med["weekdays"], d), "status": med["log"].get(d.isoformat())} for d in week],
        })
    return out


def overview(ctx, request):
    household_id, document, now = api.latest(ctx)
    if household_id is None:
        return 200, {"state": "unconfigured", "meds": []}
    member = api.child_id(document, request)
    monday = (now.date() - timedelta(days=now.weekday())).isoformat()
    rows = ctx.store.list_meds(household_id, member, monday) if member else []
    return 200, {"state": "manual", "member_id": member, "date": now.date().isoformat(), "now": now.strftime("%H:%M"),
                 "meds": build(rows, now), "source": "medication entered in Chit"}


def _fields(data):
    weekdays = data.get("weekdays", [])
    if not isinstance(weekdays, list):
        raise HTTPError(400, "weekdays must be a list of 0 (Monday) to 6 (Sunday)")
    return (str(data.get("name", "")), data.get("dose"), data.get("time"), weekdays, data.get("remind_member_id") or None, data.get("supply"))


def add(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    data = api.body(request)
    med_id = api.checked(ctx.store.add_med, household_id, str(data.get("member_id", "")), *_fields(data))
    return 201, {"id": med_id}


def update(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    api.checked(ctx.store.update_med, household_id, request.params["id"], *_fields(api.body(request)))
    return 200, {"id": request.params["id"]}


def remove(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    api.checked(ctx.store.archive_med, household_id, request.params["id"])
    return 200, {"id": request.params["id"], "removed": True}


def log(ctx, request):
    household_id, _, now = api.need_household(ctx)
    data = api.body(request)
    day = api.parse_day(data.get("date"), now, past_days=7)
    api.checked(ctx.store.log_med, household_id, request.params["id"], day, data.get("status"))
    return 200, {"id": request.params["id"], "date": day.isoformat(), "status": data.get("status")}


def register(router) -> None:
    router.get("/api/kids/health/meds")(overview)
    router.post("/api/kids/health/meds")(add)
    router.put("/api/kids/health/meds/{id}")(update)
    router.delete("/api/kids/health/meds/{id}")(remove)
    router.post("/api/kids/health/meds/{id}/log")(log)
