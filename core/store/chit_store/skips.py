"""Per-day skips for chores and reminders (planner/chores, planner/reminders): operations management on the dashboard."""
from __future__ import annotations

from datetime import date

from .common import _now

_TABLES = {"chore": "chore_series", "reminder": "reminders"}


class Skips:
    def set_skipped(self, household_id: str, kind: str, item_id: str, day: date, skipped: bool) -> None:
        if kind not in _TABLES:
            raise ValueError("kind must be chore or reminder")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                if not connection.execute(
                    "SELECT 1 FROM %s WHERE id = ? AND household_id = ? AND archived = 0" % _TABLES[kind], (item_id, household_id)
                ).fetchone():
                    raise LookupError("%s does not exist in this household" % kind)
                if skipped:
                    connection.execute(
                        "INSERT INTO planner_skips(household_id, kind, item_id, day, created_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                        (household_id, kind, item_id, day.isoformat(), _now()))
                else:
                    connection.execute("DELETE FROM planner_skips WHERE kind = ? AND item_id = ? AND day = ?",
                                       (kind, item_id, day.isoformat()))
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def skipped_days(self, kind: str, item_id: str) -> "set[str]":
        with self._connection() as connection:
            return {d for (d,) in connection.execute("SELECT day FROM planner_skips WHERE kind = ? AND item_id = ?", (kind, item_id))}

    def skipped_item_ids(self, household_id: str, kind: str, day: date) -> "set[str]":
        with self._connection() as connection:
            return {i for (i,) in connection.execute(
                "SELECT item_id FROM planner_skips WHERE household_id = ? AND kind = ? AND day = ?", (household_id, kind, day.isoformat()))}
