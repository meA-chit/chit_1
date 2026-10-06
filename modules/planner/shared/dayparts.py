"""Day parts: the household's generic blocks of the day, used by chores, reminders and the timeline.

Morning 06-10, Day 10-16, Evening 16-20; the rest (20-22) is Relax. People choose a part, never an exact time.
The server is the single source: the API returns these lists so the web client never duplicates the hours.
"""
from __future__ import annotations

DAY_PARTS = [
    {"id": "morning", "label": "Morning", "start": "06:00", "end": "10:00"},
    {"id": "day", "label": "Day", "start": "10:00", "end": "16:00"},
    {"id": "evening", "label": "Evening", "start": "16:00", "end": "20:00"},
]
RELAX = {"id": "relax", "label": "Relax", "start": "20:00", "end": "22:00"}
ZONES = DAY_PARTS + [RELAX]  # what the timeline draws; only DAY_PARTS can be chosen for a chore or reminder
PART_IDS = {part["id"] for part in DAY_PARTS}
PART_ORDER = {part["id"]: index for index, part in enumerate(DAY_PARTS)}


def part_window(part_id):
    for part in DAY_PARTS:
        if part["id"] == part_id:
            return part["start"], part["end"]
    return None


WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
WEEKDAY_NAMES = {number: name for name, number in WEEKDAYS.items()}


def parse_weekdays(names):
    """['tuesday', 'friday'] -> [1, 4]. Empty list = every day. Unknown names raise ValueError."""
    if not isinstance(names, list):
        raise ValueError("weekdays must be a list of day names")
    try:
        return sorted({WEEKDAYS[str(name).lower()] for name in names})
    except KeyError as error:
        raise ValueError("unknown weekday %s" % error) from None


def parse_part(value):
    if value in (None, ""):
        return None
    if value not in PART_IDS:
        raise ValueError("time of day must be morning, day or evening")
    return value
