"""Seed subjects and grades from seed/kids/learning.json (ADR-0010). Dates are relative so the sample never goes stale."""
from __future__ import annotations

from datetime import date, timedelta
import json

from chit_server.paths import REPO_ROOT

SEED_FILE = REPO_ROOT / "seed" / "kids" / "learning.json"


def seed(store, today=None):
    today = today or date.today()
    if not SEED_FILE.is_file():
        return []
    document = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    household_id, member = document["household_id"], document["member_id"]
    if store.list_subjects_with_grades(household_id, member):
        return []
    store.set_grade_weights(household_id, **document["weights"])
    for subject in document["subjects"]:
        subject_id = store.add_subject(household_id, member, subject["name"], subject["kind"])
        for entry in subject["grades"]:
            store.add_grade(household_id, subject_id, entry["type"], entry["grade"], today - timedelta(days=entry["days_ago"]), entry.get("note"))
    return [s["name"] for s in document["subjects"]]
