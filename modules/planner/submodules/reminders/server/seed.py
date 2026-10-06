"""Seed reminders for the sample household: seed/planner/reminders.json. Dates are offsets from today so they never go stale."""
from __future__ import annotations

from datetime import date, timedelta
import json

from chit_server.paths import REPO_ROOT

SEED_FILE = REPO_ROOT / "seed" / "planner" / "reminders.json"
WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}


def seed(store, today=None):
    today = today or date.today()
    if not SEED_FILE.is_file():
        return []
    document = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    loaded = []
    for item in document["reminders"]:
        if store.reminder_exists(item["id"]):
            continue
        on_date = (today + timedelta(days=item["in_days"])).isoformat() if "in_days" in item else None
        store.add_reminder(document["household_id"], item["title"], item.get("member_id"), on_date,
                           [WEEKDAYS[d] for d in item.get("weekdays", [])], item.get("day_part"), reminder_id=item["id"])
        loaded.append(item["id"])
    return loaded
