"""Seed grades and homework from seed/kids/learning.json (ADR-0010). Dates are relative so the sample never goes stale."""
from __future__ import annotations

from datetime import date, timedelta
import json

from chit_server.paths import REPO_ROOT

SEED_FILE = REPO_ROOT / "seed" / "kids" / "learning.json"


def seed(store, today=None):
    """Grades for the subjects the school plan created (kids/school seeds first). A name that is not in the plan is skipped: subjects only come from the plan."""
    today = today or date.today()
    if not SEED_FILE.is_file():
        return []
    document = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    household_id, member = document["household_id"], document["member_id"]
    if any(s["grades"] for s in store.list_subjects_with_grades(household_id, member)):
        return []
    _seed_tasks(store, household_id, member, document.get("tasks", []), today)
    store.set_grade_weights(household_id, **document["weights"])
    subjects = {s["name"].lower(): s["id"] for s in store.list_subjects(household_id, member)}
    seeded = []
    for subject in document["subjects"]:
        subject_id = subjects.get(subject["name"].lower())
        if subject_id is None:
            continue
        for entry in subject["grades"]:
            store.add_grade(household_id, subject_id, entry["type"], entry["grade"], today - timedelta(days=entry["days_ago"]), entry.get("note"))
        seeded.append(subject["name"])
    return seeded


def _seed_tasks(store, household_id, member, tasks, today):
    for task in tasks:
        task_id = store.add_task(household_id, member, task["kind"], task["subject"], task["title"], (today + timedelta(days=task["days_ahead"])).isoformat(),
                                 None, task["by"], today)
        if "done_days_ago" in task:
            store.set_task_done(household_id, task_id, True)
