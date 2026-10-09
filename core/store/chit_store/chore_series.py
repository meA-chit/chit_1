"""Recurring chores with completion history (owned by planner/chores; lives here until the store is split, open decision 12)."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Sequence

from .common import _member_id, _now, _required_text


def _weekday_csv(weekdays: Sequence[int]) -> str:
    days = sorted(set(int(day) for day in weekdays))
    if any(day < 0 or day > 6 for day in days):
        raise ValueError("weekdays must be 0 (Monday) to 6 (Sunday)")
    return ",".join(str(day) for day in days)


PART_IDS = ("morning", "day", "evening")
_PART_RANK = {"morning": 0, "day": 1, "evening": 2, None: 3}


def _part(value: "str | None") -> "str | None":
    if value in (None, ""):
        return None
    if value not in PART_IDS:
        raise ValueError("time of day must be morning, day or evening")
    return value


def _expected(csv: str, day: date) -> bool:
    return not csv or str(day.weekday()) in csv.split(",")


def compute_streak(csv: str, completed: "set[str]", today: date, horizon: int = 400, skipped: "set[str] | None" = None) -> int:
    """Consecutive expected days with a completion, ending today (or yesterday while today is still open).
    A day the household skipped is not expected, so it neither counts nor breaks the streak."""
    skipped = skipped or set()
    streak = 0
    day = today
    for _ in range(horizon):
        if _expected(csv, day) and day.isoformat() not in skipped:
            if day.isoformat() in completed:
                streak += 1
            elif day != today:
                break
        day -= timedelta(days=1)
    return streak


class ChoreSeries:
    def add_chore_series(self, household_id: str, title: str, assignee_id: "str | None" = None,
                         weekdays: Sequence[int] = (), due_time: "str | None" = None,
                         series_id: "str | None" = None, day_part: "str | None" = None) -> str:
        series_id = series_id or _member_id()
        now = _now()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                if assignee_id is not None and not connection.execute(
                    "SELECT 1 FROM household_members WHERE id = ? AND household_id = ?", (assignee_id, household_id)
                ).fetchone():
                    raise ValueError("assignee must be a member of this household")
                connection.execute(
                    "INSERT INTO chore_series(id, household_id, title, assignee_id, weekdays, due_time, day_part, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (series_id, household_id, _required_text(title, "chore title"), assignee_id,
                     _weekday_csv(weekdays), due_time or None, _part(day_part), now, now))
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return series_id

    def list_chores_today(self, household_id: str, today: date) -> list[dict[str, Any]]:
        """Chores expected today with done/skipped flags and streak (callers hide skipped ones). Chores not due today are not listed."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, title, assignee_id, weekdays, due_time, day_part FROM chore_series "
                "WHERE household_id = ? AND archived = 0 ORDER BY created_at, rowid", (household_id,)).fetchall()
            chores = []
            for series_id, title, assignee_id, csv, due_time, day_part in rows:
                if not _expected(csv, today):
                    continue
                completed = {d for (d,) in connection.execute(
                    "SELECT day FROM chore_completions WHERE series_id = ? AND day <= ?", (series_id, today.isoformat()))}
                skips = {d for (d,) in connection.execute(
                    "SELECT day FROM planner_skips WHERE kind = 'chore' AND item_id = ?", (series_id,))}
                chores.append({
                    "id": series_id, "title": title, "assignee_id": assignee_id, "due_time": due_time, "day_part": day_part,
                    "weekdays": [int(d) for d in csv.split(",") if d],
                    "done": today.isoformat() in completed,
                    "skipped": today.isoformat() in skips,
                    "streak": compute_streak(csv, completed, today, skipped=skips),
                })
            chores.sort(key=lambda chore: _PART_RANK[chore["day_part"]])  # stable: creation order within a part
            return chores

    def list_chore_series(self, household_id: str) -> list[dict[str, Any]]:
        """Every active chore with its schedule (for the settings screen), not only those due today."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, title, assignee_id, weekdays, day_part FROM chore_series "
                "WHERE household_id = ? AND archived = 0 ORDER BY created_at, rowid", (household_id,)).fetchall()
        return [{"id": r[0], "title": r[1], "assignee_id": r[2], "weekdays": [int(d) for d in r[3].split(",") if d], "day_part": r[4]}
                for r in rows]

    def update_chore_series(self, household_id: str, series_id: str, title: str, assignee_id: "str | None",
                            weekdays: Sequence[int], day_part: "str | None") -> None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                if assignee_id is not None and not connection.execute(
                    "SELECT 1 FROM household_members WHERE id = ? AND household_id = ?", (assignee_id, household_id)
                ).fetchone():
                    raise ValueError("assignee must be a member of this household")
                cursor = connection.execute(
                    "UPDATE chore_series SET title = ?, assignee_id = ?, weekdays = ?, day_part = ?, updated_at = ? "
                    "WHERE id = ? AND household_id = ? AND archived = 0",
                    (_required_text(title, "chore title"), assignee_id, _weekday_csv(weekdays), _part(day_part), _now(),
                     series_id, household_id))
                if cursor.rowcount != 1:
                    raise LookupError("chore does not exist in this household")
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def archive_chore_series(self, household_id: str, series_id: str) -> None:
        """Hide a chore everywhere but keep its history (streak data), so it can be restored later."""
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE chore_series SET archived = 1, updated_at = ? WHERE id = ? AND household_id = ? AND archived = 0",
                (_now(), series_id, household_id))
            if cursor.rowcount != 1:
                raise LookupError("chore does not exist in this household")

    def set_chore_done(self, household_id: str, series_id: str, day: date, done: bool,
                       completed_by: "str | None" = None) -> None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                if not connection.execute(
                    "SELECT 1 FROM chore_series WHERE id = ? AND household_id = ?", (series_id, household_id)
                ).fetchone():
                    raise LookupError("chore does not exist in this household")
                if done:
                    connection.execute(
                        "INSERT INTO chore_completions(series_id, day, completed_by, completed_at) VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING",
                        (series_id, day.isoformat(), completed_by, _now()))
                else:
                    connection.execute("DELETE FROM chore_completions WHERE series_id = ? AND day = ?",
                                       (series_id, day.isoformat()))
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def chore_series_exists(self, series_id: str) -> bool:
        with self._connection() as connection:
            return connection.execute("SELECT 1 FROM chore_series WHERE id = ?", (series_id,)).fetchone() is not None
