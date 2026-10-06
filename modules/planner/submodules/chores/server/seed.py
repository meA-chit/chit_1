"""Seed chores for the sample household: seed/planner/chores.json (ADR-0010)."""
from __future__ import annotations

from datetime import date, timedelta
import json

from chit_server.paths import REPO_ROOT

SEED_FILE = REPO_ROOT / "seed" / "planner" / "chores.json"
WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}


def seed(store, today=None):
    """Idempotent. `seed_streak` = completed on the last N expected days up to yesterday, so demo streaks never go stale."""
    today = today or date.today()
    if not SEED_FILE.is_file():
        return []
    document = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    household_id = document["household_id"]
    loaded = []
    for chore in document["chores"]:
        if store.chore_series_exists(chore["id"]):
            continue
        weekdays = [WEEKDAYS[d] for d in chore.get("weekdays", [])]
        store.add_chore_series(household_id, chore["title"], chore.get("assignee_id"), weekdays,
                               chore.get("due_time"), series_id=chore["id"], day_part=chore.get("day_part"))
        day, remaining = today - timedelta(days=1), int(chore.get("seed_streak", 0))
        while remaining > 0:
            if not weekdays or day.weekday() in weekdays:
                store.set_chore_done(household_id, chore["id"], day, True)
                remaining -= 1
            day -= timedelta(days=1)
        if chore.get("done_today"):
            store.set_chore_done(household_id, chore["id"], today, True)
        loaded.append(chore["id"])
    return loaded
