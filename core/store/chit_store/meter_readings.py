"""Manual meter readings (energy module): total and garden water today, other meters later.

Readings are the number on the meter, so they only ever count up. A batch is applied atomically: if any reading would make a
meter go backwards in time order, nothing is saved and the error names the dates.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .common import _now

METERS = ("water_total", "water_garden")


class MeterReadings:
    def list_meter_readings(self, household_id: str, meters: "tuple[str, ...]" = METERS) -> "list[dict[str, Any]]":
        marks = ",".join("?" for _ in meters)
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT meter, read_on, value, note FROM meter_readings WHERE household_id = ? AND meter IN (%s) ORDER BY read_on, meter" % marks,
                (household_id, *meters)).fetchall()
        return [{"meter": m, "read_on": d, "value": v, "note": n} for m, d, v, n in rows]

    def save_meter_readings(self, household_id: str, readings: "list[dict[str, Any]]", today: "date | None" = None) -> int:
        """Insert or replace readings (same meter and day replaces). Each item: meter, read_on (ISO date), value, note."""
        today = today or date.today()
        clean = []
        for item in readings:
            meter = item.get("meter")
            if meter not in METERS:
                raise ValueError("unknown meter")
            try:
                day = date.fromisoformat(str(item.get("read_on")))
            except ValueError:
                raise ValueError("%s is not a date (use YYYY-MM-DD)" % item.get("read_on")) from None
            if day > today:
                raise ValueError("%s is in the future" % day.isoformat())
            value = item.get("value")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 10_000_000:
                raise ValueError("%s: the reading must be a number, 0 or more" % day.isoformat())
            clean.append((meter, day.isoformat(), round(float(value), 3), str(item.get("note") or "").strip()[:200]))
        if not clean:
            raise ValueError("no readings to save")
        with self._connection() as connection:
            if not connection.execute("SELECT 1 FROM households WHERE id = ?", (household_id,)).fetchone():
                raise LookupError("household does not exist")
            connection.execute("BEGIN IMMEDIATE")
            try:
                for meter, day, value, note in clean:
                    connection.execute(
                        "INSERT INTO meter_readings(household_id, meter, read_on, value, note, updated_at) VALUES (?, ?, ?, ?, ?, ?) "
                        "ON CONFLICT(household_id, meter, read_on) DO UPDATE SET value = excluded.value, note = excluded.note, updated_at = excluded.updated_at",
                        (household_id, meter, day, value, note, _now()))
                for meter in {m for m, *_ in clean}:
                    previous = None
                    for day, value in connection.execute(
                            "SELECT read_on, value FROM meter_readings WHERE household_id = ? AND meter = ? ORDER BY read_on", (household_id, meter)):
                        if previous and value < previous[1]:
                            raise ValueError("%s reads %s, lower than %s on %s: a meter only counts up" % (day, _fmt(value), _fmt(previous[1]), previous[0]))
                        previous = (day, value)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return len(clean)

    def delete_meter_readings_on(self, household_id: str, day: str) -> int:
        """Remove every meter's reading for one day."""
        with self._connection() as connection:
            cursor = connection.execute("DELETE FROM meter_readings WHERE household_id = ? AND read_on = ?", (household_id, day))
            connection.commit()
            return cursor.rowcount


def _fmt(value: float) -> str:
    return ("%.3f" % value).rstrip("0").rstrip(".")
