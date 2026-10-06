"""Kids module data: star chores and goals, grades, the school-day plan and medication (kids/*; lives here until the store is split)."""
from __future__ import annotations

from datetime import date
from typing import Any, Sequence

from .common import _member_id, _now, _required_text

GRADE_TYPES = ("written", "oral")
SUBJECT_KINDS = ("main", "other")
SLOT_KINDS = ("lesson", "break", "meal", "care")


def _csv(weekdays: Sequence[int]) -> str:
    days = sorted(set(int(d) for d in weekdays))
    if any(d < 0 or d > 6 for d in days):
        raise ValueError("weekdays must be 0 (Monday) to 6 (Sunday)")
    return ",".join(str(d) for d in days)


def _hhmm(value: Any, label: str) -> str:
    text = str(value or "")
    if len(text) != 5 or text[2] != ":" or not (text[:2] + text[3:]).isdigit() or int(text[:2]) > 23 or int(text[3:]) > 59:
        raise ValueError("%s must look like 08:30" % label)
    return text


def _text(value: Any) -> "str | None":
    text = (str(value).strip() if value is not None else "")
    return text[:500] or None


class Kids:
    # ---------- shared checks ----------
    def _child(self, connection: Any, household_id: str, member_id: str) -> None:
        if not connection.execute("SELECT 1 FROM household_members WHERE id = ? AND household_id = ? AND role = 'child'",
                                  (member_id, household_id)).fetchone():
            raise ValueError("member must be a child in this household")

    def _owned(self, connection: Any, table: str, household_id: str, row_id: str) -> None:
        if not connection.execute("SELECT 1 FROM %s WHERE id = ? AND household_id = ?" % table, (row_id, household_id)).fetchone():
            raise LookupError("not found in this household")

    # ---------- stars ----------
    def set_star_chore(self, household_id: str, series_id: str, enabled: bool) -> None:
        with self._connection() as connection:
            row = connection.execute("SELECT assignee_id FROM chore_series WHERE id = ? AND household_id = ? AND archived = 0",
                                     (series_id, household_id)).fetchone()
            if not row:
                raise LookupError("chore does not exist in this household")
            if enabled and not row[0]:
                raise ValueError("a star chore needs an assignee, so the star has an owner")
            if enabled:
                connection.execute("INSERT OR IGNORE INTO kid_star_chores(series_id) VALUES (?)", (series_id,))
            else:
                connection.execute("DELETE FROM kid_star_chores WHERE series_id = ?", (series_id,))

    def star_chore_ids(self, household_id: str) -> "set[str]":
        with self._connection() as connection:
            return {s for (s,) in connection.execute(
                "SELECT k.series_id FROM kid_star_chores k JOIN chore_series c ON c.id = k.series_id WHERE c.household_id = ?", (household_id,))}

    def set_chore_outcome(self, household_id: str, series_id: str, day: date, outcome: "str | None") -> None:
        if outcome not in (None, "well", "again"):
            raise ValueError("outcome must be well, again or null")
        with self._connection() as connection:
            if not connection.execute(
                    "SELECT 1 FROM kid_star_chores k JOIN chore_series c ON c.id = k.series_id WHERE k.series_id = ? AND c.household_id = ?",
                    (series_id, household_id)).fetchone():
                raise LookupError("not a star chore in this household")
            if outcome is None:
                connection.execute("DELETE FROM kid_chore_outcomes WHERE series_id = ? AND day = ?", (series_id, day.isoformat()))
                return
            if not connection.execute("SELECT 1 FROM chore_completions WHERE series_id = ? AND day = ?", (series_id, day.isoformat())).fetchone():
                raise ValueError("the chore has not been ticked off that day")
            connection.execute(
                "INSERT INTO kid_chore_outcomes(series_id, day, outcome, granted_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(series_id, day) DO UPDATE SET outcome = excluded.outcome, granted_at = excluded.granted_at",
                (series_id, day.isoformat(), outcome, _now()))

    def chore_outcomes(self, household_id: str, day: date) -> "dict[str, str]":
        with self._connection() as connection:
            return dict(connection.execute(
                "SELECT o.series_id, o.outcome FROM kid_chore_outcomes o JOIN chore_series c ON c.id = o.series_id "
                "WHERE c.household_id = ? AND o.day = ?", (household_id, day.isoformat())).fetchall())

    def star_days(self, household_id: str, member_id: str, since: str) -> "dict[str, int]":
        """{day: stars} for a child since a date. A star is a 'well' outcome on a star chore assigned to the child that is still ticked off."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT o.day, COUNT(*) FROM kid_chore_outcomes o "
                "JOIN chore_series c ON c.id = o.series_id JOIN kid_star_chores k ON k.series_id = c.id "
                "JOIN chore_completions d ON d.series_id = o.series_id AND d.day = o.day "
                "WHERE c.household_id = ? AND c.assignee_id = ? AND o.outcome = 'well' AND o.day >= ? GROUP BY o.day",
                (household_id, member_id, since)).fetchall()
        return dict(rows)

    # ---------- goals ----------
    def add_goal(self, household_id: str, member_id: str, title: str, cost: int, note: "str | None", started_on: date) -> str:
        goal_id = _member_id()
        if isinstance(cost, bool) or not isinstance(cost, int) or not 1 <= cost <= 10000:
            raise ValueError("cost must be a whole number of stars from 1 to 10000")
        with self._connection() as connection:
            self._child(connection, household_id, member_id)
            connection.execute(
                "INSERT INTO kid_goals(id, household_id, member_id, title, note, cost, started_on, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (goal_id, household_id, member_id, _required_text(title, "goal title"), _text(note), cost, started_on.isoformat(), _now()))
        return goal_id

    def update_goal(self, household_id: str, goal_id: str, title: str, cost: int, note: "str | None") -> None:
        if isinstance(cost, bool) or not isinstance(cost, int) or not 1 <= cost <= 10000:
            raise ValueError("cost must be a whole number of stars from 1 to 10000")
        with self._connection() as connection:
            self._owned(connection, "kid_goals", household_id, goal_id)
            connection.execute("UPDATE kid_goals SET title = ?, cost = ?, note = ? WHERE id = ?",
                               (_required_text(title, "goal title"), cost, _text(note), goal_id))

    def set_goal_status(self, household_id: str, goal_id: str, status: str) -> None:
        if status not in ("active", "approved", "archived"):
            raise ValueError("invalid status")
        with self._connection() as connection:
            self._owned(connection, "kid_goals", household_id, goal_id)
            connection.execute("UPDATE kid_goals SET status = ?, approved_at = ? WHERE id = ?",
                               (status, _now() if status == "approved" else None, goal_id))

    def list_goals(self, household_id: str) -> "list[dict[str, Any]]":
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, member_id, title, note, cost, started_on, status, approved_at FROM kid_goals "
                "WHERE household_id = ? AND status != 'archived' ORDER BY cost, created_at", (household_id,)).fetchall()
        keys = ("id", "member_id", "title", "note", "cost", "started_on", "status", "approved_at")
        return [dict(zip(keys, row)) for row in rows]

    # ---------- grades ----------
    def get_grade_weights(self, household_id: str) -> "dict[str, int]":
        with self._connection() as connection:
            row = connection.execute("SELECT main_written_pct, other_written_pct FROM kid_settings WHERE household_id = ?", (household_id,)).fetchone()
        return {"main_written_pct": row[0], "other_written_pct": row[1]} if row else {"main_written_pct": 50, "other_written_pct": 30}

    def set_grade_weights(self, household_id: str, main_written_pct: int, other_written_pct: int) -> None:
        for value in (main_written_pct, other_written_pct):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
                raise ValueError("weights are whole percentages from 0 to 100")
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO kid_settings(household_id, main_written_pct, other_written_pct) VALUES (?, ?, ?) "
                "ON CONFLICT(household_id) DO UPDATE SET main_written_pct = excluded.main_written_pct, other_written_pct = excluded.other_written_pct",
                (household_id, main_written_pct, other_written_pct))

    def add_subject(self, household_id: str, member_id: str, name: str, kind: str) -> str:
        if kind not in SUBJECT_KINDS:
            raise ValueError("subject kind must be main or other")
        subject_id = _member_id()
        with self._connection() as connection:
            self._child(connection, household_id, member_id)
            connection.execute("INSERT INTO kid_subjects(id, household_id, member_id, name, kind, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                               (subject_id, household_id, member_id, _required_text(name, "subject name"), kind, _now()))
        return subject_id

    def update_subject(self, household_id: str, subject_id: str, name: str, kind: str) -> None:
        if kind not in SUBJECT_KINDS:
            raise ValueError("subject kind must be main or other")
        with self._connection() as connection:
            self._owned(connection, "kid_subjects", household_id, subject_id)
            connection.execute("UPDATE kid_subjects SET name = ?, kind = ? WHERE id = ?", (_required_text(name, "subject name"), kind, subject_id))

    def archive_subject(self, household_id: str, subject_id: str) -> None:
        with self._connection() as connection:
            self._owned(connection, "kid_subjects", household_id, subject_id)
            connection.execute("UPDATE kid_subjects SET archived = 1 WHERE id = ?", (subject_id,))

    def add_grade(self, household_id: str, subject_id: str, grade_type: str, grade: float, given_on: date, note: "str | None") -> str:
        if grade_type not in GRADE_TYPES:
            raise ValueError("grade type must be written or oral")
        if isinstance(grade, bool) or not isinstance(grade, (int, float)) or not 1 <= grade <= 6:
            raise ValueError("a grade is a number from 1 to 6")
        grade_id = _member_id()
        with self._connection() as connection:
            if not connection.execute("SELECT 1 FROM kid_subjects WHERE id = ? AND household_id = ? AND archived = 0", (subject_id, household_id)).fetchone():
                raise LookupError("subject does not exist in this household")
            connection.execute("INSERT INTO kid_grades(id, subject_id, grade_type, grade, given_on, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (grade_id, subject_id, grade_type, float(grade), given_on.isoformat(), _text(note), _now()))
        return grade_id

    def delete_grade(self, household_id: str, grade_id: str) -> None:
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM kid_grades WHERE id = ? AND subject_id IN (SELECT id FROM kid_subjects WHERE household_id = ?)", (grade_id, household_id))
            if cursor.rowcount != 1:
                raise LookupError("grade does not exist in this household")

    def list_subjects_with_grades(self, household_id: str, member_id: str) -> "list[dict[str, Any]]":
        with self._connection() as connection:
            subjects = connection.execute(
                "SELECT id, name, kind FROM kid_subjects WHERE household_id = ? AND member_id = ? AND archived = 0 ORDER BY kind, name",
                (household_id, member_id)).fetchall()
            out = []
            for subject_id, name, kind in subjects:
                grades = connection.execute(
                    "SELECT id, grade_type, grade, given_on, note FROM kid_grades WHERE subject_id = ? ORDER BY given_on, created_at", (subject_id,)).fetchall()
                out.append({"id": subject_id, "name": name, "kind": kind, "grades": [
                    {"id": g[0], "grade_type": g[1], "grade": g[2], "given_on": g[3], "note": g[4]} for g in grades]})
        return out

    # ---------- school-day plan ----------
    def add_school_slot(self, household_id: str, member_id: str, weekday: int, start: str, end: str, title: str, kind: str, note: "str | None") -> str:
        if kind not in SLOT_KINDS:
            raise ValueError("kind must be lesson, break, meal or care")
        if isinstance(weekday, bool) or not isinstance(weekday, int) or not 0 <= weekday <= 6:
            raise ValueError("weekday must be 0 (Monday) to 6 (Sunday)")
        start, end = _hhmm(start, "start"), _hhmm(end, "end")
        if end <= start:
            raise ValueError("the end must be after the start")
        slot_id = _member_id()
        with self._connection() as connection:
            self._child(connection, household_id, member_id)
            connection.execute(
                "INSERT INTO kid_school_slots(id, household_id, member_id, weekday, start_time, end_time, title, kind, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (slot_id, household_id, member_id, weekday, start, end, _required_text(title, "title"), kind, _text(note)))
        return slot_id

    def update_school_slot(self, household_id: str, slot_id: str, start: str, end: str, title: str, kind: str, note: "str | None") -> None:
        if kind not in SLOT_KINDS:
            raise ValueError("kind must be lesson, break, meal or care")
        start, end = _hhmm(start, "start"), _hhmm(end, "end")
        if end <= start:
            raise ValueError("the end must be after the start")
        with self._connection() as connection:
            self._owned(connection, "kid_school_slots", household_id, slot_id)
            connection.execute("UPDATE kid_school_slots SET start_time = ?, end_time = ?, title = ?, kind = ?, note = ? WHERE id = ?",
                               (start, end, _required_text(title, "title"), kind, _text(note), slot_id))

    def delete_school_slot(self, household_id: str, slot_id: str) -> None:
        with self._connection() as connection:
            self._owned(connection, "kid_school_slots", household_id, slot_id)
            connection.execute("DELETE FROM kid_school_slots WHERE id = ?", (slot_id,))

    def copy_school_day(self, household_id: str, member_id: str, from_weekday: int, to_weekdays: Sequence[int]) -> int:
        targets = [d for d in set(int(d) for d in to_weekdays) if d != from_weekday and 0 <= d <= 6]
        with self._connection() as connection:
            self._child(connection, household_id, member_id)
            rows = connection.execute(
                "SELECT start_time, end_time, title, kind, note FROM kid_school_slots WHERE household_id = ? AND member_id = ? AND weekday = ?",
                (household_id, member_id, from_weekday)).fetchall()
            for target in targets:
                connection.execute("DELETE FROM kid_school_slots WHERE household_id = ? AND member_id = ? AND weekday = ?", (household_id, member_id, target))
                for start, end, title, kind, note in rows:
                    connection.execute(
                        "INSERT INTO kid_school_slots(id, household_id, member_id, weekday, start_time, end_time, title, kind, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (_member_id(), household_id, member_id, target, start, end, title, kind, note))
        return len(targets)

    def list_school_slots(self, household_id: str, member_id: str, weekday: "int | None" = None) -> "list[dict[str, Any]]":
        query = "SELECT id, weekday, start_time, end_time, title, kind, note FROM kid_school_slots WHERE household_id = ? AND member_id = ?"
        args: list = [household_id, member_id]
        if weekday is not None:
            query += " AND weekday = ?"
            args.append(weekday)
        with self._connection() as connection:
            rows = connection.execute(query + " ORDER BY weekday, start_time", args).fetchall()
        keys = ("id", "weekday", "start", "end", "title", "kind", "note")
        return [dict(zip(keys, row)) for row in rows]

    # ---------- medication ----------
    def _med_fields(self, connection: Any, household_id: str, name: str, time_of_day: str, weekdays: Sequence[int],
                    remind_member_id: "str | None", supply: "int | None"):
        if remind_member_id and not connection.execute(
                "SELECT 1 FROM household_members WHERE id = ? AND household_id = ? AND role = 'adult'", (remind_member_id, household_id)).fetchone():
            raise ValueError("the reminder goes to an adult in this household")
        if supply is not None and (isinstance(supply, bool) or not isinstance(supply, int) or supply < 0):
            raise ValueError("supply is a whole number of doses")
        return _required_text(name, "medication name"), _hhmm(time_of_day, "time"), _csv(weekdays), remind_member_id or None, supply

    def add_med(self, household_id: str, member_id: str, name: str, dose: "str | None", time_of_day: str, weekdays: Sequence[int],
                remind_member_id: "str | None", supply: "int | None") -> str:
        med_id = _member_id()
        with self._connection() as connection:
            self._child(connection, household_id, member_id)
            n, t, w, r, s = self._med_fields(connection, household_id, name, time_of_day, weekdays, remind_member_id, supply)
            connection.execute(
                "INSERT INTO kid_meds(id, household_id, member_id, name, dose, time_of_day, weekdays, remind_member_id, supply, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (med_id, household_id, member_id, n, _text(dose), t, w, r, s, _now()))
        return med_id

    def update_med(self, household_id: str, med_id: str, name: str, dose: "str | None", time_of_day: str, weekdays: Sequence[int],
                   remind_member_id: "str | None", supply: "int | None") -> None:
        with self._connection() as connection:
            self._owned(connection, "kid_meds", household_id, med_id)
            n, t, w, r, s = self._med_fields(connection, household_id, name, time_of_day, weekdays, remind_member_id, supply)
            connection.execute("UPDATE kid_meds SET name = ?, dose = ?, time_of_day = ?, weekdays = ?, remind_member_id = ?, supply = ? WHERE id = ?",
                               (n, _text(dose), t, w, r, s, med_id))

    def archive_med(self, household_id: str, med_id: str) -> None:
        with self._connection() as connection:
            self._owned(connection, "kid_meds", household_id, med_id)
            connection.execute("UPDATE kid_meds SET archived = 1 WHERE id = ?", (med_id,))

    def log_med(self, household_id: str, med_id: str, day: date, status: "str | None") -> None:
        """Mark a dose given or missed (None clears it). Giving a dose uses one unit of the supply; clearing or changing it gives the unit back."""
        if status not in (None, "given", "missed"):
            raise ValueError("status must be given, missed or null")
        with self._connection() as connection:
            self._owned(connection, "kid_meds", household_id, med_id)
            before = connection.execute("SELECT status FROM kid_med_log WHERE med_id = ? AND day = ?", (med_id, day.isoformat())).fetchone()
            was_given = bool(before and before[0] == "given")
            if status is None:
                connection.execute("DELETE FROM kid_med_log WHERE med_id = ? AND day = ?", (med_id, day.isoformat()))
            else:
                connection.execute(
                    "INSERT INTO kid_med_log(med_id, day, status, logged_at) VALUES (?, ?, ?, ?) "
                    "ON CONFLICT(med_id, day) DO UPDATE SET status = excluded.status, logged_at = excluded.logged_at",
                    (med_id, day.isoformat(), status, _now()))
            now_given = status == "given"
            if was_given and not now_given:
                connection.execute("UPDATE kid_meds SET supply = supply + 1 WHERE id = ? AND supply IS NOT NULL", (med_id,))
            elif now_given and not was_given:
                connection.execute("UPDATE kid_meds SET supply = MAX(supply - 1, 0) WHERE id = ? AND supply IS NOT NULL", (med_id,))

    def list_meds(self, household_id: str, member_id: str, since: str) -> "list[dict[str, Any]]":
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, name, dose, time_of_day, weekdays, remind_member_id, supply FROM kid_meds "
                "WHERE household_id = ? AND member_id = ? AND archived = 0 ORDER BY time_of_day, name", (household_id, member_id)).fetchall()
            meds = []
            for med_id, name, dose, tod, csv, remind, supply in rows:
                log = dict(connection.execute("SELECT day, status FROM kid_med_log WHERE med_id = ? AND day >= ?", (med_id, since)).fetchall())
                meds.append({"id": med_id, "name": name, "dose": dose, "time": tod, "weekdays": [int(d) for d in csv.split(",") if d],
                             "remind_member_id": remind, "supply": supply, "log": log})
        return meds
