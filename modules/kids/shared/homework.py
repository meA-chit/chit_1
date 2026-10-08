"""Homework and tests: the summary tiles and the per-task view. Pure functions."""
from __future__ import annotations

from datetime import date, timedelta

TEST_HORIZON_DAYS = 14


def view(task, today):
    """A stored task -> what the clients show. `days` is the days until it is due (negative when overdue)."""
    due = date.fromisoformat(task["due_on"])
    return {"id": task["id"], "kind": task["kind"], "subject": task["subject"], "title": task["title"], "due_on": task["due_on"],
            "note": task["note"], "done": task["done_at"] is not None, "done_on": task["done_at"][:10] if task["done_at"] else None,
            "dismissed": task.get("dismissed_at") is not None, "by": task["created_by"], "days": (due - today).days}


def summarize(tasks, today):
    """The tiles on the homework screen: due tomorrow, tests soon, overdue, done this week, and the open load per school day."""
    monday = today - timedelta(days=today.weekday())
    openn = [t for t in tasks if not t["done"] and not t["dismissed"]]       # a task that is not relevant is neither open nor done
    week = []
    for offset in range(5):
        day = (monday + timedelta(days=offset)).isoformat()
        week.append({"day": day, "open": sum(1 for t in openn if t["due_on"] == day), "tests": sum(1 for t in openn if t["due_on"] == day and t["kind"] == "test")})
    return {
        "due_tomorrow": sum(1 for t in openn if t["days"] == 1),
        "tests_soon": sum(1 for t in openn if t["kind"] == "test" and 0 <= t["days"] <= TEST_HORIZON_DAYS),
        "overdue": sum(1 for t in openn if t["days"] < 0),
        "done_this_week": sum(1 for t in tasks if t["done"] and t["done_on"] >= monday.isoformat()),
        "week": week,
    }
