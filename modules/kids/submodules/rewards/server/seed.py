"""Seed star chores, outcomes and goals from seed/kids/rewards.json (ADR-0010). Idempotent: skipped when the household has goals."""
from __future__ import annotations

from datetime import date, timedelta
import json

from chit_server.paths import REPO_ROOT

SEED_FILE = REPO_ROOT / "seed" / "kids" / "rewards.json"


def seed(store, today=None):
    today = today or date.today()
    if not SEED_FILE.is_file():
        return []
    document = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    household_id = document["household_id"]
    if store.list_goals(household_id) or not store.chore_series_exists(document["star_chores"][0]):
        return []
    for chore in document["star_chores"]:
        store.set_star_chore(household_id, chore, True)
    for outcome in document["outcomes"]:
        store.set_chore_outcome(household_id, outcome["chore"], today - timedelta(days=outcome["days_ago"]), outcome["outcome"])
    for goal in document["goals"]:
        store.add_goal(household_id, goal["member_id"], goal["title"], goal["cost"], goal.get("note"), date(1, 1, 1))
    return [g["title"] for g in document["goals"]]
