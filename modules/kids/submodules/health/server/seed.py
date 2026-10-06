"""Seed medication reminders from seed/kids/health.json (ADR-0010). Sample names only; real medication never belongs in seed data."""
from __future__ import annotations

from datetime import date, timedelta
import json

from chit_server.paths import REPO_ROOT

SEED_FILE = REPO_ROOT / "seed" / "kids" / "health.json"
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def seed(store, today=None):
    today = today or date.today()
    if not SEED_FILE.is_file():
        return []
    document = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    household_id = document["household_id"]
    if any(store.list_meds(household_id, m["member_id"], "0000-01-01") for m in document["meds"][:1]):
        return []
    for med in document["meds"]:
        med_id = store.add_med(household_id, med["member_id"], med["name"], med.get("dose"), med["time"],
                               [WEEKDAYS.index(d) for d in med["weekdays"]], med.get("remind_member_id"), med.get("supply"))
        for ago in med.get("given_days_ago", []):
            store.log_med(household_id, med_id, today - timedelta(days=ago), "given")
    return [m["name"] for m in document["meds"]]
