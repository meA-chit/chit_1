"""What the child's phone shows of their day beyond lessons: weekly activities with leave-by, calendar events, and the bag checklist. Pure functions."""
from __future__ import annotations

from datetime import date, timedelta

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
EVENT_DAYS = 14
HIDDEN_CATEGORIES = ("work", "waste_collection")     # a child's phone never shows a parent's work or the bin calendar


def _minutes(value):
    if not value:
        return None
    hours, minutes = str(value)[:5].split(":")
    return int(hours) * 60 + int(minutes)


def _hhmm(total):
    total = max(0, min(total, 24 * 60 - 1))
    return "%02d:%02d" % (total // 60, total % 60)


def weekly_activities(activities, names):
    """The child's regular activities (household setup). `leave_by` only when a commute was entered: nothing is inferred.

    `names` maps adult ids to first names, for "Dad takes you"."""
    out = []
    for activity in activities or []:
        start, end = _minutes(activity.get("start_time")), _minutes(activity.get("end_time"))
        days = [WEEKDAYS.index(d) for d in activity.get("days") or [] if d in WEEKDAYS]
        if start is None or not days:
            continue
        mode, travel = activity.get("commute_mode"), activity.get("travel_minutes")
        commute = bool(mode and travel)
        escort = "parent" if activity.get("escort") == "parent" else "independent"
        out.append({
            "name": activity["name"], "place": activity.get("location"), "start": _hhmm(start), "end": _hhmm(end) if end is not None else None,
            "weekdays": days, "mode": mode if commute else None, "travel_minutes": travel if commute else None,
            "leave_by": _hhmm(start - travel) if commute else None, "escort": escort,
            "escort_name": names.get(activity.get("escort_adult_client_id")) if escort == "parent" else None,
        })
    out.sort(key=lambda a: (a["weekdays"][0], a["start"]))
    return out


def child_events(agenda, member_id, today):
    """Calendar events from the child's own calendars (school, sport, family), the next two weeks. Household-wide calendars are not the child's."""
    last = today + timedelta(days=EVENT_DAYS - 1)
    out = []
    for event in agenda.get("events", []):
        if member_id not in (event.get("member_ids") or []) or event.get("category") in HIDDEN_CATEGORIES:
            continue
        day = date.fromisoformat(event["start"][:10])
        if not today <= day <= last:
            continue
        out.append({"title": event["title"], "date": day.isoformat(), "start": None if event.get("all_day") else event["start"][11:16],
                    "end": None if event.get("all_day") else event["end"][11:16], "all_day": bool(event.get("all_day")),
                    "source": event.get("source"), "category": event.get("category")})
    out.sort(key=lambda e: (e["date"], e["start"] or "", e["title"]))
    return out[:40]


def school_day(slots, day):
    """The lesson titles of `day` in the order they start, or [] when the child has no lessons that weekday."""
    lessons = sorted((s for s in slots if s["weekday"] == day.weekday() and s["kind"] == "lesson"), key=lambda s: s["start"])
    return [s["title"] for s in lessons]


def next_school_day(slots, after):
    for offset in range(1, 8):
        day = after + timedelta(days=offset)
        if school_day(slots, day):
            return day
    return None


def derive_bag(titles, items, reminders, tasks, activity_names, day, ticked):
    """The checklist for one school day, from lessons (their subject items), reminders, homework due that day and after-school activities.

    Items are only ever the ones someone wrote down. An item needed by two subjects appears once ("for Maths, German"), and is ticked once."""
    entries, order = {}, []

    def add(label, source, reason, rid=None, done=False):
        key = label.strip().lower()
        if key not in entries:
            entries[key] = {"key": key, "label": label.strip(), "source": source, "for": [], "ticked": key in ticked or done}
            if rid:
                entries[key]["rid"] = rid           # a reminder: ticking it marks the reminder itself done, so both layouts agree
            order.append(key)
        if reason and reason not in entries[key]["for"]:
            entries[key]["for"].append(reason)

    def by_subject(names, source):
        for name in names:
            for item in items:
                if item["subject"].lower() == name.lower():
                    add(item["label"], source, name)

    seen = []
    for title in titles:
        if title not in seen:
            seen.append(title)
    by_subject(seen, "subject")
    for reminder in reminders:
        if reminder.get("state") == "na":           # the child said it is not relevant: it is not on the list
            continue
        add(reminder["title"], "reminder", None, reminder.get("id"), reminder.get("state") == "done")
    for task in tasks:
        if task["kind"] == "homework" and not task["done"] and task["due_on"] == day.isoformat():
            add("%s: %s" % (task["subject"], task["title"]) if task["subject"] else task["title"], "homework", task["subject"])
    by_subject(activity_names, "activity")
    return [entries[key] for key in order]
