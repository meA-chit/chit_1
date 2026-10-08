"""Seed a school-day plan from seed/kids/school.json (ADR-0010): Monday is typed in, then copied to the other school days.

Subjects exist only because a lesson is in the plan, so the subject types (core, minor, elective) are set here, after the lessons."""
from __future__ import annotations

import json

from chit_server.paths import REPO_ROOT

SEED_FILE = REPO_ROOT / "seed" / "kids" / "school.json"
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def seed(store, today=None):
    if not SEED_FILE.is_file():
        return []
    document = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    household_id, member = document["household_id"], document["member_id"]
    if store.list_school_slots(household_id, member):
        return []
    for slot in document["monday"]:
        store.add_school_slot(household_id, member, 0, slot["start"], slot["end"], slot["title"], slot["kind"], slot.get("note"))
    store.copy_school_day(household_id, member, 0, [WEEKDAYS.index(d) for d in document["copy_to"]])
    for name, kind in document.get("subject_kinds", {}).items():
        store.set_subject_kind_by_name(household_id, member, name, kind)
    for item in document.get("bag_items", []):     # sample items per subject or activity; real households write their own
        store.add_bag_item(household_id, member, item["subject"], item["label"], item["by"])
    return ["school day"]
