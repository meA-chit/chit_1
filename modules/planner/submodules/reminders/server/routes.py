"""Planned reminders for a person or the whole family (planner/reminders).

One-off (a date) or recurring (weekdays; none = every day), in a day part (morning/day/evening) or any time.
They appear on the family timeline and are edited from the household settings screen.
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
        return None, None
    document = ctx.store.get_household_document(household_id)
    return household_id, datetime.now(ZoneInfo(document["household"]["timezone"])).date()


def _out(reminder):
    return {**reminder, "weekdays": [schedule.WEEKDAY_NAMES[d] for d in reminder["weekdays"]]}


def list_all(ctx, request):
    household_id, _ = _context(ctx)
    if household_id is None:
        return 200, {"state": "unconfigured", "reminders": []}
    return 200, {"state": "manual", "reminders": [_out(r) for r in ctx.store.list_reminders(household_id)], "day_parts": schedule.DAY_PARTS}


def today(ctx, request):
    household_id, day = _context(ctx)
    if household_id is None:
        return 200, {"state": "unconfigured", "reminders": []}
    states = ctx.store.reminder_states_for_day(household_id, day)        # the dashboard's own done marks (a child's phone has its own)
    everything = [{**_out(r), "done": states.get(r["id"]) == "done"} for r in ctx.store.list_reminders_for_day(household_id, day)]
    return 200, {
        "state": "manual", "date": day.isoformat(), "day_parts": schedule.DAY_PARTS,
        "reminders": [r for r in everything if not r["skipped"]],
        "skipped": [r for r in everything if r["skipped"]],       # kept so the dashboard can offer undo
        "upcoming": [_out(r) for r in ctx.store.list_upcoming_reminders(household_id, day, 7)],
    }


def skip(ctx, request):
    """Skip (or restore) a reminder for today only. Removing it for good is DELETE."""
    household_id, _ = _context(ctx)
    if household_id is None:
        raise HTTPError(404, "No household")
    body = request.json()
    if not isinstance(body, dict) or not isinstance(body.get("skipped"), bool):
        raise HTTPError(400, "skipped must be true or false")
    _, day = _context(ctx)
    try:
        ctx.store.set_skipped(household_id, "reminder", request.params["id"], day, body["skipped"])
    except LookupError:
        raise HTTPError(404, "Reminder not found") from None
    return 200, {"id": request.params["id"], "skipped": body["skipped"], "date": day.isoformat()}


def mark_done(ctx, request):
    """Mark a reminder done for today on the dashboard (or undo). A reminder is a nudge: this does not remove it, and a child's phone is separate."""
    household_id, day = _context(ctx)
    if household_id is None:
        raise HTTPError(404, "No household")
    body = request.json()
    if not isinstance(body, dict) or not isinstance(body.get("done"), bool):
        raise HTTPError(400, "done must be true or false")
    try:
        ctx.store.set_reminder_state(household_id, request.params["id"], day, "done" if body["done"] else None)
    except LookupError:
        raise HTTPError(404, "Reminder not found") from None
    return 200, {"id": request.params["id"], "done": body["done"], "date": day.isoformat()}


def _fields(body):
    if not isinstance(body, dict):
        raise HTTPError(400, "Request body must be a JSON object")
    try:
        return (str(body.get("title", "")), body.get("member_id") or None, body.get("on_date") or None,
                schedule.parse_weekdays(body.get("weekdays", [])), schedule.parse_part(body.get("day_part")))
    except ValueError as error:
        raise HTTPError(400, "Invalid reminder: %s" % error) from None


def create(ctx, request):
    household_id, _ = _context(ctx)
    if household_id is None:
        raise HTTPError(404, "No household")
    title, member, on_date, weekdays, part = _fields(request.json())
    try:
        return 201, {"id": ctx.store.add_reminder(household_id, title, member, on_date, weekdays, part)}
    except ValueError as error:
        raise HTTPError(400, "Invalid reminder: %s" % error) from None


def update(ctx, request):
    household_id, _ = _context(ctx)
    if household_id is None:
        raise HTTPError(404, "No household")
    title, member, on_date, weekdays, part = _fields(request.json())
    try:
        ctx.store.update_reminder(household_id, request.params["id"], title, member, on_date, weekdays, part)
    except LookupError:
        raise HTTPError(404, "Reminder not found") from None
    except ValueError as error:
        raise HTTPError(400, "Invalid reminder: %s" % error) from None
    return 200, {"id": request.params["id"]}


def archive(ctx, request):
    household_id, _ = _context(ctx)
    if household_id is None:
        raise HTTPError(404, "No household")
    try:
        ctx.store.archive_reminder(household_id, request.params["id"])
    except LookupError:
        raise HTTPError(404, "Reminder not found") from None
    return 200, {"id": request.params["id"], "archived": True}


def register(router) -> None:
    router.get("/api/planner/reminders")(list_all)
    router.get("/api/planner/reminders/today")(today)
    router.post("/api/planner/reminders")(create)
    router.put("/api/planner/reminders/{id}")(update)
    router.delete("/api/planner/reminders/{id}")(archive)
    router.post("/api/planner/reminders/{id}/skip")(skip)
    router.post("/api/planner/reminders/{id}/done")(mark_done)
