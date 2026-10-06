"""Recurring household chores with streaks (planner/chores).

A chore repeats on chosen weekdays (none = every day) in a day part (morning/day/evening/any time),
never at an exact time. Edited from the household settings screen; ticked off on the dashboard.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from chit_server.loader import load_file_module
from chit_server.router import HTTPError

schedule = load_file_module(Path(__file__).parents[2].parent / "shared" / "dayparts.py")


def _context(ctx):
    household_id = ctx.store.latest_household_id()
    if household_id is None:
        return None, None, None
    document = ctx.store.get_household_document(household_id)
    today = datetime.now(ZoneInfo(document["household"]["timezone"])).date()
    return household_id, document, today


def options(ctx, request):
    return 200, {"day_parts": schedule.DAY_PARTS, "weekdays": list(schedule.WEEKDAYS)}


def _person(people, member_id):
    person = people.get(member_id)
    return None if person is None else {
        "id": person["client_id"], "name": person["name"], "avatar": person.get("avatar"), "color": person.get("color")}


def today_list(ctx, request):
    household_id, document, today = _context(ctx)
    if household_id is None:
        return 200, {"state": "unconfigured", "chores": []}
    people = {m["client_id"]: m for m in document["members"]}
    everything = [{**chore, "assignee": _person(people, chore["assignee_id"]), "weekdays": [schedule.WEEKDAY_NAMES[d] for d in chore["weekdays"]]}
                  for chore in ctx.store.list_chores_today(household_id, today)]
    chores = [c for c in everything if not c["skipped"]]
    skipped = [c for c in everything if c["skipped"]]  # kept so the dashboard can offer undo
    done = sum(1 for chore in chores if chore["done"])
    return 200, {
        "state": "manual", "date": today.isoformat(), "chores": chores, "skipped": skipped, "day_parts": schedule.DAY_PARTS,
        "summary": {"done": done, "total": len(chores), "best_streak": max([c["streak"] for c in chores], default=0)},
        "source": "household chores entered in Chit",
    }


def list_all(ctx, request):
    """Every active chore with its schedule, for the settings screen."""
    household_id, _, _ = _context(ctx)
    if household_id is None:
        return 200, {"state": "unconfigured", "chores": []}
    chores = [{**c, "weekdays": [schedule.WEEKDAY_NAMES[d] for d in c["weekdays"]]} for c in ctx.store.list_chore_series(household_id)]
    return 200, {"state": "manual", "chores": chores}


def toggle(ctx, request):
    household_id, _, today = _context(ctx)
    if household_id is None:
        raise HTTPError(404, "No household")
    body = request.json()
    if not isinstance(body, dict) or not isinstance(body.get("done"), bool):
        raise HTTPError(400, "done must be true or false")
    try:
        ctx.store.set_chore_done(household_id, request.params["id"], today, body["done"], body.get("by"))
    except LookupError:
        raise HTTPError(404, "Chore not found") from None
    return 200, {"id": request.params["id"], "done": body["done"], "date": today.isoformat()}


def skip(ctx, request):
    """Skip (or restore) one occurrence, today only: operations management, not deleting the chore."""
    household_id, _, today = _context(ctx)
    if household_id is None:
        raise HTTPError(404, "No household")
    body = request.json()
    if not isinstance(body, dict) or not isinstance(body.get("skipped"), bool):
        raise HTTPError(400, "skipped must be true or false")
    try:
        ctx.store.set_skipped(household_id, "chore", request.params["id"], today, body["skipped"])
    except LookupError:
        raise HTTPError(404, "Chore not found") from None
    return 200, {"id": request.params["id"], "skipped": body["skipped"], "date": today.isoformat()}


def _fields(body):
    if not isinstance(body, dict):
        raise HTTPError(400, "Request body must be a JSON object")
    try:
        return (str(body.get("title", "")), body.get("assignee_id") or None,
                schedule.parse_weekdays(body.get("weekdays", [])), schedule.parse_part(body.get("day_part")))
    except ValueError as error:
        raise HTTPError(400, "Invalid chore: %s" % error) from None


def create(ctx, request):
    household_id, _, _ = _context(ctx)
    if household_id is None:
        raise HTTPError(404, "No household")
    title, assignee, weekdays, part = _fields(request.json())
    try:
        series_id = ctx.store.add_chore_series(household_id, title, assignee, weekdays, day_part=part)
    except ValueError as error:
        raise HTTPError(400, "Invalid chore: %s" % error) from None
    return 201, {"id": series_id}


def update(ctx, request):
    household_id, _, _ = _context(ctx)
    if household_id is None:
        raise HTTPError(404, "No household")
    title, assignee, weekdays, part = _fields(request.json())
    try:
        ctx.store.update_chore_series(household_id, request.params["id"], title, assignee, weekdays, part)
    except LookupError:
        raise HTTPError(404, "Chore not found") from None
    except ValueError as error:
        raise HTTPError(400, "Invalid chore: %s" % error) from None
    return 200, {"id": request.params["id"]}


def archive(ctx, request):
    household_id, _, _ = _context(ctx)
    if household_id is None:
        raise HTTPError(404, "No household")
    try:
        ctx.store.archive_chore_series(household_id, request.params["id"])
    except LookupError:
        raise HTTPError(404, "Chore not found") from None
    return 200, {"id": request.params["id"], "archived": True}


def register(router) -> None:
    router.get("/api/planner/chores/options")(options)
    router.get("/api/planner/chores/today")(today_list)
    router.get("/api/planner/chores")(list_all)
    router.post("/api/planner/chores")(create)
    router.put("/api/planner/chores/{id}")(update)
    router.delete("/api/planner/chores/{id}")(archive)
    router.post("/api/planner/chores/{id}/toggle")(toggle)
    router.post("/api/planner/chores/{id}/skip")(skip)
