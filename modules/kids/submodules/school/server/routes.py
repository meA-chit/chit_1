"""The school-day plan (kids/school): lessons, recess, meals and care typed in by a parent per weekday.

State is `manual`: nothing is read from a school system. Trips to and from school stay on the family timeline (planner).
"""
from __future__ import annotations

from pathlib import Path

from chit_server.loader import load_file_module
from chit_server.router import HTTPError

api = load_file_module(Path(__file__).parents[3] / "shared" / "api.py")


def _slot(data):
    return data.get("start"), data.get("end"), str(data.get("title", "")), data.get("kind"), data.get("note")


def plan(ctx, request):
    """All weekdays for a child (the editor), or one weekday with ?weekday=0..6 / today."""
    household_id, document, now = api.latest(ctx)
    if household_id is None:
        return 200, {"state": "unconfigured", "slots": []}
    member = api.child_id(document, request)
    weekday = request.query.get("weekday")
    if weekday == "today":
        weekday = str(now.weekday())
    if weekday is not None and (not weekday.isdigit() or int(weekday) > 6):
        raise HTTPError(400, "weekday must be 0 (Monday) to 6 (Sunday) or today")
    slots = ctx.store.list_school_slots(household_id, member, int(weekday) if weekday is not None else None) if member else []
    return 200, {"state": "manual", "member_id": member, "today_weekday": now.weekday(), "now": now.strftime("%H:%M"),
                 "slots": slots, "source": "school day typed in by a parent"}


def add_slot(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    data = api.body(request)
    start, end, title, kind, note = _slot(data)
    slot_id = api.checked(ctx.store.add_school_slot, household_id, str(data.get("member_id", "")), data.get("weekday"), start, end, title, kind, note)
    return 201, {"id": slot_id}


def update_slot(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    api.checked(ctx.store.update_school_slot, household_id, request.params["id"], *_slot(api.body(request)))
    return 200, {"id": request.params["id"]}


def remove_slot(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    api.checked(ctx.store.delete_school_slot, household_id, request.params["id"])
    return 200, {"id": request.params["id"], "removed": True}


def copy_day(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    data = api.body(request)
    targets = data.get("to_weekdays")
    if not isinstance(targets, list):
        raise HTTPError(400, "to_weekdays must be a list")
    copied = api.checked(ctx.store.copy_school_day, household_id, str(data.get("member_id", "")), data.get("from_weekday"), targets)
    return 200, {"copied_to": copied}


def register(router) -> None:
    router.get("/api/kids/school/plan")(plan)
    router.post("/api/kids/school/slots")(add_slot)
    router.put("/api/kids/school/slots/{id}")(update_slot)
    router.delete("/api/kids/school/slots/{id}")(remove_slot)
    router.post("/api/kids/school/copy")(copy_day)
