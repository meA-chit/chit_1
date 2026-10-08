"""Family timeline for a day (today by default, up to two weeks ahead), built from the routines entered in household setup.

Data state is `manual`: work hours, school/care times and activities were typed in by the household.
Nothing is inferred: a child's block has no start when no drop-off time was entered, and weekdays without
a work location produce no work block. Calendar feed events are merged by the client (see web/).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from chit_server.icons import icon_for
from chit_server.loader import load_file_module

from chit_server.router import HTTPError

schedule = load_file_module(Path(__file__).parents[2].parent / "shared" / "dayparts.py")

DEFAULT_TRAVEL_MINUTES = 15
MODE_VERB = {"walk": "Walk", "cycle": "Cycle", "car": "Drive"}


def _minutes(value):
    if not value:
        return None
    hours, minutes = str(value)[:5].split(":")
    return int(hours) * 60 + int(minutes)


def _hhmm(total):
    total = max(0, min(total, 24 * 60 - 1))
    return "%02d:%02d" % (total // 60, total % 60)


def build_lanes(document, weekday):
    """Pure function: household document + weekday name -> lanes of routine blocks."""
    members = document["members"]
    lanes = {m["client_id"]: {
        "member_id": m["client_id"], "name": m["name"], "role": m["role"],
        "avatar": m.get("avatar"), "color": m.get("color"), "blocks": [],
    } for m in members}

    def add(member_id, start, end, title, kind, row, start_unknown=False, icon=None):
        if member_id in lanes and (end is not None):
            block = {
                "id": "%s-%d" % (member_id, len(lanes[member_id]["blocks"])),
                "title": title, "kind": kind, "row": row, "source": "routine",
                "start": None if start_unknown else _hhmm(start), "end": _hhmm(end),
            }
            if icon:
                block["icon"] = icon          # e.g. the football for "Football training"
            lanes[member_id]["blocks"].append(block)

    for member in members:
        profile = member["profile"]
        if member["role"] == "adult":
            location = (profile.get("work_days") or {}).get(weekday)
            start, end = _minutes(profile.get("work_start")), _minutes(profile.get("work_end"))
            if location in ("office", "home") and start is not None and end is not None and end > start:
                commute = profile.get("commute_minutes") or 0
                if location == "office" and commute:
                    add(member["client_id"], start - commute, start, "Commute", "commute", 0)
                    add(member["client_id"], end, end + commute, "Commute", "commute", 0)
                add(member["client_id"], start, end, "Work · " + location, "work", 0)
            continue

        # child
        child = member["name"]
        pickup, dropoff = _minutes(profile.get("pickup_time")), _minutes(profile.get("dropoff_time"))
        travel = profile.get("travel_minutes") or DEFAULT_TRAVEL_MINUTES
        mode = profile.get("commute_mode")
        if weekday in (profile.get("care_days") or []) and pickup is not None:
            label = profile.get("school_or_care_name") or "School or care"
            add(member["client_id"], dropoff or 0, pickup, label, "school", 0, start_unknown=dropoff is None)
            if mode in ("walk", "cycle"):
                # the child travels alone: the trip is on the child's own lane, no adult is involved
                verb = MODE_VERB[mode]
                if dropoff is not None:
                    add(member["client_id"], dropoff - travel, dropoff, "%s to school" % verb, "commute", 1)
                add(member["client_id"], pickup, pickup + travel, "%s home" % verb, "commute", 1)
            else:
                # by car (or not set): the first listed adult is the default for each trip (document order = priority)
                pickup_adults = profile.get("pickup_adult_client_ids") or []
                if pickup_adults:
                    add(pickup_adults[0], pickup, pickup + travel, "Pick up " + child, "pickup", 1)
                dropoff_adults = profile.get("dropoff_adult_client_ids") or []
                if dropoff_adults and dropoff is not None:
                    add(dropoff_adults[0], dropoff - travel, dropoff, "Drop off " + child, "dropoff", 1)
        for activity in profile.get("activities") or []:
            a_start, a_end = _minutes(activity.get("start_time")), _minutes(activity.get("end_time"))
            if weekday not in (activity.get("days") or []) or a_start is None or a_end is None or a_end <= a_start:
                continue
            add(member["client_id"], a_start, a_end, activity["name"], "activity", 1, icon=icon_for(activity["name"], "sport_activity"))
            a_mode = activity.get("commute_mode")
            a_travel = activity.get("travel_minutes")
            if a_mode is None or not a_travel:
                continue  # no commute entered: nothing is inferred
            escort = activity.get("escort_adult_client_id") if activity.get("escort") == "parent" else None
            if escort:
                go = "Take %s to %s" % (child, activity["name"]) if a_mode == "car" else "%s %s to %s" % (MODE_VERB[a_mode], child, activity["name"])
                back = "Pick up " + child if a_mode == "car" else "%s %s home" % (MODE_VERB[a_mode], child)
                add(escort, a_start - a_travel, a_start, go, "dropoff", 1)
                add(escort, a_end, a_end + a_travel, back, "pickup", 1)
            else:
                verb = MODE_VERB[a_mode]
                add(member["client_id"], a_start - a_travel, a_start, "%s to %s" % (verb, activity["name"]), "commute", 2)
                add(member["client_id"], a_end, a_end + a_travel, "%s home" % verb, "commute", 2)
    return list(lanes.values())


def reminder_items(reminders):
    """Reminders for the day, for the client to place in the zone bands (not on a person's clock row)."""
    return [{"id": r["id"], "title": r["title"], "member_id": r["member_id"], "day_part": r["day_part"]}
            for r in reminders if not r.get("skipped")]


MAX_DAYS_AHEAD = 14


def _target_date(request, today):
    raw = request.query.get("date")
    if not raw:
        return today
    try:
        day = date.fromisoformat(raw)
    except ValueError:
        raise HTTPError(400, "date must look like 2026-10-07") from None
    if not today <= day <= today + timedelta(days=MAX_DAYS_AHEAD):
        raise HTTPError(400, "date must be today or up to %d days ahead" % MAX_DAYS_AHEAD)
    return day


def day_view(ctx, request):
    household_id = ctx.store.latest_household_id()
    if household_id is None:
        return 200, {"state": "unconfigured", "lanes": []}
    document = ctx.store.get_household_document(household_id)
    zone = ZoneInfo(document["household"]["timezone"])
    now = datetime.now(zone)
    day = _target_date(request, now.date())
    weekday = day.strftime("%A").lower()
    lanes = build_lanes(document, weekday)
    reminders = reminder_items(ctx.store.list_reminders_for_day(household_id, day))
    has_any = any(lane["blocks"] for lane in lanes) or bool(reminders)
    return 200, {
        "state": "manual",
        "household": document["household"]["name"],
        "date": day.isoformat(), "weekday": weekday, "timezone": document["household"]["timezone"],
        "is_today": day == now.date(), "today": now.date().isoformat(), "now": now.strftime("%H:%M"),
        "max_days_ahead": MAX_DAYS_AHEAD,
        "lanes": lanes,
        "reminders": reminders,
        "zones": schedule.ZONES,
        "empty_reason": None if has_any else "no_routines",
        "source": "household routines and reminders entered in Chit",
    }


def register(router) -> None:
    router.get("/api/planner/timeline/day")(day_view)
    router.get("/api/planner/timeline/today")(day_view)  # same view; `date` defaults to today
