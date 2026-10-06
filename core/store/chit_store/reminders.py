"""Reminders: planned nudges for a person (or the whole family), one-off or recurring, in a day part (owned by planner/reminders)."""
from __future__ import annotations

from datetime import date
from typing import Any, Sequence

from .chore_series import _expected, _part, _weekday_csv
from .common import _member_id, _now, _optional_date, _required_text

_PART_RANK = {"morning": 0, "day": 1, "evening": 2, None: 3}


class Reminders:
    def _reminder_fields(self, connection: Any, household_id: str, title: str, member_id: "str | None",
                         on_date: "str | None", weekdays: Sequence[int], day_part: "str | None") -> tuple:
        if member_id is not None and not connection.execute(
            "SELECT 1 FROM household_members WHERE id = ? AND household_id = ?", (member_id, household_id)
        ).fetchone():
            raise ValueError("reminder member must belong to this household")
        when = _optional_date(on_date) if on_date else None
        if when and weekdays:
            raise ValueError("a reminder is either on one date or on weekdays, not both")
        return _required_text(title, "reminder title"), member_id, when, _weekday_csv(weekdays), _part(day_part)

    def add_reminder(self, household_id: str, title: str, member_id: "str | None" = None, on_date: "str | None" = None,
                     weekdays: Sequence[int] = (), day_part: "str | None" = None, reminder_id: "str | None" = None) -> str:
        reminder_id = reminder_id or _member_id()
        now = _now()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                fields = self._reminder_fields(connection, household_id, title, member_id, on_date, weekdays, day_part)
                connection.execute(
                    "INSERT INTO reminders(id, household_id, title, member_id, on_date, weekdays, day_part, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (reminder_id, household_id, *fields, now, now))
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return reminder_id

    def update_reminder(self, household_id: str, reminder_id: str, title: str, member_id: "str | None",
                        on_date: "str | None", weekdays: Sequence[int], day_part: "str | None") -> None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                fields = self._reminder_fields(connection, household_id, title, member_id, on_date, weekdays, day_part)
                cursor = connection.execute(
                    "UPDATE reminders SET title = ?, member_id = ?, on_date = ?, weekdays = ?, day_part = ?, updated_at = ? "
                    "WHERE id = ? AND household_id = ? AND archived = 0", (*fields, _now(), reminder_id, household_id))
                if cursor.rowcount != 1:
                    raise LookupError("reminder does not exist in this household")
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def archive_reminder(self, household_id: str, reminder_id: str) -> None:
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE reminders SET archived = 1, updated_at = ? WHERE id = ? AND household_id = ? AND archived = 0",
                (_now(), reminder_id, household_id))
            if cursor.rowcount != 1:
                raise LookupError("reminder does not exist in this household")

    def reminder_exists(self, reminder_id: str) -> bool:
        with self._connection() as connection:
            return connection.execute("SELECT 1 FROM reminders WHERE id = ?", (reminder_id,)).fetchone() is not None

    def _rows(self, household_id: str) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, title, member_id, on_date, weekdays, day_part FROM reminders "
                "WHERE household_id = ? AND archived = 0 ORDER BY created_at, rowid", (household_id,)).fetchall()
        return [{"id": r[0], "title": r[1], "member_id": r[2], "on_date": r[3],
                 "weekdays": [int(d) for d in r[4].split(",") if d], "day_part": r[5], "_csv": r[4]} for r in rows]

    def list_reminders(self, household_id: str) -> list[dict[str, Any]]:
        """All active reminders (settings screen). One-off reminders in the past are not shown."""
        today = date.today().isoformat()
        return [{k: v for k, v in row.items() if k != "_csv"} for row in self._rows(household_id)
                if row["on_date"] is None or row["on_date"] >= today]

    def list_reminders_for_day(self, household_id: str, day: date) -> list[dict[str, Any]]:
        """Reminders that apply on `day`, each with a `skipped` flag (callers hide skipped ones)."""
        skipped = self.skipped_item_ids(household_id, "reminder", day)
        out = []
        for row in self._rows(household_id):
            applies = row["on_date"] == day.isoformat() if row["on_date"] else _expected(row["_csv"], day)
            if applies:
                out.append({**{k: v for k, v in row.items() if k != "_csv"}, "skipped": row["id"] in skipped})
        out.sort(key=lambda r: _PART_RANK[r["day_part"]])
        return out

    def list_upcoming_reminders(self, household_id: str, after: date, days: int = 7) -> list[dict[str, Any]]:
        """One-off reminders dated in the days after `after`, soonest first."""
        end = date.fromordinal(after.toordinal() + days).isoformat()
        rows = [r for r in self._rows(household_id) if r["on_date"] and after.isoformat() < r["on_date"] <= end]
        rows.sort(key=lambda r: (r["on_date"], _PART_RANK[r["day_part"]]))
        return [{k: v for k, v in row.items() if k != "_csv"} for row in rows]
