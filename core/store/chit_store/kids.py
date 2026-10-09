"""Kids module data: star chores and goals, grades, the school-day plan and medication (kids/*; lives here until the store is split)."""
from __future__ import annotations

from datetime import date
import re
from typing import Any, Sequence

from .common import _member_id, _now, _required_text

GRADE_TYPES = ("written", "oral")
SUBJECT_KINDS = ("core", "minor", "elective")
CODE_MAX = 6
_KIND_RANK = "CASE kind WHEN 'core' THEN 0 WHEN 'minor' THEN 1 ELSE 2 END"
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


def default_code(name: str, taken: "set[str]") -> str:
    """A short, unique code for a subject name: the name itself when short, the initials of several words, else the first letters.
    `taken` holds the lower-case codes already used by the child's other subjects."""
    name = name.strip()
    words = [w for w in re.split(r"[\s/_&.\-]+", name) if w]
    base = name if len(name) <= 5 else "".join(w[0] for w in words)[:4].upper() if len(words) > 1 else (words[0][:4] if words else name[:4])
    base = (base or "?")[:CODE_MAX]
    code, n = base, 2
    while code.lower() in taken:
        code = base[:CODE_MAX - len(str(n))] + str(n)
        n += 1
    return code


def clean_code(value: Any) -> str:
    code = str(value if value is not None else "").strip()
    if not 1 <= len(code) <= CODE_MAX or re.search(r"\s", code):
        raise ValueError("a code is 1 to %d characters without spaces" % CODE_MAX)
    return code


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
                connection.execute("INSERT INTO kid_star_chores(series_id) VALUES (?) ON CONFLICT DO NOTHING", (series_id,))
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
        """The written share (percent) of a subject's average, per subject type; the oral share is the rest."""
        with self._connection() as connection:
            row = connection.execute("SELECT core_written_pct, minor_written_pct, elective_written_pct FROM kid_settings WHERE household_id = ?", (household_id,)).fetchone()
        return dict(zip(("core_written_pct", "minor_written_pct", "elective_written_pct"), row)) if row else {"core_written_pct": 50, "minor_written_pct": 30, "elective_written_pct": 30}

    def set_grade_weights(self, household_id: str, core_written_pct: int, minor_written_pct: int, elective_written_pct: int) -> None:
        for value in (core_written_pct, minor_written_pct, elective_written_pct):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
                raise ValueError("weights are whole percentages from 0 to 100")
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO kid_settings(household_id, core_written_pct, minor_written_pct, elective_written_pct) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(household_id) DO UPDATE SET core_written_pct = excluded.core_written_pct, minor_written_pct = excluded.minor_written_pct, "
                "elective_written_pct = excluded.elective_written_pct",
                (household_id, core_written_pct, minor_written_pct, elective_written_pct))

    # Subjects are never typed in on their own: a subject is a lesson title in the child's school-day plan (kids/school), with a type.
    def _sync_subjects(self, connection: Any, household_id: str, member_id: str) -> None:
        """Make the child's subjects match the lesson titles in their plan. New titles become 'minor' subjects with a generated code (a parent
        sets the type, code and full name); a title that left the plan archives its subject, which keeps the grades and returns if the lesson is added again."""
        titles: "dict[str, str]" = {}
        for (title,) in connection.execute("SELECT title FROM kid_school_slots WHERE household_id = ? AND member_id = ? AND kind = 'lesson' ORDER BY weekday, start_time",
                                           (household_id, member_id)):
            titles.setdefault(title.strip().lower(), title.strip())
        rows = connection.execute("SELECT id, name, archived, code FROM kid_subjects WHERE household_id = ? AND member_id = ?", (household_id, member_id)).fetchall()
        known = {name.lower(): (subject_id, archived) for subject_id, name, archived, _ in rows}
        taken = {code.lower() for _, _, archived, code in rows if code and not archived}
        for subject_id, name, archived, code in rows:                      # subjects from before codes existed
            if not code and not archived and name.strip().lower() in titles:
                fresh = default_code(name, taken)
                taken.add(fresh.lower())
                connection.execute("UPDATE kid_subjects SET code = ? WHERE id = ?", (fresh, subject_id))
        for key, title in titles.items():
            if key not in known:
                fresh = default_code(title, taken)
                taken.add(fresh.lower())
                connection.execute("INSERT INTO kid_subjects(id, household_id, member_id, name, kind, code, created_at) VALUES (?, ?, ?, ?, 'minor', ?, ?)",
                                   (_member_id(), household_id, member_id, title, fresh, _now()))
            elif known[key][1]:
                code = connection.execute("SELECT code FROM kid_subjects WHERE id = ?", (known[key][0],)).fetchone()[0]
                if not code or code.lower() in taken:                      # its old code was taken while it was away
                    code = default_code(title, taken)
                taken.add(code.lower())
                connection.execute("UPDATE kid_subjects SET archived = 0, code = ? WHERE id = ?", (code, known[key][0]))
        for key, (subject_id, archived) in known.items():
            if key not in titles and not archived:
                connection.execute("UPDATE kid_subjects SET archived = 1 WHERE id = ?", (subject_id,))

    def _rename_subject_rows(self, connection: Any, member_id: str, old: str, new: str) -> None:
        """A subject's name is also written on its lessons, homework and bag items: rename them together so they stay one subject."""
        connection.execute("UPDATE kid_subjects SET name = ? WHERE member_id = ? AND lower(name) = lower(?)", (new, member_id, old))
        connection.execute("UPDATE kid_school_slots SET title = ? WHERE member_id = ? AND kind = 'lesson' AND lower(title) = lower(?)", (new, member_id, old))
        connection.execute("UPDATE kid_tasks SET subject = ? WHERE member_id = ? AND lower(subject) = lower(?)", (new, member_id, old))
        connection.execute("UPDATE kid_bag_items SET subject = ? WHERE member_id = ? AND lower(subject) = lower(?) "
                           "AND NOT EXISTS (SELECT 1 FROM kid_bag_items o WHERE o.member_id = kid_bag_items.member_id "
                           "AND o.subject = ? AND o.label = kid_bag_items.label)", (new, member_id, old, new))   # skip items the new name already has

    def _free_code(self, connection: Any, member_id: str, code: str, own_id: "str | None") -> None:
        if connection.execute("SELECT 1 FROM kid_subjects WHERE member_id = ? AND archived = 0 AND lower(code) = lower(?) AND id IS NOT ?", (member_id, code, own_id)).fetchone():
            raise ValueError("another subject already uses the code %s" % code)

    def update_subject(self, household_id: str, subject_id: str, name: "str | None" = None, code: "str | None" = None, kind: "str | None" = None) -> None:
        """Change a subject's full name, code and/or type (None leaves it as it is). A new name is carried to its lessons, homework and bag items."""
        if kind is not None and kind not in SUBJECT_KINDS:
            raise ValueError("subject type must be core, minor or elective")
        with self._connection() as connection:
            self._owned(connection, "kid_subjects", household_id, subject_id)
            member_id, old_name = connection.execute("SELECT member_id, name FROM kid_subjects WHERE id = ?", (subject_id,)).fetchone()
            new_name = _required_text(str(name), "name")[:60] if name is not None else None
            new_code = clean_code(code) if code is not None else None
            if new_name is not None and new_name != old_name:
                if connection.execute("SELECT 1 FROM kid_subjects WHERE member_id = ? AND lower(name) = lower(?) AND id != ?", (member_id, new_name, subject_id)).fetchone():
                    raise ValueError("another subject already has the name %s" % new_name)
            if new_code is not None:
                self._free_code(connection, member_id, new_code, subject_id)
            if new_name is not None and new_name != old_name:
                self._rename_subject_rows(connection, member_id, old_name, new_name)
            if new_code is not None:
                connection.execute("UPDATE kid_subjects SET code = ? WHERE id = ?", (new_code, subject_id))
            if kind is not None:
                connection.execute("UPDATE kid_subjects SET kind = ? WHERE id = ?", (kind, subject_id))

    def merge_subjects(self, household_id: str, source_id: str, target_id: str) -> None:
        """Fold a duplicate subject (`source`) into the one to keep (`target`), for the same child. The duplicate's lessons take the kept
        subject's name, its grades move over, its homework and bag items follow, and the duplicate is deleted. The kept subject's name, code and type stay."""
        if source_id == target_id:
            raise ValueError("choose a different subject to merge into")
        with self._connection() as connection:
            self._owned(connection, "kid_subjects", household_id, source_id)
            self._owned(connection, "kid_subjects", household_id, target_id)
            member_id, source_name = connection.execute("SELECT member_id, name FROM kid_subjects WHERE id = ?", (source_id,)).fetchone()
            target_member, target_name = connection.execute("SELECT member_id, name FROM kid_subjects WHERE id = ?", (target_id,)).fetchone()
            if member_id != target_member:
                raise ValueError("a subject can only be merged into another subject of the same child")
            connection.execute("UPDATE kid_school_slots SET title = ? WHERE member_id = ? AND kind = 'lesson' AND lower(title) = lower(?)", (target_name, member_id, source_name))
            connection.execute("UPDATE kid_tasks SET subject = ? WHERE member_id = ? AND lower(subject) = lower(?)", (target_name, member_id, source_name))
            connection.execute("UPDATE kid_bag_items SET subject = ? WHERE member_id = ? AND lower(subject) = lower(?) "
                               "AND NOT EXISTS (SELECT 1 FROM kid_bag_items o WHERE o.member_id = kid_bag_items.member_id "
                               "AND o.subject = ? AND o.label = kid_bag_items.label)", (target_name, member_id, source_name, target_name))
            connection.execute("DELETE FROM kid_bag_items WHERE member_id = ? AND lower(subject) = lower(?)", (member_id, source_name))   # items the kept subject already had
            connection.execute("UPDATE kid_grades SET subject_id = ? WHERE subject_id = ?", (target_id, source_id))
            connection.execute("DELETE FROM kid_subjects WHERE id = ?", (source_id,))

    def delete_subject(self, household_id: str, subject_id: str) -> "dict[str, int]":
        """Remove a subject for good: its lessons leave the school-day plan, its grades and bag items are deleted, and homework that named it keeps
        its text but loses the subject. -> how many lessons and grades were removed (so a screen can say what was lost)."""
        with self._connection() as connection:
            self._owned(connection, "kid_subjects", household_id, subject_id)
            member_id, name = connection.execute("SELECT member_id, name FROM kid_subjects WHERE id = ?", (subject_id,)).fetchone()
            lessons = connection.execute("DELETE FROM kid_school_slots WHERE member_id = ? AND kind = 'lesson' AND lower(title) = lower(?)", (member_id, name)).rowcount
            grades = connection.execute("SELECT COUNT(*) FROM kid_grades WHERE subject_id = ?", (subject_id,)).fetchone()[0]
            connection.execute("UPDATE kid_tasks SET subject = NULL WHERE member_id = ? AND lower(subject) = lower(?)", (member_id, name))
            connection.execute("DELETE FROM kid_bag_items WHERE member_id = ? AND lower(subject) = lower(?)", (member_id, name))
            connection.execute("DELETE FROM kid_subjects WHERE id = ?", (subject_id,))       # grades go with it
        return {"lessons": lessons, "grades": grades}

    def set_subject_kind(self, household_id: str, subject_id: str, kind: str) -> None:
        self.update_subject(household_id, subject_id, kind=kind)

    def set_subject_kind_by_name(self, household_id: str, member_id: str, name: str, kind: str) -> None:
        if kind not in SUBJECT_KINDS:
            raise ValueError("subject type must be core, minor or elective")
        with self._connection() as connection:
            self._sync_subjects(connection, household_id, member_id)
            connection.execute("UPDATE kid_subjects SET kind = ? WHERE household_id = ? AND member_id = ? AND lower(name) = lower(?)", (kind, household_id, member_id, name.strip()))

    def list_subjects(self, household_id: str, member_id: str) -> "list[dict[str, Any]]":
        """The child's subjects (lesson titles in their plan) with type, code and how many lessons a week they have."""
        with self._connection() as connection:
            self._sync_subjects(connection, household_id, member_id)
            rows = connection.execute(
                "SELECT s.id, s.name, s.kind, s.code, (SELECT COUNT(*) FROM kid_school_slots k WHERE k.household_id = s.household_id AND k.member_id = s.member_id "
                "AND k.kind = 'lesson' AND lower(k.title) = lower(s.name)) FROM kid_subjects s WHERE s.household_id = ? AND s.member_id = ? AND s.archived = 0 "
                "ORDER BY " + _KIND_RANK.replace("kind", "s.kind") + ", s.name", (household_id, member_id)).fetchall()
        return [{"id": r[0], "name": r[1], "kind": r[2], "code": r[3], "lessons": r[4]} for r in rows]

    def add_grade(self, household_id: str, subject_id: str, grade_type: str, grade: float, given_on: date, note: "str | None") -> str:
        if grade_type not in GRADE_TYPES:
            raise ValueError("grade type must be written or oral")
        if isinstance(grade, bool) or not isinstance(grade, (int, float)) or not 1 <= grade <= 6:
            raise ValueError("a grade is a number from 1 to 6")
        grade_id = _member_id()
        with self._connection() as connection:
            if not connection.execute("SELECT 1 FROM kid_subjects WHERE id = ? AND household_id = ? AND archived = 0", (subject_id, household_id)).fetchone():
                raise LookupError("subject does not exist in this child's school plan")
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
            self._sync_subjects(connection, household_id, member_id)
            subjects = connection.execute(
                "SELECT id, name, kind, code FROM kid_subjects WHERE household_id = ? AND member_id = ? AND archived = 0 ORDER BY " + _KIND_RANK + ", name",
                (household_id, member_id)).fetchall()
            out = []
            for subject_id, name, kind, code in subjects:
                grades = connection.execute(
                    "SELECT id, grade_type, grade, given_on, note FROM kid_grades WHERE subject_id = ? ORDER BY given_on, created_at", (subject_id,)).fetchall()
                lessons = connection.execute("SELECT COUNT(*) FROM kid_school_slots WHERE household_id = ? AND member_id = ? AND kind = 'lesson' AND lower(title) = lower(?)",
                                             (household_id, member_id, name)).fetchone()[0]
                out.append({"id": subject_id, "name": name, "kind": kind, "code": code, "lessons": lessons, "grades": [
                    {"id": g[0], "grade_type": g[1], "grade": g[2], "given_on": g[3], "note": g[4]} for g in grades]})
        return out

    # ---------- school-day plan ----------
    def _set_subject_fields(self, connection: Any, household_id: str, member_id: str, name: str, kind: "str | None", code: "str | None") -> None:
        """Type and code given with a lesson go to its subject (None leaves them). A code another subject uses is refused."""
        row = connection.execute("SELECT id FROM kid_subjects WHERE household_id = ? AND member_id = ? AND lower(name) = lower(?)", (household_id, member_id, name.strip())).fetchone()
        if not row:
            return
        if code is not None and str(code).strip():
            code = clean_code(code)
            self._free_code(connection, member_id, code, row[0])
            connection.execute("UPDATE kid_subjects SET code = ? WHERE id = ?", (code, row[0]))
        if kind:
            connection.execute("UPDATE kid_subjects SET kind = ? WHERE id = ?", (kind, row[0]))

    def add_school_slot(self, household_id: str, member_id: str, weekday: int, start: str, end: str, title: str, kind: str, note: "str | None",
                        subject_kind: "str | None" = None, subject_code: "str | None" = None) -> str:
        """A lesson also creates its subject (if the title is new) and may set the subject's type: this is the only way a subject comes to exist."""
        if kind not in SLOT_KINDS:
            raise ValueError("kind must be lesson, break, meal or care")
        if subject_kind is not None and subject_kind not in SUBJECT_KINDS:
            raise ValueError("subject type must be core, minor or elective")
        if isinstance(weekday, bool) or not isinstance(weekday, int) or not 0 <= weekday <= 6:
            raise ValueError("weekday must be 0 (Monday) to 6 (Sunday)")
        start, end = _hhmm(start, "start"), _hhmm(end, "end")
        if end <= start:
            raise ValueError("the end must be after the start")
        slot_id = _member_id()
        with self._connection() as connection:
            self._child(connection, household_id, member_id)
            title = _required_text(title, "title")
            connection.execute(
                "INSERT INTO kid_school_slots(id, household_id, member_id, weekday, start_time, end_time, title, kind, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (slot_id, household_id, member_id, weekday, start, end, title, kind, _text(note)))
            self._sync_subjects(connection, household_id, member_id)
            if kind == "lesson":
                self._set_subject_fields(connection, household_id, member_id, title, subject_kind, subject_code)
        return slot_id

    def update_school_slot(self, household_id: str, slot_id: str, start: str, end: str, title: str, kind: str, note: "str | None",
                           subject_kind: "str | None" = None, subject_code: "str | None" = None) -> None:
        if kind not in SLOT_KINDS:
            raise ValueError("kind must be lesson, break, meal or care")
        if subject_kind is not None and subject_kind not in SUBJECT_KINDS:
            raise ValueError("subject type must be core, minor or elective")
        start, end = _hhmm(start, "start"), _hhmm(end, "end")
        if end <= start:
            raise ValueError("the end must be after the start")
        with self._connection() as connection:
            self._owned(connection, "kid_school_slots", household_id, slot_id)
            member_id, old_title, old_kind = connection.execute("SELECT member_id, title, kind FROM kid_school_slots WHERE id = ?", (slot_id,)).fetchone()
            title = _required_text(title, "title")
            connection.execute("UPDATE kid_school_slots SET start_time = ?, end_time = ?, title = ?, kind = ?, note = ? WHERE id = ?",
                               (start, end, title, kind, _text(note), slot_id))
            if old_kind == "lesson" and old_title.strip().lower() != title.lower():
                # the last lesson with the old title was renamed: carry its subject (type and grades) over instead of archiving it
                left = connection.execute("SELECT 1 FROM kid_school_slots WHERE member_id = ? AND kind = 'lesson' AND lower(title) = lower(?)", (member_id, old_title.strip())).fetchone()
                taken = connection.execute("SELECT 1 FROM kid_subjects WHERE member_id = ? AND lower(name) = lower(?)", (member_id, title)).fetchone()
                if not left and not taken:
                    self._rename_subject_rows(connection, member_id, old_title.strip(), title)
            self._sync_subjects(connection, household_id, member_id)
            if kind == "lesson":
                self._set_subject_fields(connection, household_id, member_id, title, subject_kind, subject_code)

    def delete_school_slot(self, household_id: str, slot_id: str) -> None:
        with self._connection() as connection:
            self._owned(connection, "kid_school_slots", household_id, slot_id)
            (member_id,) = connection.execute("SELECT member_id FROM kid_school_slots WHERE id = ?", (slot_id,)).fetchone()
            connection.execute("DELETE FROM kid_school_slots WHERE id = ?", (slot_id,))
            self._sync_subjects(connection, household_id, member_id)

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
            self._sync_subjects(connection, household_id, member_id)
        return len(targets)

    def list_school_slots(self, household_id: str, member_id: str, weekday: "int | None" = None) -> "list[dict[str, Any]]":
        """Slots with `subject_kind` (core, minor or elective) and `code` on lessons, None on breaks, meals and care."""
        query = "SELECT id, weekday, start_time, end_time, title, kind, note FROM kid_school_slots WHERE household_id = ? AND member_id = ?"
        args: list = [household_id, member_id]
        if weekday is not None:
            query += " AND weekday = ?"
            args.append(weekday)
        with self._connection() as connection:
            rows = connection.execute(query + " ORDER BY weekday, start_time", args).fetchall()
            kinds = {name.lower(): (kind, code) for name, kind, code in connection.execute("SELECT name, kind, code FROM kid_subjects WHERE household_id = ? AND member_id = ?", (household_id, member_id))}
        keys = ("id", "weekday", "start", "end", "title", "kind", "note")
        out = []
        for row in rows:
            slot = dict(zip(keys, row))
            known = kinds.get(slot["title"].strip().lower()) if slot["kind"] == "lesson" else None
            slot["subject_kind"], slot["code"] = known if known else (None, None)
            out.append(slot)
        return out

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
                remind_member_id: "str | None", supply: "int | None", critical: bool = False) -> str:
        med_id = _member_id()
        with self._connection() as connection:
            self._child(connection, household_id, member_id)
            n, t, w, r, s = self._med_fields(connection, household_id, name, time_of_day, weekdays, remind_member_id, supply)
            connection.execute(
                "INSERT INTO kid_meds(id, household_id, member_id, name, dose, time_of_day, weekdays, remind_member_id, supply, created_at, critical) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (med_id, household_id, member_id, n, _text(dose), t, w, r, s, _now(), int(bool(critical))))
        return med_id

    def update_med(self, household_id: str, med_id: str, name: str, dose: "str | None", time_of_day: str, weekdays: Sequence[int],
                   remind_member_id: "str | None", supply: "int | None", critical: bool = False) -> None:
        with self._connection() as connection:
            self._owned(connection, "kid_meds", household_id, med_id)
            n, t, w, r, s = self._med_fields(connection, household_id, name, time_of_day, weekdays, remind_member_id, supply)
            connection.execute("UPDATE kid_meds SET name = ?, dose = ?, time_of_day = ?, weekdays = ?, remind_member_id = ?, supply = ?, critical = ? WHERE id = ?",
                               (n, _text(dose), t, w, r, s, int(bool(critical)), med_id))

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
                connection.execute("UPDATE kid_meds SET supply = CASE WHEN supply > 1 THEN supply - 1 ELSE 0 END WHERE id = ? AND supply IS NOT NULL", (med_id,))

    def list_meds(self, household_id: str, member_id: str, since: str) -> "list[dict[str, Any]]":
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, name, dose, time_of_day, weekdays, remind_member_id, supply, critical FROM kid_meds "
                "WHERE household_id = ? AND member_id = ? AND archived = 0 ORDER BY time_of_day, name", (household_id, member_id)).fetchall()
            meds = []
            for med_id, name, dose, tod, csv, remind, supply, critical in rows:
                log = dict(connection.execute("SELECT day, status FROM kid_med_log WHERE med_id = ? AND day >= ?", (med_id, since)).fetchall())
                meds.append({"id": med_id, "name": name, "dose": dose, "time": tod, "weekdays": [int(d) for d in csv.split(",") if d],
                             "remind_member_id": remind, "supply": supply, "critical": bool(critical), "log": log})
        return meds
